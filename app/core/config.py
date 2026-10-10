from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_NAME: str = "library"
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    
    SECRET_KEY: str = "supersecretkey"
    JWT_SECRET_KEY: str = "supersecretjwtkey"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    BACKEND_CORS_ORIGINS: str = "*"
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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

@lru_cache
def get_settings():
    return Settings()
