import logging
import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from app.config import CLASSMATE_API_URL, CLASSMATE_API_KEY

router = APIRouter()
logger = logging.getLogger(__name__)

_HEADERS = {"X-API-Key": CLASSMATE_API_KEY}
_TIMEOUT = httpx.Timeout(10.0)


def _proxy_error(exc: Exception) -> HTTPException:
    return HTTPException(status_code=503, detail=f"Classmate API unavailable: {exc}")


@router.get("/health")
async def appointments_health():
    """Check classmate Healthcare Appointment API health."""
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        try:
            resp = await client.get(f"{CLASSMATE_API_URL}/health")
            return JSONResponse(content=resp.json(), status_code=resp.status_code)
        except httpx.RequestError as exc:
            raise _proxy_error(exc)


@router.get("/slots")
async def get_slots(doctor: str = ""):
    """Return available appointment slots, optionally filtered by doctor."""
    params = {"doctor": doctor} if doctor else {}
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        try:
            resp = await client.get(f"{CLASSMATE_API_URL}/slots", params=params)
            return JSONResponse(content=resp.json(), status_code=resp.status_code)
        except httpx.RequestError as exc:
            raise _proxy_error(exc)


@router.post("/reserve")
async def reserve_slot(request: Request):
    """Reserve an appointment slot. Forwards the JSON body to the classmate API."""
    body = await request.json()
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        try:
            resp = await client.post(
                f"{CLASSMATE_API_URL}/reserve",
                json=body,
                headers=_HEADERS,
            )
            return JSONResponse(content=resp.json(), status_code=resp.status_code)
        except httpx.RequestError as exc:
            raise _proxy_error(exc)


@router.delete("/reserve/{reservation_id}")
async def cancel_reservation(reservation_id: str):
    """Cancel an existing reservation by ID."""
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        try:
            resp = await client.delete(
                f"{CLASSMATE_API_URL}/reserve/{reservation_id}",
                headers=_HEADERS,
            )
            return JSONResponse(content=resp.json(), status_code=resp.status_code)
        except httpx.RequestError as exc:
            raise _proxy_error(exc)


@router.get("/reservations")
async def get_reservations(doctor: str = ""):
    """View all reservations, optionally filtered by doctor."""
    params = {"doctor": doctor} if doctor else {}
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        try:
            resp = await client.get(
                f"{CLASSMATE_API_URL}/reservations",
                params=params,
                headers=_HEADERS,
            )
            return JSONResponse(content=resp.json(), status_code=resp.status_code)
        except httpx.RequestError as exc:
            raise _proxy_error(exc)
