import re
import magic
from datetime import datetime, timezone

ALLOWED = {
    "application/dicom": "DICOM",
    "image/png":         "PNG",
    "image/jpeg":        "JPEG",
    "image/tiff":        "TIFF",
}

# DICOM files: 128-byte preamble followed by the magic string "DICM"
_DICOM_MAGIC = b"DICM"
_DICOM_MAGIC_OFFSET = 128


def _detect_mime(contents: bytes) -> str:
    """Detect MIME type from raw file bytes."""
    # Explicit DICOM check before falling back to libmagic
    if len(contents) > _DICOM_MAGIC_OFFSET + 4 and contents[_DICOM_MAGIC_OFFSET:_DICOM_MAGIC_OFFSET + 4] == _DICOM_MAGIC:
        return "application/dicom"
    try:
        return magic.from_buffer(contents, mime=True)
    except Exception:
        return "application/octet-stream"


def validate(contents: bytes, filename: str) -> dict:
    """Validate file bytes against the allowed medical imaging formats."""
    mime = _detect_mime(contents)
    fmt = ALLOWED.get(mime)
    size_mb = f"{len(contents) / (1024 * 1024):.2f}MB"
    valid = fmt is not None

    return {
        "valid":     valid,
        "format":    fmt if valid else mime,
        "size":      size_mb,
        "message":   "Valid medical imaging format"
                     if valid
                     else f"Invalid format. Allowed: {', '.join(ALLOWED.values())}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def sanitise_filename(filename: str) -> str:
    """Strip path traversal and special characters from an uploaded filename."""
    # Remove directory components
    filename = filename.replace("\\", "/").rsplit("/", 1)[-1]
    # Allow only word characters, dots, and hyphens
    filename = re.sub(r"[^\w.\-]", "_", filename)
    return filename[:255] or "upload"
