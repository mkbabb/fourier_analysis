"""Admin moderation endpoints for gallery management."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Request

from api.dependencies import (
    admin_required,
    get_client_ip,
    hash_ip,
)
from api.models.gallery import (
    AdminStatsResponse,
    GalleryEntryResponse,
    GalleryTier,
    SetTierRequest,
)
from api.routers.gallery import _entry_from_doc
from api.services.database import get_db
from api.services.rate_limiter import admin_limiter

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

admin_router = APIRouter(prefix="/api/admin", tags=["admin"])

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def log_audit(ip_hash: str, action: str, target: str) -> None:
    db = get_db()
    await db.admin_audit.insert_one(
        {
            "timestamp": datetime.now(UTC),
            "ip_hash": ip_hash,
            "action": action,
            "target": target,
        }
    )


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------


@admin_router.get("/verify", dependencies=[Depends(admin_required)])
async def admin_verify():
    """Verify admin token is valid."""
    return {"ok": True}


@admin_router.get("/stats", response_model=AdminStatsResponse, dependencies=[Depends(admin_required)])
async def admin_stats():
    """Aggregate gallery and storage statistics."""
    db = get_db()

    # Count entries by tier
    pipeline = [
        {"$group": {"_id": "$tier", "count": {"$sum": 1}}},
    ]
    tier_counts = {"featured": 0, "saved": 0, "normal": 0}
    async for row in db.gallery.aggregate(pipeline):
        tier_id = row["_id"]
        if tier_id in tier_counts:
            tier_counts[tier_id] = row["count"]

    total_entries = sum(tier_counts.values())

    # Sum views and likes
    totals_pipeline = [
        {
            "$group": {
                "_id": None,
                "total_views": {"$sum": "$views"},
                "total_likes": {"$sum": "$likes"},
            }
        }
    ]
    totals = {"total_views": 0, "total_likes": 0}
    async for row in db.gallery.aggregate(totals_pipeline):
        totals["total_views"] = row.get("total_views", 0)
        totals["total_likes"] = row.get("total_likes", 0)

    # Storage from images collection
    storage_pipeline = [
        {"$group": {"_id": None, "total_bytes": {"$sum": "$bytes"}}},
    ]
    storage_bytes = 0
    async for row in db.images.aggregate(storage_pipeline):
        storage_bytes = row.get("total_bytes", 0)

    return AdminStatsResponse(
        total_entries=total_entries,
        featured=tier_counts["featured"],
        saved=tier_counts["saved"],
        normal=tier_counts["normal"],
        total_views=totals["total_views"],
        total_likes=totals["total_likes"],
        storage_bytes=storage_bytes,
    )


@admin_router.put(
    "/gallery/{hash}/tier",
    response_model=GalleryEntryResponse,
    dependencies=[Depends(admin_required)],
)
async def set_tier(hash: str, body: SetTierRequest, request: Request):
    """Set the tier for a gallery entry."""
    client_ip = get_client_ip(request)
    ip_hashed = hash_ip(client_ip)
    admin_limiter.check(ip_hashed)

    db = get_db()
    result = await db.gallery.update_one(
        {"snapshot_hash": hash},
        {"$set": {"tier": body.tier, "updated_at": datetime.now(UTC)}},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Gallery entry not found")

    await log_audit(ip_hashed, "set_tier", hash)

    doc = await db.gallery.find_one({"snapshot_hash": hash})
    return _entry_from_doc(doc)


@admin_router.delete("/gallery/{hash}", dependencies=[Depends(admin_required)])
async def delete_gallery_entry(hash: str, request: Request):
    """Delete a gallery entry."""
    client_ip = get_client_ip(request)
    ip_hashed = hash_ip(client_ip)
    admin_limiter.check(ip_hashed)

    db = get_db()
    result = await db.gallery.delete_one({"snapshot_hash": hash})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Gallery entry not found")

    await log_audit(ip_hashed, "delete", hash)

    return {"ok": True}
