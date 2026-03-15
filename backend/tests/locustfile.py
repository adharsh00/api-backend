"""Locust load-test script for the Image Validation API.

Usage:
    locust -f tests/locustfile.py --host http://<EC2-IP>:8000
"""
from locust import HttpUser, task, between
from io import BytesIO

try:
    from PIL import Image

    def _make_png_bytes() -> bytes:
        img = Image.new("RGB", (50, 50), color=(0, 128, 255))
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    _PNG = _make_png_bytes()
except ImportError:
    # Minimal 1×1 PNG fallback
    _PNG = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
        b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00"
        b"\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x18\xdd"
        b"\x8d\x8d\x00\x00\x00\x00IEND\xaeB`\x82"
    )


class ValidationUser(HttpUser):
    """Simulates a user uploading images and checking the API health."""

    wait_time = between(1, 3)

    @task(3)
    def validate_png_image(self):
        self.client.post(
            "/validate-image",
            files={"file": ("sample.png", _PNG, "image/png")},
        )

    @task(1)
    def check_health(self):
        self.client.get("/health")

    @task(1)
    def get_supported_formats(self):
        self.client.get("/formats")
