from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from ..models.user import User, Role, RefreshToken, PasswordResetToken
from ..core.security import hash_password, verify_password, create_access_token, create_refresh_token, generate_password_reset_token

def register_user(db: Session, user_data):
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hash_password(user_data.password)
    )
    member_role = db.query(Role).filter(Role.name == "member").first()
    if member_role:
        new_user.roles.append(member_role)
        
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def authenticate_user(db: Session, email, password):
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user

def create_tokens(db: Session, user: User, user_agent: str = None, ip_address: str = None):
    access_token = create_access_token(data={"sub": user.id})
    refresh_token_str = create_refresh_token(data={"sub": user.id})
    
    rt = RefreshToken(
        user_id=user.id,
        token_hash=hash_password(refresh_token_str),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        user_agent=user_agent,
        ip_address=ip_address
    )
    db.add(rt)
    db.commit()
    return {"access_token": access_token, "refresh_token": refresh_token_str}

def refresh_access_token(db: Session, refresh_token_str: str):
    from ..core.security import decode_token
    payload = decode_token(refresh_token_str)
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    return create_access_token(data={"sub": user.id})

def revoke_refresh_token(db: Session, token_id: str):
    rt = db.query(RefreshToken).filter(RefreshToken.id == token_id).first()
    if rt:
        rt.is_revoked = True
        rt.revoked_at = datetime.now(timezone.utc)
        db.commit()

def logout_user(db: Session, user_id: str, token_id: str = None):
    if token_id:
        revoke_refresh_token(db, token_id)

def request_password_reset(db: Session, email: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return
    token = generate_password_reset_token()
    prt = PasswordResetToken(
        user_id=user.id,
        token_hash=hash_password(token),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
    )
    db.add(prt)
    db.commit()
    return token

def reset_password(db: Session, token: str, new_password: str):
    now = datetime.now(timezone.utc)
    tokens = db.query(PasswordResetToken).filter(
        PasswordResetToken.is_used == False,
        PasswordResetToken.expires_at > now
    ).all()
    
    matched_token = None
    for t in tokens:
        if verify_password(token, t.token_hash):
            matched_token = t
            break
            
    if not matched_token:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
        
    user = db.query(User).filter(User.id == matched_token.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="User not found")
        
    user.hashed_password = hash_password(new_password)
    matched_token.is_used = True
    matched_token.used_at = now
    db.commit()
    return True

def change_password(db: Session, user: User, old_password: str, new_password: str):
    if not verify_password(old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid old password")
    user.hashed_password = hash_password(new_password)
    db.commit()
