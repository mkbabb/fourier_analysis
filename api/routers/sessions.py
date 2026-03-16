"""Session management: register, login, logout, and current-user info."""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request

from api.config import settings
from api.dependencies import get_client_ip, hash_ip, require_session, resolve_session
from api.services.database import get_db
from api.services.rate_limiter import login_limiter, write_limiter
from api.slugs import generate_slug

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


def _make_session_doc(user_slug: str, ip_hash: str) -> dict:
    """Build a new session document."""
    now = datetime.now(UTC)
    return {
        "_id": str(uuid.uuid4()),
        "user_slug": user_slug,
        "ip_hash": ip_hash,
        "created_at": now,
        "last_seen_at": now,
        "expires_at": now + timedelta(days=settings.session_ttl_days),
    }


@router.post("")
async def register(request: Request):
    """Create a new anonymous user and session."""
    client_ip = get_client_ip(request)
    ip_hashed = hash_ip(client_ip)
    write_limiter.check(ip_hashed)

    db = get_db()
    slug = generate_slug()
    now = datetime.now(UTC)

    await db.users.insert_one(
        {"_id": slug, "created_at": now, "last_seen_at": now},
    )

    session_doc = _make_session_doc(slug, ip_hashed)
    await db.sessions.insert_one(session_doc)

    return {"token": session_doc["_id"], "user_slug": slug}


@router.post("/login")
async def login(request: Request):
    """Login by slug — creates a new session for an existing user."""
    client_ip = get_client_ip(request)
    ip_hashed = hash_ip(client_ip)
    login_limiter.check(ip_hashed)

    body = await request.json()
    slug = (body.get("slug") or "").strip().lower()

    if not slug:
        await asyncio.sleep(0.2)
        raise HTTPException(status_code=400, detail="Slug required")

    db = get_db()
    user = await db.users.find_one({"_id": slug})

    # Constant delay on ALL paths (timing attack mitigation)
    await asyncio.sleep(0.2)

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    session_doc = _make_session_doc(slug, ip_hashed)
    await db.sessions.insert_one(session_doc)
    return {"token": session_doc["_id"], "user_slug": slug}


@router.get("/me")
async def me(user_slug: str = Depends(require_session)):
    """Return current user info."""
    db = get_db()
    user = await db.users.find_one({"_id": user_slug})
    return {"user_slug": user_slug, "created_at": user["created_at"]}


@router.delete("")
async def logout(request: Request):
    """Delete the current session."""
    token = request.headers.get("X-Session-Token")
    if token:
        db = get_db()
        await db.sessions.delete_one({"_id": token})
    return {"ok": True}
