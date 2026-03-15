"""Asset-based models for images, contours, and snapshots."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from api.models.shared import ContourSettings, AnimationSettings


# ---------------------------------------------------------------------------
# Image assets
# ---------------------------------------------------------------------------


class ImageAssetResponse(BaseModel):
    image_slug: str
    sha256: str
    original_name: str
    content_type: str
    bytes: int
    created_at: datetime
    last_accessed_at: datetime


# ---------------------------------------------------------------------------
# Contour assets
# ---------------------------------------------------------------------------


class ContourAssetResponse(BaseModel):
    contour_hash: str
    image_slug: str | None = None
    source: str
    point_count: int
    bbox: dict
    image_bounds: dict | None = None
    preview_path: str = ""
    created_at: datetime
    last_accessed_at: datetime
    points: dict


# ---------------------------------------------------------------------------
# Snapshots
# ---------------------------------------------------------------------------


class SnapshotResponse(BaseModel):
    snapshot_hash: str
    image_slug: str
    contour_hash: str
    contour_settings: ContourSettings
    animation_settings: AnimationSettings
    created_at: datetime


# ---------------------------------------------------------------------------
# Requests
# ---------------------------------------------------------------------------


class ExtractContourRequest(BaseModel):
    contour_settings: ContourSettings = Field(default_factory=ContourSettings)


class SaveContourRequest(BaseModel):
    image_slug: str
    points: dict  # {"x": list[float], "y": list[float]}


class CreateSnapshotRequest(BaseModel):
    contour_hash: str
    contour_settings: ContourSettings = Field(default_factory=ContourSettings)
    animation_settings: AnimationSettings = Field(default_factory=AnimationSettings)
