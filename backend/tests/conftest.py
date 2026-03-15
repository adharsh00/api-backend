"""Shared pytest fixtures for the backend test suite."""
import pytest
from io import BytesIO


@pytest.fixture
def sample_png_bytes() -> bytes:
    """Return a minimal valid PNG file as bytes (generated with Pillow)."""
    try:
        from PIL import Image
        img = Image.new("RGB", (50, 50), color=(255, 0, 0))
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        # Hardcoded 1×1 red PNG as fallback when Pillow is not available
        return (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
            b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
            b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x18\xdd"
            b"\x8d\x8d\x00\x00\x00\x00IEND\xaeB`\x82"
        )


@pytest.fixture
def sample_jpeg_bytes() -> bytes:
    """Return a minimal valid JPEG file as bytes."""
    try:
        from PIL import Image
        img = Image.new("RGB", (50, 50), color=(0, 128, 255))
        buf = BytesIO()
        img.save(buf, format="JPEG")
        return buf.getvalue()
    except ImportError:
        # Minimal JPEG magic bytes
        return b"\xff\xd8\xff\xe0" + b"\x00" * 100 + b"\xff\xd9"


@pytest.fixture
def sample_dicom_bytes() -> bytes:
    """Return a minimal valid DICOM file: 128-byte preamble + 'DICM' magic."""
    preamble = b"\x00" * 128
    magic = b"DICM"
    # Minimal File Meta Information — tag (0002,0000) UL value = 0
    dataset = (
        b"\x02\x00\x00\x00"  # Tag (0002,0000)
        b"UL"                 # VR: UnsignedLong
        b"\x00\x00"          # Reserved
        b"\x04\x00\x00\x00"  # Length = 4
        b"\x00\x00\x00\x00"  # Value = 0
    )
    return preamble + magic + dataset


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Return bytes that look like a PDF (invalid medical format)."""
    return b"%PDF-1.4 fake pdf content for testing purposes"
