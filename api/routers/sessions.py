"""Session CRUD endpoints."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from bson import ObjectId
from fastapi import APIRouter, HTTPException

from api.config import settings
from api.dependencies import get_gridfs, get_session, validate_slug
from api.models.session import (
    AnimationSettings,
    ContourSettings,
    SessionResponse,
    SessionUpdate,
)
from api.services.database import get_db
from api.slugs import generate_slug

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.post("", response_model=SessionResponse)
async def create_session():
    db = get_db()
    slug = generate_slug()
    # Ensure uniqueness
    while await db.sessions.find_one({"slug": slug}):
        slug = generate_slug()

    now = datetime.now(timezone.utc)
    doc = {
        "slug": slug,
        "created_at": now,
        "expires_at": now + timedelta(days=settings.session_ttl_days),
        "parameters": ContourSettings().model_dump(),
        "animation_settings": AnimationSettings().model_dump(),
        "image": None,
        "results": None,
    }
    await db.sessions.insert_one(doc)
    return SessionResponse(
        slug=slug,
        created_at=now,
        parameters=ContourSettings(),
        animation_settings=AnimationSettings(),
    )


@router.get("/{slug}", response_model=SessionResponse)
async def get_session_endpoint(slug: str):
    session = await get_session(slug)
    return SessionResponse(
        slug=session["slug"],
        created_at=session["created_at"],
        parameters=ContourSettings(**session["parameters"]),
        animation_settings=AnimationSettings(**session["animation_settings"]),
        has_image=session.get("image") is not None,
        has_results=session.get("results") is not None,
    )


@router.put("/{slug}", response_model=SessionResponse)
async def update_session(slug: str, update: SessionUpdate):
    session = await get_session(slug)
    db = get_db()

    update_doc: dict = {}
    if update.parameters is not None:
        update_doc["parameters"] = update.parameters.model_dump()
    if update.animation_settings is not None:
        update_doc["animation_settings"] = update.animation_settings.model_dump()

    if update_doc:
        # Refresh TTL
        update_doc["expires_at"] = datetime.now(timezone.utc) + timedelta(
            days=settings.session_ttl_days
        )
        await db.sessions.update_one({"slug": slug}, {"$set": update_doc})

    updated = await db.sessions.find_one({"slug": slug})
    return SessionResponse(
        slug=updated["slug"],
        created_at=updated["created_at"],
        parameters=ContourSettings(**updated["parameters"]),
        animation_settings=AnimationSettings(**updated["animation_settings"]),
        has_image=updated.get("image") is not None,
        has_results=updated.get("results") is not None,
    )


@router.delete("/{slug}")
async def delete_session(slug: str):
    validate_slug(slug)
    db = get_db()

    # Retrieve session first so we can clean up its GridFS file
    session = await db.sessions.find_one({"slug": slug})
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # Delete the associated GridFS image file if present
    if session.get("image") and session["image"].get("file_id"):
        bucket = get_gridfs()
        try:
            await bucket.delete(ObjectId(session["image"]["file_id"]))
        except Exception:
            pass  # Best-effort cleanup; don't fail the deletion

    await db.sessions.delete_one({"slug": slug})
    return {"status": "deleted"}
