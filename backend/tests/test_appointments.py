"""Tests for the appointments proxy routes."""
import pytest
from app.routes.appointments import router


def test_appointments_router_imported():
    """Smoke test: the appointments router loads without errors."""
    assert router is not None


def test_appointments_router_has_routes():
    """Verify that all expected route paths are registered."""
    paths = {r.path for r in router.routes}
    assert "/health" in paths
    assert "/slots" in paths
    assert "/reserve" in paths
    assert "/reservations" in paths
