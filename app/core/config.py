from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_INSECURE_DEFAULTS = {"supersecretkey", "supersecretjwtkey", "changeme", ""}


class Settings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "library"
    DB_USER: str = "root"
    DB_PASSWORD: str = ""

    # In production these MUST be provided via the environment (see validator below).
    SECRET_KEY: str = "supersecretkey"
    JWT_SECRET_KEY: str = "supersecretjwtkey"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    # Comma-separated list of explicit origins. "*" is rejected because the API
    # uses cookie credentials (browsers refuse "*" together with credentials).
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    ENVIRONMENT: str = "development"

    STORAGE_BACKEND: str = "local"
    STORAGE_LOCAL_PATH: str = "storage/uploads"
    MAX_UPLOAD_SIZE_MB: int = 100
    ALLOWED_FILE_EXTENSIONS: str = "pdf,epub,txt,md"

    S3_BUCKET_NAME: str | None = None
    S3_REGION: str | None = None
    S3_ACCESS_KEY_ID: str | None = None
    S3_SECRET_ACCESS_KEY: str | None = None
    S3_ENDPOINT_URL: str | None = None

    RATE_LIMIT_AUTH: str = "5/minute"
    RATE_LIMIT_GENERAL: str = "100/minute"

    # Cookies
    COOKIE_SECURE: bool | None = None  # None -> True in production, False otherwise
    COOKIE_SAMESITE: str = "lax"
    COOKIE_DOMAIN: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ---- derived helpers -------------------------------------------------
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT.lower() in {"production", "prod"}

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.BACKEND_CORS_ORIGINS.split(",") if o.strip()]

    @property
    def cookie_secure(self) -> bool:
        return self.is_production if self.COOKIE_SECURE is None else self.COOKIE_SECURE

    @property
    def allowed_extensions(self) -> set[str]:
        return {e.strip().lower().lstrip(".") for e in self.ALLOWED_FILE_EXTENSIONS.split(",") if e.strip()}

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    # ---- validation ------------------------------------------------------
    @model_validator(mode="after")
    def _validate_security(self):
        if "*" in self.cors_origins:
            raise ValueError(
                "BACKEND_CORS_ORIGINS must list explicit origins; '*' cannot be used with cookie credentials."
            )
        if self.COOKIE_SAMESITE.lower() not in {"lax", "strict", "none"}:
            raise ValueError("COOKIE_SAMESITE must be one of: lax, strict, none")
        if self.is_production:
            for name in ("SECRET_KEY", "JWT_SECRET_KEY"):
                value = getattr(self, name)
                if value in _INSECURE_DEFAULTS or len(value) < 32:
                    raise ValueError(
                        f"{name} must be set to a random value of at least 32 characters in production "
                        "(e.g. `python -c \"import secrets; print(secrets.token_urlsafe(48))\"`)."
                    )
        return self


@lru_cache
def get_settings():
    return Settings()
