from abc import ABC, abstractmethod

class StorageBackend(ABC):
    @abstractmethod
    def upload(self, key: str, data: bytes, content_type: str) -> str:
        pass
        
    @abstractmethod
    def download(self, key: str) -> bytes:
        pass
        
    @abstractmethod
    def delete(self, key: str) -> bool:
        pass
        
    @abstractmethod
    def get_url(self, key: str) -> str:
        pass
        
    @abstractmethod
    def exists(self, key: str) -> bool:
        pass
