import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services import s3_service, sqs_service, validation_service
from app.config import MAX_FILE_SIZE

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/validate-image")
async def validate_image(file: UploadFile = File(...)):
    """Validate an uploaded medical image file.

    Processing flow:
    1. Read and size-check the file
    2. Sanitise the filename
    3. Detect MIME type and validate format
    4. Upload to Amazon S3 (best-effort)
    5. Enqueue validation result to AWS SQS (best-effort)
    6. Return validation response
    """
    contents = await file.read()

    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Empty file uploaded")

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed size is {MAX_FILE_SIZE // (1024 * 1024)} MB",
        )

    safe_filename = validation_service.sanitise_filename(file.filename or "unknown")

    # 1. Detect MIME type and validate
    result = validation_service.validate(contents, safe_filename)

    # 2. Upload to S3 (non-fatal if unavailable during local development)
    try:
        s3_key = s3_service.upload(contents, safe_filename)
        result["s3_key"] = s3_key
    except Exception as exc:
        logger.warning("S3 upload failed: %s", exc)
        result["s3_key"] = None

    # 3. Enqueue to SQS (non-fatal)
    try:
        sqs_service.enqueue({"s3_key": result.get("s3_key"), "format": result["format"]})
    except Exception as exc:
        logger.warning("SQS enqueue failed: %s", exc)

    return result


@router.get("/formats")
def get_formats():
    """Return the list of accepted medical imaging formats."""
    return {
        "supported_formats": ["DICOM", "PNG", "JPEG", "TIFF"],
        "description": "Accepted medical imaging formats",
    }
