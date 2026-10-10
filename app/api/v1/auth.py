from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...schemas.user import UserCreate, UserLogin, UserResponse, UserUpdate, PasswordChange, PasswordResetRequest, PasswordResetConfirm, UserWithRoles
from ...services import auth_service
from ...models.user import User

router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register(user_data: UserCreate, response: Response, db: Session = Depends(get_db)):
    user = auth_service.register_user(db, user_data)
    tokens = auth_service.create_tokens(db, user)
    response.set_cookie("access_token", f"Bearer {tokens['access_token']}", httponly=True, samesite="lax")
    response.set_cookie("refresh_token", tokens['refresh_token'], httponly=True, samesite="lax")
    return user

@router.post("/login", response_model=UserResponse)
def login(user_data: UserLogin, request: Request, response: Response, db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(db, user_data.email, user_data.password)
    tokens = auth_service.create_tokens(
        db, user, 
        user_agent=request.headers.get("user-agent"), 
        ip_address=request.client.host if request.client else None
    )
    response.set_cookie("access_token", f"Bearer {tokens['access_token']}", httponly=True, samesite="lax")
    response.set_cookie("refresh_token", tokens['refresh_token'], httponly=True, samesite="lax")
    return user

@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    refresh_token = request.cookies.get("refresh_token")
    auth_service.logout_user(db, current_user.id, refresh_token)
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return {"message": "Logged out successfully"}

@router.post("/refresh")
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
    new_access_token = auth_service.refresh_access_token(db, refresh_token)
    response.set_cookie("access_token", f"Bearer {new_access_token}", httponly=True, samesite="lax")
    return {"message": "Token refreshed"}

@router.get("/me", response_model=UserWithRoles)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.put("/me", response_model=UserResponse)
def update_me(data: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    for k, v in data.dict(exclude_unset=True).items():
        setattr(current_user, k, v)
    db.commit()
    db.refresh(current_user)
    return current_user

@router.post("/me/change-password")
def change_password(data: PasswordChange, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    auth_service.change_password(db, current_user, data.old_password, data.new_password)
    return {"message": "Password updated successfully"}

@router.post("/forgot-password")
def forgot_password(data: PasswordResetRequest, db: Session = Depends(get_db)):
    auth_service.request_password_reset(db, data.email)
    return {"message": "If that email is registered, a reset link will be sent."}

@router.post("/reset-password")
def reset_password(data: PasswordResetConfirm, db: Session = Depends(get_db)):
    auth_service.reset_password(db, data.token, data.new_password)
    return {"message": "Password reset successfully"}
