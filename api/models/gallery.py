"""Gallery and audit Pydantic models."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

GalleryTier = Literal["featured", "saved", "normal"]

# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class GalleryEntryResponse(BaseModel):
    snapshot_hash: str
    image_slug: str
    contour_hash: str
    user_slug: str | None = None
    tier: GalleryTier = "normal"
    views: int = 0
    likes: int = 0
    active_bases: list[str] = Field(default_factory=list)
    n_harmonics: int = 0
    created_at: datetime
    updated_at: datetime


class GalleryListResponse(BaseModel):
    items: list[GalleryEntryResponse]
    total: int
    page: int
    pages: int


class AdminStatsResponse(BaseModel):
    total_entries: int
    featured: int
    saved: int
    normal: int
    total_views: int
    total_likes: int
    storage_bytes: int


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------


class PublishRequest(BaseModel):
    snapshot_hash: str
    image_slug: str


class SetTierRequest(BaseModel):
    tier: GalleryTier
