"""Shared contour models and defaults."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

import numpy as np
from numpy.typing import NDArray


def _enum_value(value: Enum | str) -> str:
    return value.value if isinstance(value, Enum) else value


class ContourStrategy(Enum):
    """Strategy for contour extraction."""

    THRESHOLD = "threshold"
    ADAPTIVE_THRESHOLD = "adaptive_threshold"
    MULTI_THRESHOLD = "multi_threshold"
    CANNY = "canny"
    EDGE_AWARE = "edge_aware"
    ML = "ml"
    AUTO = "auto"


class AlphaMode(Enum):
    """How AUTO and explicit strategies should treat alpha masks."""

    AUTO = "auto"
    IGNORE = "ignore"
    PREFER = "prefer"
    ONLY = "only"


@dataclass(frozen=True)
class ContourConfig:
    """Canonical contour configuration shared across surfaces."""

    strategy: ContourStrategy | str = ContourStrategy.AUTO
    resize: int | None = 768
    blur_sigma: float = 0.5
    canny_sigma: float = 1.5
    closing_radius: int = 1
    n_classes: int = 3
    min_contour_length: int = 40
    min_contour_area: float = 0.001
    max_contours: int | None = 16
    smooth_contours: float = 0.03
    contrast_enhance: bool = True
    canny_low: float | None = None
    canny_high: float | None = None
    alpha_mode: AlphaMode | str = AlphaMode.AUTO
    tour_method: str = "nearest_2opt"
    ml_threshold: float = 0.5
    ml_detail_threshold: float = 0.3

    def normalized(self) -> ContourConfig:
        """Return a validated configuration."""
        strategy = self.strategy
        if isinstance(strategy, str):
            strategy = ContourStrategy(strategy.lower())

        alpha_mode = self.alpha_mode
        if isinstance(alpha_mode, str):
            alpha_mode = AlphaMode(alpha_mode.lower())

        resize = None
        if self.resize is not None:
            resize_int = int(self.resize)
            if resize_int > 0:
                resize = max(32, resize_int)
        max_contours = self.max_contours
        if max_contours is not None:
            max_contours = max(0, int(max_contours)) or None

        canny_low = None if self.canny_low is None else max(0.0, float(self.canny_low))
        canny_high = None if self.canny_high is None else max(0.0, float(self.canny_high))

        return ContourConfig(
            strategy=strategy,
            resize=resize,
            blur_sigma=max(0.0, float(self.blur_sigma)),
            canny_sigma=max(0.0, float(self.canny_sigma)),
            closing_radius=max(1, int(self.closing_radius)),
            n_classes=max(2, int(self.n_classes)),
            min_contour_length=max(3, int(self.min_contour_length)),
            min_contour_area=max(0.0, min(1.0, float(self.min_contour_area))),
            max_contours=max_contours,
            smooth_contours=max(0.0, min(1.0, float(self.smooth_contours))),
            contrast_enhance=bool(self.contrast_enhance),
            canny_low=canny_low,
            canny_high=canny_high,
            alpha_mode=alpha_mode,
            tour_method=self.tour_method,
            ml_threshold=max(0.0, min(1.0, float(self.ml_threshold))),
            ml_detail_threshold=max(0.0, min(1.0, float(self.ml_detail_threshold))),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to JSON-friendly primitives."""
        return {
            "strategy": _enum_value(self.strategy),
            "resize": self.resize,
            "blur_sigma": self.blur_sigma,
            "canny_sigma": self.canny_sigma,
            "closing_radius": self.closing_radius,
            "n_classes": self.n_classes,
            "min_contour_length": self.min_contour_length,
            "min_contour_area": self.min_contour_area,
            "max_contours": self.max_contours,
            "smooth_contours": self.smooth_contours,
            "contrast_enhance": self.contrast_enhance,
            "canny_low": self.canny_low,
            "canny_high": self.canny_high,
            "alpha_mode": _enum_value(self.alpha_mode),
            "tour_method": self.tour_method,
            "ml_threshold": self.ml_threshold,
            "ml_detail_threshold": self.ml_detail_threshold,
        }


DEFAULT_CONTOUR_CONFIG = ContourConfig().normalized()


@dataclass(frozen=True)
class ContourCandidateDiagnostics:
    """Diagnostics for one candidate extraction path."""

    candidate: str
    strategy: str
    used_alpha: bool
    contour_count: int
    total_points: int
    retained_area_fraction: float
    secondary_area_fraction: float
    primary_span_fraction: float
    weighted_compactness: float
    max_jump: float
    mean_jump: float
    score: float
    pruned_large_jump: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate": self.candidate,
            "strategy": self.strategy,
            "used_alpha": self.used_alpha,
            "contour_count": self.contour_count,
            "total_points": self.total_points,
            "retained_area_fraction": self.retained_area_fraction,
            "secondary_area_fraction": self.secondary_area_fraction,
            "primary_span_fraction": self.primary_span_fraction,
            "weighted_compactness": self.weighted_compactness,
            "max_jump": self.max_jump,
            "mean_jump": self.mean_jump,
            "score": self.score,
            "pruned_large_jump": self.pruned_large_jump,
        }


@dataclass(frozen=True)
class ContourDiagnostics:
    """Extraction-level diagnostics for the selected contour set."""

    requested_strategy: str
    selected_strategy: str
    selected_candidate: str
    alpha_mode: str
    used_alpha: bool
    contour_count: int
    total_points: int
    retained_area_fraction: float
    secondary_area_fraction: float
    primary_span_fraction: float
    max_jump: float
    mean_jump: float
    score: float
    notes: tuple[str, ...]
    candidates: tuple[ContourCandidateDiagnostics, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "requested_strategy": self.requested_strategy,
            "selected_strategy": self.selected_strategy,
            "selected_candidate": self.selected_candidate,
            "alpha_mode": self.alpha_mode,
            "used_alpha": self.used_alpha,
            "contour_count": self.contour_count,
            "total_points": self.total_points,
            "retained_area_fraction": self.retained_area_fraction,
            "secondary_area_fraction": self.secondary_area_fraction,
            "primary_span_fraction": self.primary_span_fraction,
            "max_jump": self.max_jump,
            "mean_jump": self.mean_jump,
            "score": self.score,
            "notes": list(self.notes),
            "candidates": [candidate.to_dict() for candidate in self.candidates],
        }


@dataclass
class ContourExtractionResult:
    """Selected contour set plus diagnostics and ordered path."""

    config: ContourConfig
    contours: list[NDArray[np.complex128]]
    ordered_path: NDArray[np.complex128]
    diagnostics: ContourDiagnostics
