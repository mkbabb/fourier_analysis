"""Gallery browsing and publishing endpoints."""

from __future__ import annotations

import math
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query, Request

from api.dependencies import (
    get_client_ip,
    hash_ip,
    resolve_session,
)
from api.models.gallery import (
    GalleryEntryResponse,
    GalleryListResponse,
    PublishRequest,
)
from api.services.database import get_db
from api.services.rate_limiter import like_limiter, write_limiter

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

gallery_router = APIRouter(prefix="/api/gallery", tags=["gallery"])

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SORT_KEYS = {
    "newest": ("created_at", -1),
    "views": ("views", -1),
    "likes": ("likes", -1),
}


def _entry_from_doc(doc: dict) -> GalleryEntryResponse:
    """Build a response model from a MongoDB gallery document."""
    data = {k: v for k, v in doc.items() if k not in ("_id", "liked_ips")}
    return GalleryEntryResponse(**data)


# ---------------------------------------------------------------------------
# Public gallery endpoints
# ---------------------------------------------------------------------------


@gallery_router.get("", response_model=GalleryListResponse)
async def list_gallery(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    sort: str = Query(default="newest"),
    tier: str = Query(default="all"),
    q: str = Query(default=""),
    basis: str = Query(default=""),
):
    """List gallery entries with filtering, sorting, and pagination."""
    db = get_db()

    # Build filter
    query_filter: dict = {}
    if tier != "all":
        query_filter["tier"] = tier
    if q:
        query_filter["image_slug"] = {"$regex": q, "$options": "i"}
    if basis:
        query_filter["active_bases"] = basis

    # Sort
    sort_field, sort_dir = SORT_KEYS.get(sort, SORT_KEYS["newest"])

    total = await db.gallery.count_documents(query_filter)
    pages = math.ceil(total / limit) if total > 0 else 1
    skip = (page - 1) * limit

    cursor = (
        db.gallery.find(query_filter, {"liked_ips": 0})
        .sort(sort_field, sort_dir)
        .skip(skip)
        .limit(limit)
    )
    items = [_entry_from_doc(doc) async for doc in cursor]

    return GalleryListResponse(items=items, total=total, page=page, pages=pages)


@gallery_router.get("/{hash}", response_model=GalleryEntryResponse)
async def get_gallery_entry(hash: str):
    """Fetch a single gallery entry by snapshot_hash."""
    db = get_db()
    doc = await db.gallery.find_one({"snapshot_hash": hash})
    if doc is None:
        raise HTTPException(status_code=404, detail="Gallery entry not found")
    return _entry_from_doc(doc)


@gallery_router.post("", response_model=GalleryEntryResponse)
async def publish_to_gallery(body: PublishRequest, request: Request):
    """Publish a snapshot to the gallery."""
    client_ip = get_client_ip(request)
    ip_hashed = hash_ip(client_ip)
    write_limiter.check(ip_hashed)

    user_slug = await resolve_session(request)

    db = get_db()

    # Verify snapshot exists
    snapshot = await db.snapshots.find_one({"snapshot_hash": body.snapshot_hash})
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    # Check for duplicate
    existing = await db.gallery.find_one({"snapshot_hash": body.snapshot_hash})
    if existing is not None:
        raise HTTPException(status_code=409, detail="Snapshot already published")

    now = datetime.now(UTC)

    # Extract denormalized fields from snapshot's nested settings
    anim_settings = snapshot.get("animation_settings", {})
    contour_settings = snapshot.get("contour_settings", {})
    active_bases = anim_settings.get("active_bases", [])
    n_harmonics = contour_settings.get("n_harmonics", 0)

    gallery_doc = {
        "snapshot_hash": body.snapshot_hash,
        "image_slug": body.image_slug,
        "contour_hash": snapshot.get("contour_hash", ""),
        "user_slug": user_slug,
        "tier": "normal",
        "views": 0,
        "likes": 0,
        "liked_ips": [],
        "active_bases": active_bases,
        "n_harmonics": n_harmonics,
        "created_at": now,
        "updated_at": now,
    }

    await db.gallery.insert_one(gallery_doc)
    return _entry_from_doc(gallery_doc)


@gallery_router.post("/{hash}/view")
async def increment_view(hash: str):
    """Increment the view counter for a gallery entry."""
    db = get_db()
    result = await db.gallery.update_one(
        {"snapshot_hash": hash},
        {"$inc": {"views": 1}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Gallery entry not found")

    doc = await db.gallery.find_one({"snapshot_hash": hash}, {"views": 1})
    return {"views": doc["views"]}


@gallery_router.post("/{hash}/like")
async def toggle_like(hash: str, request: Request):
    """Toggle a like for a gallery entry, keyed by hashed IP."""
    client_ip = get_client_ip(request)
    ip_hashed = hash_ip(client_ip)
    like_limiter.check(ip_hashed)

    db = get_db()
    doc = await db.gallery.find_one({"snapshot_hash": hash})
    if doc is None:
        raise HTTPException(status_code=404, detail="Gallery entry not found")

    liked_ips: list = doc.get("liked_ips", [])
    if ip_hashed in liked_ips:
        # Unlike
        await db.gallery.update_one(
            {"snapshot_hash": hash},
            {"$pull": {"liked_ips": ip_hashed}, "$inc": {"likes": -1}},
        )
        liked = False
    else:
        # Like
        await db.gallery.update_one(
            {"snapshot_hash": hash},
            {"$push": {"liked_ips": ip_hashed}, "$inc": {"likes": 1}},
        )
        liked = True

    updated = await db.gallery.find_one({"snapshot_hash": hash}, {"likes": 1})
    return {"liked": liked, "likes": updated["likes"]}
