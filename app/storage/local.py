import os
from .base import StorageBackend

class LocalStorage(StorageBackend):
    def __init__(self, base_path: str):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)
        
    def upload(self, key: str, data: bytes, content_type: str) -> str:
        path = os.path.join(self.base_path, key)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
        return path
        
    def download(self, key: str) -> bytes:
        path = os.path.join(self.base_path, key)
        with open(path, "rb") as f:
            return f.read()
            
    def delete(self, key: str) -> bool:
        path = os.path.join(self.base_path, key)
        if os.path.exists(path):
            os.remove(path)
            return True
        return False
        
    def get_url(self, key: str) -> str:
        return f"/uploads/{key}"
        
    def exists(self, key: str) -> bool:
        return os.path.exists(os.path.join(self.base_path, key))
