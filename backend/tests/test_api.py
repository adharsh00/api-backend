"""Integration-style tests for the FastAPI application routes."""
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock
from app.main import app

_TRANSPORT = ASGITransport(app=app)


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(transport=_TRANSPORT, base_url="http://test") as client:
        r = await client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "healthy"
    assert "service" in body


@pytest.mark.asyncio
async def test_get_formats():
    async with AsyncClient(transport=_TRANSPORT, base_url="http://test") as client:
        r = await client.get("/formats")
    assert r.status_code == 200
    body = r.json()
    assert "supported_formats" in body
    for fmt in ("DICOM", "PNG", "JPEG", "TIFF"):
        assert fmt in body["supported_formats"]


@pytest.mark.asyncio
async def test_validate_image_empty_file():
    async with AsyncClient(transport=_TRANSPORT, base_url="http://test") as client:
        r = await client.post(
            "/validate-image",
            files={"file": ("empty.png", b"", "image/png")},
        )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_validate_image_valid_png(sample_png_bytes):
    with patch("app.services.s3_service.s3") as mock_s3, \
         patch("app.services.sqs_service.sqs") as mock_sqs:
        mock_s3.put_object = MagicMock()
        mock_sqs.send_message = MagicMock(return_value={"MessageId": "test-msg-id"})

        async with AsyncClient(transport=_TRANSPORT, base_url="http://test") as client:
            r = await client.post(
                "/validate-image",
                files={"file": ("test.png", sample_png_bytes, "image/png")},
            )

    assert r.status_code == 200
    body = r.json()
    assert body["valid"] is True
    assert body["format"] == "PNG"
    assert "size" in body
    assert "timestamp" in body


@pytest.mark.asyncio
async def test_validate_image_invalid_format(sample_pdf_bytes):
    with patch("app.services.s3_service.s3") as mock_s3, \
         patch("app.services.sqs_service.sqs") as mock_sqs:
        mock_s3.put_object = MagicMock()
        mock_sqs.send_message = MagicMock(return_value={"MessageId": "test-msg-id"})

        async with AsyncClient(transport=_TRANSPORT, base_url="http://test") as client:
            r = await client.post(
                "/validate-image",
                files={"file": ("doc.pdf", sample_pdf_bytes, "application/pdf")},
            )

    assert r.status_code == 200
    body = r.json()
    assert body["valid"] is False
    assert "Invalid format" in body["message"]
