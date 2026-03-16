"""Background cleanup task for expired assets."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from api.config import get_settings
from api.services.database import get_db

logger = logging.getLogger(__name__)


async def run_janitor() -> None:
    """Delete unpinned assets older than max_age_days. Run on startup + every 6 hours."""
    while True:
        try:
            await _cleanup_cycle()
        except Exception:
            logger.exception("Janitor cycle failed")
        await asyncio.sleep(6 * 3600)


async def _cleanup_cycle() -> None:
    settings = get_settings()
    db = get_db()
    cutoff = datetime.now(UTC) - timedelta(days=settings.asset_max_age_days)

    # ------------------------------------------------------------------
    # 1. Collect pinned assets from snapshots AND gallery
    # ------------------------------------------------------------------

    pinned_contours: set[str] = set()
    pinned_images: set[str] = set()
    pinned_snapshots: set[str] = set()

    # Snapshots pin their own contour + image
    async for snap in db.snapshots.find({}, {"contour_hash": 1, "image_slug": 1, "snapshot_hash": 1}):
        pinned_contours.add(snap["contour_hash"])
        if snap.get("image_slug"):
            pinned_images.add(snap["image_slug"])

    # Gallery entries with tier featured or saved additionally pin their assets
    async for entry in db.gallery.find(
        {"tier": {"$in": ["featured", "saved"]}},
        {"snapshot_hash": 1, "image_slug": 1, "contour_hash": 1},
    ):
        pinned_snapshots.add(entry["snapshot_hash"])
        if entry.get("image_slug"):
            pinned_images.add(entry["image_slug"])
        if entry.get("contour_hash"):
            pinned_contours.add(entry["contour_hash"])

    # ------------------------------------------------------------------
    # 2. Time-based cleanup of old unpinned assets
    # ------------------------------------------------------------------

    # Delete old unpinned contours
    result = await db.contours.delete_many(
        {
            "last_accessed_at": {"$lt": cutoff},
            "contour_hash": {"$nin": list(pinned_contours)},
        }
    )
    if result.deleted_count:
        logger.info("Janitor deleted %d old contours", result.deleted_count)

    # Delete old unpinned images and cascade to gallery
    deleted_images = await _delete_images_and_cascade(
        db,
        {
            "last_accessed_at": {"$lt": cutoff},
            "image_slug": {"$nin": list(pinned_images)},
        },
    )
    if deleted_images:
        logger.info("Janitor deleted %d old images", deleted_images)

    # ------------------------------------------------------------------
    # 3. Storage budget enforcement
    # ------------------------------------------------------------------

    budget_bytes = int(settings.storage_budget_gb * 1024 * 1024 * 1024)
    storage_pipeline = [
        {"$group": {"_id": None, "total_bytes": {"$sum": "$bytes"}}},
    ]
    total_bytes = 0
    async for row in db.images.aggregate(storage_pipeline):
        total_bytes = row.get("total_bytes", 0)

    if total_bytes > budget_bytes:
        overage = total_bytes - budget_bytes
        logger.warning(
            "Storage budget exceeded by %d bytes (%d total vs %d budget). "
            "Evicting oldest unpinned images.",
            overage,
            total_bytes,
            budget_bytes,
        )
        freed = 0
        cursor = db.images.find(
            {"image_slug": {"$nin": list(pinned_images)}},
            {"image_slug": 1, "bytes": 1},
        ).sort("last_accessed_at", 1)

        async for img_doc in cursor:
            if freed >= overage:
                break
            slug = img_doc["image_slug"]
            img_bytes = img_doc.get("bytes", 0)
            count = await _delete_images_and_cascade(
                db, {"image_slug": slug}
            )
            if count:
                freed += img_bytes
                logger.info(
                    "Budget eviction: deleted image %s (%d bytes)", slug, img_bytes
                )

    # ------------------------------------------------------------------
    # 4. Session + user cleanup
    # ------------------------------------------------------------------

    now = datetime.now(UTC)

    # Expired sessions
    result = await db.sessions.delete_many({"expires_at": {"$lt": now}})
    if result.deleted_count:
        logger.info("Janitor deleted %d expired sessions", result.deleted_count)

    # Users unseen for user_max_age_days
    user_cutoff = now - timedelta(days=settings.user_max_age_days)
    result = await db.users.delete_many({"last_seen_at": {"$lt": user_cutoff}})
    if result.deleted_count:
        logger.info("Janitor deleted %d stale users", result.deleted_count)


async def _delete_images_and_cascade(db, filter_: dict) -> int:
    """Delete images matching *filter_* and cascade-delete referencing gallery entries.

    Returns the number of deleted images.
    """
    # Collect slugs of images about to be deleted
    slugs_to_delete: list[str] = []
    async for img in db.images.find(filter_, {"image_slug": 1}):
        slugs_to_delete.append(img["image_slug"])

    if not slugs_to_delete:
        return 0

    # Cascade: delete gallery entries that reference these images
    cascade_result = await db.gallery.delete_many(
        {"image_slug": {"$in": slugs_to_delete}}
    )
    if cascade_result.deleted_count:
        logger.info(
            "Janitor cascade-deleted %d gallery entries for deleted images",
            cascade_result.deleted_count,
        )

    # Delete the images themselves
    result = await db.images.delete_many(filter_)
    return result.deleted_count
