"""Image upload and retrieval endpoints (asset-based)."""

from __future__ import annotations

import hashlib
import io
import logging
import os
from pathlib import Path

from bson import Binary
from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)

from api.config import settings
from api.dependencies import get_image_asset, get_image_meta, validate_image_slug
from api.models.assets import (
    ExtractContourRequest,
    ImageAssetResponse,
)
from api.responses import contour_response
from api.services import computation
from api.services.database import get_db
from api.services.image_storage import (
    image_bytes,
    image_tempfile,
    store_contour_asset,
    store_image_asset,
)
from fourier_analysis.contours import resample_arc_length
from fourier_analysis.shortest_tour import build_contour_tour

import numpy as np

router = APIRouter(prefix="/api/images", tags=["images"])

ALLOWED_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp",
    ".gif", ".heic", ".heif", ".avif",
}

CONTENT_TYPE_MAP = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".bmp": "image/bmp",
    ".tiff": "image/tiff",
    ".tif": "image/tiff",
    ".webp": "image/webp",
    ".gif": "image/gif",
    ".heic": "image/heic",
    ".heif": "image/heif",
    ".avif": "image/avif",
}


def _image_response(doc: dict) -> ImageAssetResponse:
    return ImageAssetResponse(
        image_slug=doc["image_slug"],
        sha256=doc["sha256"],
        original_name=doc["original_name"],
        content_type=doc["content_type"],
        bytes=doc["bytes"],
        created_at=doc["created_at"],
        last_accessed_at=doc["last_accessed_at"],
    )


@router.post("", response_model=ImageAssetResponse)
async def upload_image(file: UploadFile):
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
    content_type = CONTENT_TYPE_MAP.get(ext, "image/png")

    doc = await store_image_asset(sha, content, file.filename or "upload.png", content_type)
    return _image_response(doc)


@router.get("/by-hash/{sha256}", response_model=ImageAssetResponse)
async def get_image_by_hash(sha256: str):
    db = get_db()
    doc = await db.images.find_one({"sha256": sha256}, {"blob": 0})
    if doc is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return _image_response(doc)


@router.get("/{imageSlug}", response_model=ImageAssetResponse)
async def get_image_metadata(imageSlug: str):
    doc = await get_image_meta(imageSlug)
    return _image_response(doc)


@router.get("/{imageSlug}/blob")
async def get_image_blob(imageSlug: str):
    doc = await get_image_asset(imageSlug)
    data, content_type = image_bytes(doc)
    return StreamingResponse(
        io.BytesIO(data),
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )


@router.get("/{imageSlug}/thumbnail")
async def get_image_thumbnail(imageSlug: str):
    doc = await get_image_asset(imageSlug)
    # Serve thumbnail if available, otherwise fall back to original blob
    if doc.get("thumbnail"):
        data = bytes(doc["thumbnail"]) if isinstance(doc["thumbnail"], Binary) else doc["thumbnail"]
        content_type = doc.get("thumbnail_content_type", "image/avif")
    else:
        data, content_type = image_bytes(doc)
    return StreamingResponse(
        io.BytesIO(data),
        media_type=content_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )


@router.get("/{imageSlug}/overlay")
async def get_image_overlay(imageSlug: str, resize: int = 768):
    """Serve the image resized to match contour extraction dimensions.

    The returned image is in the same pixel space that contour coordinates
    were extracted from, enabling pixel-perfect overlay alignment.
    """
    from PIL import Image as PILImage

    doc = await get_image_asset(imageSlug)
    data, _ = image_bytes(doc)

    def _resize():
        from PIL import ImageOps
        img = PILImage.open(io.BytesIO(data))
        img = ImageOps.exif_transpose(img)
        img = img.convert("RGB")
        if resize:
            ratio = resize / max(img.size)
            new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
            img = img.resize(new_size, PILImage.Resampling.LANCZOS)
        buf = io.BytesIO()
        try:
            img.save(buf, format="AVIF", quality=70)
            ct = "image/avif"
        except Exception:
            img.save(buf, format="WEBP", quality=80)
            ct = "image/webp"
        return buf.getvalue(), ct, img.size

    import asyncio
    overlay_bytes, content_type, (w, h) = await asyncio.to_thread(_resize)

    return StreamingResponse(
        io.BytesIO(overlay_bytes),
        media_type=content_type,
        headers={
            "Cache-Control": "public, max-age=86400",
            "X-Image-Width": str(w),
            "X-Image-Height": str(h),
        },
    )


@router.post("/{imageSlug}/extract-contour")
async def extract_contour(imageSlug: str, req: ExtractContourRequest):
    doc = await get_image_asset(imageSlug)
    tmp = image_tempfile(doc)
    try:
        cs = req.contour_settings
        result = await computation.compute_contours(
            Path(tmp.name),
            strategy=cs.strategy,
            resize=cs.resize,
            blur_sigma=cs.blur_sigma,
            n_classes=cs.n_classes,
            min_contour_length=cs.min_contour_length,
            min_contour_area=cs.min_contour_area,
            max_contours=cs.max_contours,
            smooth_contours=cs.smooth_contours,
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("extract-contour failed for %s", imageSlug)
        raise
    finally:
        tmp.close()
        os.unlink(tmp.name)

    contours = result.get("contours", [])
    if not contours:
        raise HTTPException(
            status_code=422,
            detail="No contours extracted — try lowering min area or changing strategy",
        )

    image_bounds = result.get("image_bounds")

    # Combine all contours, order, and resample to n_points
    complex_contours = [
        np.array(c["x"]) + 1j * np.array(c["y"]) for c in contours
    ]
    path = build_contour_tour(complex_contours).path
    path = resample_arc_length(path, cs.n_points)
    xs = path.real.tolist()
    ys = path.imag.tolist()

    contour_doc = await store_contour_asset(
        xs, ys, imageSlug, source="extract", image_bounds=image_bounds,
    )
    return contour_response(contour_doc)
