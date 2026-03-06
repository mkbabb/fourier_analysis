"""Request/response models for compute endpoints."""

from __future__ import annotations

from pydantic import BaseModel


class ComputeContourRequest(BaseModel):
    strategy: str = "auto"
    resize: int = 512
    blur_sigma: float = 1.0
    n_classes: int = 3
    min_contour_length: int = 40


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
