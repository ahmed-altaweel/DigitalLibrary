from .base import StorageBackend
from .local import LocalStorage
from .s3 import S3Storage
from ..core.config import get_settings

def get_storage() -> StorageBackend:
    settings = get_settings()
    if settings.STORAGE_BACKEND == "s3":
        return S3Storage()
    return LocalStorage(settings.STORAGE_LOCAL_PATH)
