"""Shared FastAPI dependencies."""

from __future__ import annotations

import hashlib
import hmac
import io
import logging
import re
from datetime import UTC, datetime

from fastapi import HTTPException, Request
from PIL import Image, ImageOps
from pymongo import ReturnDocument

from api.config import settings
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


# ---------------------------------------------------------------------------
# Auth / session helpers
# ---------------------------------------------------------------------------


def get_client_ip(request: Request) -> str:
    """Extract client IP from X-Forwarded-For or request.client."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[-1].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    if request.client:
        return request.client.host
    logger.warning("Could not determine client IP")
    return "unknown"


def hash_ip(ip: str) -> str:
    """SHA-256 hash of IP address for privacy-safe storage."""
    return hashlib.sha256(ip.encode()).hexdigest()


async def resolve_session(request: Request) -> str | None:
    """Extract X-Session-Token, resolve to user_slug.
    Returns None if no header. Raises 401 if header present but invalid/expired."""
    token = request.headers.get("X-Session-Token")
    if not token:
        return None
    db = get_db()
    session = await db.sessions.find_one_and_update(
        {"_id": token, "expires_at": {"$gt": datetime.now(UTC)}},
        {"$set": {"last_seen_at": datetime.now(UTC)}},
        return_document=ReturnDocument.AFTER,
    )
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    # Also touch the user
    await db.users.update_one(
        {"_id": session["user_slug"]},
        {"$set": {"last_seen_at": datetime.now(UTC)}},
    )
    return session["user_slug"]


async def require_session(request: Request) -> str:
    """Dependency that requires a valid session."""
    user_slug = await resolve_session(request)
    if not user_slug:
        raise HTTPException(status_code=401, detail="Session required")
    return user_slug


async def admin_required(request: Request) -> bool:
    """Timing-safe Bearer token validation."""
    if not settings.admin_token:
        raise HTTPException(status_code=503, detail="Admin not configured")
    auth = request.headers.get("Authorization", "")
    expected = f"Bearer {settings.admin_token}"
    if not hmac.compare_digest(auth.encode(), expected.encode()):
        raise HTTPException(status_code=403, detail="Forbidden")
    return True
