"""Shared FastAPI dependencies."""

from __future__ import annotations

import io
import logging
import re

from fastapi import HTTPException
from PIL import Image, ImageOps

from api.services.database import get_db, touch_document

logger = logging.getLogger(__name__)

SLUG_PATTERN = re.compile(r"^[a-zA-Z0-9][-a-zA-Z0-9]{2,80}$")


def validate_image_slug(slug: str) -> str:
    if not SLUG_PATTERN.match(slug):
        raise HTTPException(status_code=400, detail="Invalid image slug")
    return slug


async def get_image_asset(image_slug: str) -> dict:
    """Fetch full image document (including blob). 404 if not found."""
    image_slug = validate_image_slug(image_slug)
    db = get_db()
    doc = await db.images.find_one({"image_slug": image_slug})
    if doc is None:
        raise HTTPException(status_code=404, detail="Image not found")
    await touch_document("images", {"image_slug": image_slug})
    return doc


async def get_image_meta(image_slug: str) -> dict:
    """Fetch image metadata (excluding blob). 404 if not found."""
    image_slug = validate_image_slug(image_slug)
    db = get_db()
    doc = await db.images.find_one({"image_slug": image_slug}, {"blob": 0})
    if doc is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return doc


async def get_contour(contour_hash: str) -> dict:
    """Fetch contour document. 404 if not found.

    Lazily backfills ``image_bounds`` for pre-migration contours by loading
    the linked image, applying the same resize logic as contour extraction,
    and persisting the computed bounds.
    """
    db = get_db()
    doc = await db.contours.find_one({"contour_hash": contour_hash})
    if doc is None:
        raise HTTPException(status_code=404, detail="Contour not found")
    await touch_document("contours", {"contour_hash": contour_hash})

    if doc.get("image_bounds") is None and doc.get("image_slug"):
        doc = await _backfill_image_bounds(db, doc)

    return doc


async def _backfill_image_bounds(db, contour_doc: dict) -> dict:
    """Compute and persist image_bounds for a contour that lacks it."""
    from bson import Binary

    image_doc = await db.images.find_one(
        {"image_slug": contour_doc["image_slug"]},
        {"blob": 1, "content_type": 1},
    )
    if image_doc is None:
        return contour_doc

    try:
        blob = image_doc["blob"]
        data = bytes(blob) if isinstance(blob, Binary) else blob
        img = Image.open(io.BytesIO(data))
        img = ImageOps.exif_transpose(img)
        orig_w, orig_h = img.size
        img.close()

        # Use default extraction resize of 768
        resize = 768
        ratio = resize / max(orig_w, orig_h)
        rw = int(orig_w * ratio)
        rh = int(orig_h * ratio)

        image_bounds = {
            "minX": -rw / 2,
            "maxX": rw / 2,
            "minY": -rh / 2,
            "maxY": rh / 2,
        }

        await db.contours.update_one(
            {"_id": contour_doc["_id"]},
            {"$set": {"image_bounds": image_bounds}},
        )
        contour_doc["image_bounds"] = image_bounds
        logger.info("Backfilled image_bounds for contour %s", contour_doc["contour_hash"])
    except Exception:
        logger.warning("Failed to backfill image_bounds for %s", contour_doc.get("contour_hash"), exc_info=True)

    return contour_doc
