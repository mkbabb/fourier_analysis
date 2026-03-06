"""Image upload and retrieval endpoints."""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from pathlib import Path

import aiofiles
from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import FileResponse

from api.config import settings
from api.dependencies import get_session, validate_slug
from api.services.database import get_db

router = APIRouter(prefix="/api/sessions/{slug}", tags=["images"])

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}


def _upload_dir() -> Path:
    p = Path(settings.upload_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


@router.post("/upload")
async def upload_image(slug: str, file: UploadFile):
    session = await get_session(slug)
    db = get_db()

    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    ext = Path(file.filename or "upload.png").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {ext}")

    content = await file.read()
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(status_code=400, detail=f"File too large (max {settings.max_upload_mb}MB)")

    sha = hashlib.sha256(content).hexdigest()
    filename = f"{slug}_{sha[:12]}{ext}"
    filepath = _upload_dir() / filename

    async with aiofiles.open(filepath, "wb") as f:
        await f.write(content)

    await db.sessions.update_one(
        {"slug": slug},
        {
            "$set": {
                "image": {
                    "filename": filename,
                    "path": str(filepath),
                    "sha256": sha,
                    "original_name": file.filename,
                },
                "results": None,  # Invalidate cached results
                "expires_at": datetime.now(timezone.utc)
                + timedelta(days=settings.session_ttl_days),
            }
        },
    )

    return {"status": "ok", "filename": filename, "sha256": sha}


@router.get("/image")
async def get_image(slug: str):
    session = await get_session(slug)

    if not session.get("image"):
        raise HTTPException(status_code=404, detail="No image uploaded")

    filepath = Path(session["image"]["path"])
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Image file not found")

    return FileResponse(filepath, media_type="image/png")
