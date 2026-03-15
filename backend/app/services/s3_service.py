import boto3
import uuid
from app.config import AWS_REGION, S3_BUCKET_NAME, AWS_ACCESS_KEY_ID, AWS_SECRET_KEY

s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_KEY,
)


def upload(contents: bytes, filename: str) -> str:
    """Upload raw bytes to S3 and return the object key."""
    key = f"uploads/{uuid.uuid4()}_{filename}"
    s3.put_object(Bucket=S3_BUCKET_NAME, Key=key, Body=contents)
    return key


def get_presigned_url(key: str, expiry: int = 3600) -> str:
    """Return a pre-signed URL that grants temporary read access to *key*."""
    return s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET_NAME, "Key": key},
        ExpiresIn=expiry,
    )
