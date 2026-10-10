import logging
from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..core.security import (
    REFRESH_TOKEN_TYPE,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_password_reset_token,
    hash_password,
    hash_token,
    utcnow,
    verify_password,
)
from ..models.user import PasswordResetToken, RefreshToken, Role, User

logger = logging.getLogger(__name__)
settings = get_settings()

# Used to keep login timing similar whether or not the email exists.
_DUMMY_HASH = hash_password("dummy-password-for-timing")


def register_user(db: Session, user_data):
    email = user_data.email.lower()
    if db.query(User).filter(func.lower(User.email) == email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")

    new_user = User(
        email=email,
        username=user_data.username,
        hashed_password=hash_password(user_data.password),
    )
    member_role = db.query(Role).filter(Role.name == "member").first()
    if member_role:
        new_user.roles.append(member_role)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def authenticate_user(db: Session, email, password):
    user = db.query(User).filter(func.lower(User.email) == str(email).lower()).first()
    if not user:
        verify_password(password, _DUMMY_HASH)
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")
    return user


def create_tokens(db: Session, user: User, user_agent: str | None = None, ip_address: str | None = None):
    access_token = create_access_token(data={"sub": user.id})
    refresh_token_str = create_refresh_token(data={"sub": user.id})

    rt = RefreshToken(
        user_id=user.id,
        token_hash=hash_token(refresh_token_str),
        expires_at=utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
        user_agent=(user_agent or "")[:500] or None,
        ip_address=ip_address,
    )
    db.add(rt)
    db.commit()
    return {"access_token": access_token, "refresh_token": refresh_token_str}


def _get_valid_refresh_record(db: Session, refresh_token_str: str) -> RefreshToken:
    invalid = HTTPException(status_code=401, detail="Invalid refresh token")
    try:
        payload = decode_token(refresh_token_str, expected_type=REFRESH_TOKEN_TYPE)
    except ValueError:
        raise invalid
    record = db.query(RefreshToken).filter(RefreshToken.token_hash == hash_token(refresh_token_str)).first()
    if (
        record is None
        or record.is_revoked
        or record.expires_at <= utcnow()
        or record.user_id != payload.get("sub")
    ):
        raise invalid
    return record


def refresh_access_token(db: Session, refresh_token_str: str):
    record = _get_valid_refresh_record(db, refresh_token_str)
    user = db.query(User).filter(User.id == record.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return create_access_token(data={"sub": user.id})


def revoke_refresh_token(db: Session, user_id: str, refresh_token_str: str):
    rt = (
        db.query(RefreshToken)
        .filter(RefreshToken.token_hash == hash_token(refresh_token_str), RefreshToken.user_id == user_id)
        .first()
    )
    if rt and not rt.is_revoked:
        rt.is_revoked = True
        rt.revoked_at = utcnow()
        db.commit()


def revoke_all_refresh_tokens(db: Session, user_id: str, commit: bool = True):
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user_id, RefreshToken.is_revoked == False  # noqa: E712
    ).update({"is_revoked": True, "revoked_at": utcnow()})
    if commit:
        db.commit()


def logout_user(db: Session, user_id: str, refresh_token_str: str | None = None):
    if refresh_token_str:
        revoke_refresh_token(db, user_id, refresh_token_str)


def request_password_reset(db: Session, email: str):
    user = db.query(User).filter(func.lower(User.email) == email.lower()).first()
    if not user or not user.is_active:
        return None
    token = generate_password_reset_token()
    prt = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_token(token),
        expires_at=utcnow() + timedelta(hours=1),
    )
    db.add(prt)
    db.commit()
    # TODO: send `token` by email once an email service is wired in. It must never
    # be returned in the HTTP response. Outside production it is logged for local testing.
    if not settings.is_production:
        logger.warning("Password reset token for %s: %s", user.email, token)
    return None


def reset_password(db: Session, token: str, new_password: str):
    now = utcnow()
    matched = (
        db.query(PasswordResetToken)
        .filter(
            PasswordResetToken.token_hash == hash_token(token),
            PasswordResetToken.is_used == False,  # noqa: E712
            PasswordResetToken.expires_at > now,
        )
        .first()
    )
    if not matched:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user = db.query(User).filter(User.id == matched.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user.hashed_password = hash_password(new_password)
    matched.is_used = True
    matched.used_at = now
    revoke_all_refresh_tokens(db, user.id, commit=False)  # force re-login everywhere
    db.commit()
    return True


def change_password(db: Session, user: User, old_password: str, new_password: str):
    if not verify_password(old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid old password")
    user.hashed_password = hash_password(new_password)
    revoke_all_refresh_tokens(db, user.id, commit=False)
    db.commit()
