"""Unit tests for the image validation service."""
import pytest
from app.services.validation_service import validate, sanitise_filename


# ---------------------------------------------------------------------------
# Format detection
# ---------------------------------------------------------------------------

def test_valid_png(sample_png_bytes):
    result = validate(sample_png_bytes, "sample.png")
    assert result["valid"] is True
    assert result["format"] == "PNG"
    assert "Valid" in result["message"]


def test_valid_jpeg(sample_jpeg_bytes):
    result = validate(sample_jpeg_bytes, "scan.jpg")
    assert result["valid"] is True
    assert result["format"] == "JPEG"


def test_valid_dicom(sample_dicom_bytes):
    result = validate(sample_dicom_bytes, "scan.dcm")
    assert result["valid"] is True
    assert result["format"] == "DICOM"


def test_invalid_pdf(sample_pdf_bytes):
    result = validate(sample_pdf_bytes, "doc.pdf")
    assert result["valid"] is False
    assert "Invalid format" in result["message"]


# ---------------------------------------------------------------------------
# Response structure
# ---------------------------------------------------------------------------

def test_result_has_required_fields(sample_png_bytes):
    result = validate(sample_png_bytes, "test.png")
    for key in ("valid", "format", "size", "message", "timestamp"):
        assert key in result


def test_size_is_mb_string(sample_png_bytes):
    result = validate(sample_png_bytes, "test.png")
    assert result["size"].endswith("MB")


# ---------------------------------------------------------------------------
# Filename sanitisation
# ---------------------------------------------------------------------------

def test_sanitise_filename_normal():
    assert sanitise_filename("image.png") == "image.png"


def test_sanitise_filename_path_traversal():
    result = sanitise_filename("../../etc/passwd")
    assert ".." not in result
    assert "passwd" in result


def test_sanitise_filename_strips_spaces_and_parens():
    result = sanitise_filename("my file (1).png")
    assert " " not in result
    assert "(" not in result


def test_sanitise_filename_empty():
    assert sanitise_filename("") == "upload"
