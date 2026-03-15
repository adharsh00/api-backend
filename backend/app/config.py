import os
from dotenv import load_dotenv

load_dotenv()

AWS_REGION        = os.getenv("AWS_REGION", "eu-west-1")
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY    = os.getenv("AWS_SECRET_ACCESS_KEY")
S3_BUCKET_NAME    = os.getenv("S3_BUCKET_NAME", "medical-image-validation")
SQS_QUEUE_URL     = os.getenv("SQS_QUEUE_URL", "")
CLASSMATE_API_URL = os.getenv("CLASSMATE_API_URL", "http://13.53.123.150:5000")
CLASSMATE_API_KEY = os.getenv("CLASSMATE_API_KEY", "healthcare-api-key-2024")

# Maximum uploaded file size (default 50 MB)
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", str(50 * 1024 * 1024)))

ALLOWED_FORMATS = {"DICOM", "PNG", "JPEG", "TIFF"}
ALLOWED_MIMES = {
    "application/dicom",
    "image/png",
    "image/jpeg",
    "image/tiff",
}
