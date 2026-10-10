from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from .database import get_db
from .security import decode_token
from ..models.user import User

def get_token_from_cookie(request: Request) -> str:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
        )
    if token.startswith("Bearer "):
        token = token[7:]
    return token

def get_optional_token_from_cookie(request: Request) -> str | None:
    token = request.cookies.get("access_token")
    if token and token.startswith("Bearer "):
        token = token[7:]
    return token

def get_current_user(token: str = Depends(get_token_from_cookie), db: Session = Depends(get_db)):
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def get_current_active_user(current_user: User = Depends(get_current_user)):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_optional_user(token: str | None = Depends(get_optional_token_from_cookie), db: Session = Depends(get_db)):
    if not token:
        return None
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            return None
        return db.query(User).filter(User.id == user_id).first()
    except ValueError:
        return None

def require_role(*roles):
    def role_checker(current_user: User = Depends(get_current_active_user)):
        user_roles = [r.name for r in current_user.roles]
        if not any(role in user_roles for role in roles):
            raise HTTPException(status_code=403, detail="Insufficient privileges")
        return current_user
    return role_checker

get_current_admin = require_role("admin")
get_current_editor = require_role("editor", "admin")
