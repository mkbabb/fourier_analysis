"""MongoDB session document and related models."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ContourSettings(BaseModel):
    strategy: str = "auto"
    resize: int = 512
    blur_sigma: float = 1.0
    n_harmonics: int = 200
    n_points: int = 1024
    n_classes: int = 3
    min_contour_length: int = 40


class AnimationSettings(BaseModel):
    fps: int = 30
    duration: float = 30.0
    max_circles: int = 80


class SessionCreate(BaseModel):
    pass


class SessionUpdate(BaseModel):
    parameters: ContourSettings | None = None
    animation_settings: AnimationSettings | None = None


class SessionResponse(BaseModel):
    slug: str
    created_at: datetime
    parameters: ContourSettings
    animation_settings: AnimationSettings
    has_image: bool = False
    has_results: bool = False
