from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..models.user import User
from .database import get_db
from .security import ACCESS_TOKEN_TYPE, decode_token


def _strip_bearer(token: str | None) -> str | None:
    if token and token.startswith("Bearer "):
        return token[7:]
    return token


def get_token_from_cookie(request: Request) -> str:
    token = _strip_bearer(request.cookies.get("access_token"))
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return token


def get_optional_token_from_cookie(request: Request) -> str | None:
    return _strip_bearer(request.cookies.get("access_token"))


def _user_from_token(token: str, db: Session) -> User | None:
    try:
        payload = decode_token(token, expected_type=ACCESS_TOKEN_TYPE)
    except ValueError:
        return None
    user_id = payload.get("sub")
    if not user_id:
        return None
    return db.query(User).filter(User.id == user_id).first()


def get_current_user(token: str = Depends(get_token_from_cookie), db: Session = Depends(get_db)) -> User:
    """Authenticated AND active user. Disabled accounts are rejected everywhere."""
    user = _user_from_token(token, db)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user")
    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    return current_user


def get_optional_user(
    token: str | None = Depends(get_optional_token_from_cookie), db: Session = Depends(get_db)
) -> User | None:
    if not token:
        return None
    user = _user_from_token(token, db)
    if user is None or not user.is_active:
        return None
    return user


def user_has_role(user: User | None, *roles: str) -> bool:
    return bool(user) and any(r.name in roles for r in user.roles)


def require_role(*roles):
    def role_checker(current_user: User = Depends(get_current_active_user)):
        if not user_has_role(current_user, *roles):
            raise HTTPException(status_code=403, detail="Insufficient privileges")
        return current_user

    return role_checker


get_current_admin = require_role("admin")
get_current_editor = require_role("editor", "admin")
