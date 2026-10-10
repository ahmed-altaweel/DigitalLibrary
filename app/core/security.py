import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from jose import JWTError, jwt

from .config import get_settings

settings = get_settings()

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

_ph = PasswordHasher()


def utcnow() -> datetime:
    """Naive UTC datetime (the DB columns are timezone-naive DateTime)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# ---- passwords ---------------------------------------------------------
def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, password)
    except (VerificationError, InvalidHashError):
        return False


# ---- opaque / JWT tokens -----------------------------------------------
def hash_token(token: str) -> str:
    """Deterministic hash for high-entropy tokens (refresh / reset) so they can be looked up directly."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _encode(data: dict, token_type: str, expires: timedelta) -> str:
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    to_encode.update(
        {"exp": now + expires, "iat": now, "type": token_type, "jti": str(uuid.uuid4())}
    )
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm="HS256")


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    return _encode(
        data, ACCESS_TOKEN_TYPE, expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )


def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
    return _encode(
        data, REFRESH_TOKEN_TYPE, expires_delta or timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    )


def decode_token(token: str, expected_type: str | None = None) -> dict:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])
    except JWTError:
        raise ValueError("Invalid token")
    if expected_type and payload.get("type") != expected_type:
        raise ValueError("Invalid token type")
    return payload


def generate_csrf_token() -> str:
    return secrets.token_hex(32)


def generate_password_reset_token() -> str:
    return secrets.token_urlsafe(48)
