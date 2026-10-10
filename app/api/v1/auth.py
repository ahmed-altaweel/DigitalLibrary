from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from ...core.config import get_settings
from ...core.database import get_db
from ...core.dependencies import get_current_user
from ...core.rate_limit import limiter
from ...models.user import User
from ...schemas.user import (
    PasswordChange,
    PasswordResetConfirm,
    PasswordResetRequest,
    UserCreate,
    UserLogin,
    UserResponse,
    UserUpdate,
    UserWithRoles,
)
from ...services import auth_service

router = APIRouter()
settings = get_settings()


def _set_cookie(response: Response, key: str, value: str, max_age: int):
    response.set_cookie(
        key,
        value,
        max_age=max_age,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.COOKIE_SAMESITE.lower(),
        domain=settings.COOKIE_DOMAIN,
        path="/",
    )


def _set_auth_cookies(response: Response, access_token: str, refresh_token: str | None = None):
    _set_cookie(response, "access_token", f"Bearer {access_token}", settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    if refresh_token:
        _set_cookie(response, "refresh_token", refresh_token, settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 86400)


def _client_ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.post("/register", response_model=UserResponse)
@limiter.limit(settings.RATE_LIMIT_AUTH)
def register(request: Request, user_data: UserCreate, response: Response, db: Session = Depends(get_db)):
    user = auth_service.register_user(db, user_data)
    tokens = auth_service.create_tokens(
        db, user, user_agent=request.headers.get("user-agent"), ip_address=_client_ip(request)
    )
    _set_auth_cookies(response, tokens["access_token"], tokens["refresh_token"])
    return user


@router.post("/login", response_model=UserResponse)
@limiter.limit(settings.RATE_LIMIT_AUTH)
def login(request: Request, user_data: UserLogin, response: Response, db: Session = Depends(get_db)):
    user = auth_service.authenticate_user(db, user_data.email, user_data.password)
    tokens = auth_service.create_tokens(
        db, user, user_agent=request.headers.get("user-agent"), ip_address=_client_ip(request)
    )
    _set_auth_cookies(response, tokens["access_token"], tokens["refresh_token"])
    return user


@router.post("/logout")
def logout(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    auth_service.logout_user(db, current_user.id, request.cookies.get("refresh_token"))
    response.delete_cookie("access_token", path="/", domain=settings.COOKIE_DOMAIN)
    response.delete_cookie("refresh_token", path="/", domain=settings.COOKIE_DOMAIN)
    return {"message": "Logged out successfully"}


@router.post("/refresh")
@limiter.limit(settings.RATE_LIMIT_GENERAL)
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
    new_access_token = auth_service.refresh_access_token(db, refresh_token)
    _set_auth_cookies(response, new_access_token)
    return {"message": "Token refreshed"}


@router.get("/me", response_model=UserWithRoles)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserResponse)
def update_me(data: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(current_user, k, v)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.post("/me/change-password")
@limiter.limit(settings.RATE_LIMIT_AUTH)
def change_password(
    request: Request,
    data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    auth_service.change_password(db, current_user, data.old_password, data.new_password)
    return {"message": "Password updated successfully"}


@router.post("/forgot-password")
@limiter.limit(settings.RATE_LIMIT_AUTH)
def forgot_password(request: Request, data: PasswordResetRequest, db: Session = Depends(get_db)):
    auth_service.request_password_reset(db, data.email)
    return {"message": "If that email is registered, a reset link will be sent."}


@router.post("/reset-password")
@limiter.limit(settings.RATE_LIMIT_AUTH)
def reset_password(request: Request, data: PasswordResetConfirm, db: Session = Depends(get_db)):
    auth_service.reset_password(db, data.token, data.new_password)
    return {"message": "Password reset successfully"}
