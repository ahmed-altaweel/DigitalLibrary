import boto3
from botocore.exceptions import ClientError
from .base import StorageBackend
from ..core.config import get_settings

class S3Storage(StorageBackend):
    def __init__(self):
        settings = get_settings()
        self.bucket = settings.S3_BUCKET_NAME
        self.client = boto3.client(
            's3',
            region_name=settings.S3_REGION,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID,
            aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY,
            endpoint_url=settings.S3_ENDPOINT_URL
        )
        
    def upload(self, key: str, data: bytes, content_type: str) -> str:
        self.client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type
        )
        return key
        
    def download(self, key: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        return response['Body'].read()
        
    def delete(self, key: str) -> bool:
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False
            
    def get_url(self, key: str) -> str:
        # Pre-signed URL or public URL depending on requirements
        return self.client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': key},
            ExpiresIn=3600
        )
        
    def exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket, Key=key)
            return True
        except ClientError:
            return False
