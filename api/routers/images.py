"""Image upload and retrieval endpoints (GridFS-backed)."""

from __future__ import annotations

import hashlib
import io
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from api.config import settings
from api.dependencies import get_gridfs, get_session
from api.services.database import get_db
from api.services.image_storage import stream_image

router = APIRouter(prefix="/api/sessions/{slug}", tags=["images"])

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}

CONTENT_TYPE_MAP = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".bmp": "image/bmp",
    ".tiff": "image/tiff",
    ".tif": "image/tiff",
    ".webp": "image/webp",
}


@router.post("/upload")
async def upload_image(slug: str, file: UploadFile):
    session = await get_session(slug)
    db = get_db()
    bucket = get_gridfs()

    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    ext = Path(file.filename or "upload.png").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {ext}")

    content = await file.read()
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(
            status_code=400, detail=f"File too large (max {settings.max_upload_mb}MB)"
        )

    sha = hashlib.sha256(content).hexdigest()

    # Deduplicate: if an image with the same hash already exists, return that session
    existing = await db.sessions.find_one({"image.sha256": sha})
    if existing:
        return {
            "status": "ok",
            "slug": existing["slug"],
            "filename": existing["image"]["original_name"],
            "sha256": sha,
            "existing": True,
        }

    content_type = CONTENT_TYPE_MAP.get(ext, "image/png")
    filename = f"{slug}_{sha[:12]}{ext}"

    # Check if a GridFS file with same sha256 already exists (orphaned dedup)
    existing_cursor = bucket.find({"metadata.sha256": sha})
    existing_gridfs = await existing_cursor.to_list(length=1)
    if existing_gridfs:
        file_id = existing_gridfs[0]._id
    else:
        file_id = await bucket.upload_from_stream(
            filename,
            content,
            metadata={
                "sha256": sha,
                "content_type": content_type,
                "original_name": file.filename,
            },
        )

    await db.sessions.update_one(
        {"slug": slug},
        {
            "$set": {
                "image": {
                    "file_id": file_id,
                    "sha256": sha,
                    "content_type": content_type,
                    "original_name": file.filename,
                },
                "results": None,  # Invalidate cached results
                "expires_at": datetime.now(timezone.utc)
                + timedelta(days=settings.session_ttl_days),
            }
        },
    )

    return {"status": "ok", "slug": slug, "filename": filename, "sha256": sha}


@router.get("/image")
async def get_image(slug: str):
    session = await get_session(slug)
    data, content_type = await stream_image(session)

    return StreamingResponse(
        io.BytesIO(data),
        media_type=content_type,
        headers={
            "Cache-Control": "public, max-age=86400",
        },
    )
