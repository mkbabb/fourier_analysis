"""Request/response models for compute endpoints."""

from __future__ import annotations

from pydantic import BaseModel, field_validator


class ComputeContourRequest(BaseModel):
    strategy: str = "auto"
    resize: int = 512
    blur_sigma: float = 1.0
    n_classes: int = 3
    min_contour_length: int = 40
    min_contour_area: float = 0.001
    max_contours: int | None = 12
    smooth_contours: float = 0.0
    ml_threshold: float = 0.5
    ml_detail_threshold: float = 0.3

    @field_validator("blur_sigma", mode="before")
    @classmethod
    def _clamp_blur(cls, v: float) -> float:
        return max(0.0, float(v))

    @field_validator("min_contour_area", mode="before")
    @classmethod
    def _clamp_area(cls, v: float) -> float:
        return max(0.0, min(1.0, float(v)))

    @field_validator("smooth_contours", mode="before")
    @classmethod
    def _clamp_smooth(cls, v: float) -> float:
        return max(0.0, min(1.0, float(v)))

    @field_validator("max_contours", mode="before")
    @classmethod
    def _clamp_max_contours(cls, v: int | None) -> int | None:
        if v is None or v <= 0:
            return None
        return int(v)


class ComputeEpicyclesRequest(BaseModel):
    n_harmonics: int = 200
    n_points: int = 1024


class ComputeBasesRequest(BaseModel):
    max_degree: int = 200
    n_points: int = 1024
    levels: list[int] | None = None
    n_eval: int = 1000


class EpicycleComponentDTO(BaseModel):
    frequency: int
    coefficient_re: float
    coefficient_im: float
    amplitude: float
    phase: float


class ComputeResult(BaseModel):
    status: str = "ok"
    data: dict
