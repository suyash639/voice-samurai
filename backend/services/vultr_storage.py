import boto3
from botocore.exceptions import ClientError
from typing import Optional
from config import config

class VultrStorage:
    """Handles file uploads to Vultr Object Storage."""

    def __init__(self):
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=config.VULTR_ENDPOINT_URL,
            access_key_id=config.VULTR_ACCESS_KEY,
            secret_access_key=config.VULTR_SECRET_KEY,
            region_name=config.VULTR_REGION
        )
        self.bucket_name = config.VULTR_BUCKET_NAME

    def upload_file(self, file_obj: bytes, filename: str) -> str:
        """
        Upload file to Vultr Object Storage.

        Args:
            file_obj: File bytes to upload
            filename: Name of the file

        Returns:
            Public URL of the uploaded file
        """
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=filename,
                Body=file_obj,
                ACL="public-read"
            )

            public_url = f"{config.VULTR_ENDPOINT_URL}/{self.bucket_name}/{filename}"
            return public_url

        except ClientError as e:
            raise Exception(f"Vultr upload failed: {str(e)}")
