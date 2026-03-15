"""Create the private S3 bucket for storing uploaded medical images."""
import boto3

s3 = boto3.client("s3", region_name="eu-west-1")
BUCKET = "medical-image-validation"


def create_bucket(bucket_name: str = BUCKET) -> None:
    s3.create_bucket(
        Bucket=bucket_name,
        CreateBucketConfiguration={"LocationConstraint": "eu-west-1"},
    )

    # Block ALL public access
    s3.put_public_access_block(
        Bucket=bucket_name,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls":       True,
            "IgnorePublicAcls":      True,
            "BlockPublicPolicy":     True,
            "RestrictPublicBuckets": True,
        },
    )

    # Enable server-side encryption by default
    s3.put_bucket_encryption(
        Bucket=bucket_name,
        ServerSideEncryptionConfiguration={
            "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
        },
    )

    print(f"S3 bucket created: {bucket_name}")


if __name__ == "__main__":
    create_bucket()
