"""Shared FastAPI dependencies."""

from __future__ import annotations

import re

from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorGridFSBucket

from api.services.database import get_db

SLUG_PATTERN = re.compile(r"^[a-zA-Z0-9][-a-zA-Z0-9]{2,80}$")


def validate_slug(slug: str) -> str:
    if not SLUG_PATTERN.match(slug):
        raise HTTPException(status_code=400, detail="Invalid session slug")
    return slug


async def get_session(slug: str) -> dict:
    slug = validate_slug(slug)
    db = get_db()
    session = await db.sessions.find_one({"slug": slug})
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


def get_gridfs() -> AsyncIOMotorGridFSBucket:
    """Return a GridFS bucket backed by the application database."""
    return AsyncIOMotorGridFSBucket(get_db())
