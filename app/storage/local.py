import os

from .base import StorageBackend


class LocalStorage(StorageBackend):
    def __init__(self, base_path: str):
        self.base_path = os.path.realpath(base_path)
        os.makedirs(self.base_path, exist_ok=True)

    def _safe_path(self, key: str) -> str:
        """Resolve `key` inside base_path; refuse anything that escapes it (path traversal)."""
        path = os.path.realpath(os.path.join(self.base_path, key))
        if os.path.commonpath([self.base_path, path]) != self.base_path:
            raise ValueError("Invalid storage key")
        return path

    def upload(self, key: str, data: bytes, content_type: str) -> str:
        path = self._safe_path(key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
        return path

    def download(self, key: str) -> bytes:
        with open(self._safe_path(key), "rb") as f:
            return f.read()

    def delete(self, key: str) -> bool:
        path = self._safe_path(key)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False

    def get_url(self, key: str) -> str:
        return f"/uploads/{key}"

    def exists(self, key: str) -> bool:
        try:
            return os.path.exists(self._safe_path(key))
        except ValueError:
            return False
