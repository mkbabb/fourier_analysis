"""Centralized GridFS image storage operations."""

from __future__ import annotations

import tempfile
from pathlib import Path

import bson.errors
import gridfs.errors
from bson import ObjectId
from fastapi import HTTPException

from api.dependencies import get_gridfs


async def download_to_tempfile(session: dict) -> Path:
    """Download a session's image from GridFS to a temporary file.

    Raises HTTPException if no image is attached or the file is missing.
    """
    if not session.get("image"):
        raise HTTPException(
            status_code=400, detail="No image uploaded for this session"
        )

    image_meta = session["image"]
    if "file_id" not in image_meta:
        raise HTTPException(
            status_code=400,
            detail="Image stored in legacy format — please re-upload",
        )

    bucket = get_gridfs()
    file_id = image_meta["file_id"]

    try:
        grid_out = await bucket.open_download_stream(ObjectId(file_id))
    except (bson.errors.InvalidId, gridfs.errors.NoFile):
        raise HTTPException(status_code=404, detail="Image file not found in storage")

    data = await grid_out.read()

    original = image_meta.get("original_name", "image.png")
    ext = Path(original).suffix.lower() or ".png"

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    tmp.write(data)
    tmp.close()
    return Path(tmp.name)


async def stream_image(session: dict) -> tuple[bytes, str]:
    """Read a session's image from GridFS, returning (data, content_type).

    Raises HTTPException if no image or file not found.
    """
    if not session.get("image"):
        raise HTTPException(status_code=404, detail="No image uploaded")

    image_meta = session["image"]

    if "file_id" not in image_meta:
        raise HTTPException(
            status_code=404,
            detail="Image stored in legacy format — please re-upload",
        )

    bucket = get_gridfs()
    try:
        grid_out = await bucket.open_download_stream(ObjectId(image_meta["file_id"]))
    except (bson.errors.InvalidId, gridfs.errors.NoFile):
        raise HTTPException(status_code=404, detail="Image file not found in storage")

    data = await grid_out.read()
    content_type = image_meta.get("content_type", "image/png")
    return data, content_type


async def delete_image(session: dict) -> None:
    """Best-effort deletion of a session's GridFS image file."""
    if not session.get("image") or not session["image"].get("file_id"):
        return
    bucket = get_gridfs()
    try:
        await bucket.delete(ObjectId(session["image"]["file_id"]))
    except Exception:
        pass  # Best-effort cleanup — GridFS delete shouldn't block session deletion
