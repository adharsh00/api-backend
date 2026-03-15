import logging
import httpx
from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter()
logger = logging.getLogger(__name__)

_TIMEOUT = httpx.Timeout(30.0)
_MAX_TRIALS_PAGE = 50


@router.post("/upload")
async def upload_to_fileio(file: UploadFile = File(...)):
    """Upload a file to file.io and return the MIME type and metadata.

    Used by the frontend to obtain a pre-upload MIME type before sending the
    file to /validate-image.
    """
    contents = await file.read()
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        try:
            resp = await client.post(
                "https://file.io",
                files={"file": (file.filename, contents, file.content_type)},
            )
            return resp.json()
        except httpx.RequestError as exc:
            raise HTTPException(status_code=503, detail=f"file.io unavailable: {exc}")


@router.get("/trials")
async def search_trials(condition: str = "medical imaging", page_size: int = 5):
    """Search ClinicalTrials.gov for studies matching *condition*.

    Returns up to *page_size* results (capped at 50 to stay within rate limits).
    """
    page_size = min(page_size, _MAX_TRIALS_PAGE)
    async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
        try:
            resp = await client.get(
                "https://clinicaltrials.gov/api/v2/studies",
                params={"query.cond": condition, "pageSize": page_size, "format": "json"},
            )
            return resp.json()
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=503, detail=f"ClinicalTrials.gov unavailable: {exc}"
            )
