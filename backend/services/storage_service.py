import boto3
import os
from botocore.exceptions import ClientError
from typing import Optional

class StorageService:
    """Service for handling Vultr Object Storage uploads and downloads."""

    def __init__(self):
        self.bucket_name = os.getenv("VULTR_BUCKET_NAME", "voice-samurai-logs")

        self.s3_client = boto3.client(
            "s3",
            endpoint_url=os.getenv("VULTR_ENDPOINT_URL"),
            access_key_id=os.getenv("VULTR_ACCESS_KEY"),
            secret_access_key=os.getenv("VULTR_SECRET_KEY"),
            region_name=os.getenv("VULTR_REGION", "ewr")
        )

    def upload_file(self, file_bytes: bytes, filename: str, bucket: Optional[str] = None) -> str:
        """
        Upload file to Vultr Object Storage and return public URL.

        Args:
            file_bytes: Raw file bytes
            filename: Name of the file to upload
            bucket: Optional bucket name (defaults to configured bucket)

        Returns:
            Public URL of the uploaded file
        """
        try:
            target_bucket = bucket or self.bucket_name

            self.s3_client.put_object(
                Bucket=target_bucket,
                Key=filename,
                Body=file_bytes,
                ACL="public-read"
            )

            endpoint_url = os.getenv("VULTR_ENDPOINT_URL")
            public_url = f"{endpoint_url}/{target_bucket}/{filename}"

            return public_url

        except ClientError as e:
            raise Exception(f"Failed to upload file to Vultr: {str(e)}")

    def download_file(self, filename: str, bucket: Optional[str] = None) -> bytes:
        """
        Download file from Vultr Object Storage.

        Args:
            filename: Name of the file to download
            bucket: Optional bucket name (defaults to configured bucket)

        Returns:
            File bytes
        """
        try:
            target_bucket = bucket or self.bucket_name

            response = self.s3_client.get_object(
                Bucket=target_bucket,
                Key=filename
            )

            return response['Body'].read()

        except ClientError as e:
            raise Exception(f"Failed to download file from Vultr: {str(e)}")
