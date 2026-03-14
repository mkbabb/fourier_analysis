from __future__ import annotations

from enum import Enum
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from fourier_analysis.contours.image import LoadedImage, load_image_inputs
from fourier_analysis.contours.models import (
    AlphaMode,
    ContourConfig,
    ContourDiagnostics,
    ContourExtractionResult,
    ContourStrategy,
    DEFAULT_CONTOUR_CONFIG,
)
from fourier_analysis.contours.selection import _select_auto_candidate, _select_explicit_candidate


def _enum_value(value: Enum | str) -> str:
    return value.value if isinstance(value, Enum) else value


def _coerce_config(
    config: ContourConfig | None,
    *,
    strategy: ContourStrategy | str = DEFAULT_CONTOUR_CONFIG.strategy,
    resize: int | None = DEFAULT_CONTOUR_CONFIG.resize,
    min_contour_length: int = DEFAULT_CONTOUR_CONFIG.min_contour_length,
    blur_sigma: float = DEFAULT_CONTOUR_CONFIG.blur_sigma,
    canny_sigma: float = DEFAULT_CONTOUR_CONFIG.canny_sigma,
    closing_radius: int = DEFAULT_CONTOUR_CONFIG.closing_radius,
    n_classes: int = DEFAULT_CONTOUR_CONFIG.n_classes,
    min_contour_area: float = DEFAULT_CONTOUR_CONFIG.min_contour_area,
    max_contours: int | None = DEFAULT_CONTOUR_CONFIG.max_contours,
    smooth_contours: float = DEFAULT_CONTOUR_CONFIG.smooth_contours,
    contrast_enhance: bool = DEFAULT_CONTOUR_CONFIG.contrast_enhance,
    canny_low: float | None = DEFAULT_CONTOUR_CONFIG.canny_low,
    canny_high: float | None = DEFAULT_CONTOUR_CONFIG.canny_high,
    alpha_mode: AlphaMode | str = DEFAULT_CONTOUR_CONFIG.alpha_mode,
    ml_threshold: float = DEFAULT_CONTOUR_CONFIG.ml_threshold,
    ml_detail_threshold: float = DEFAULT_CONTOUR_CONFIG.ml_detail_threshold,
) -> ContourConfig:
    if config is not None:
        return config.normalized()

    return ContourConfig(
        strategy=strategy,
        resize=resize,
        min_contour_length=min_contour_length,
        blur_sigma=blur_sigma,
        canny_sigma=canny_sigma,
        closing_radius=closing_radius,
        n_classes=n_classes,
        min_contour_area=min_contour_area,
        max_contours=max_contours,
        smooth_contours=smooth_contours,
        contrast_enhance=contrast_enhance,
        canny_low=canny_low,
        canny_high=canny_high,
        alpha_mode=alpha_mode,
        ml_threshold=ml_threshold,
        ml_detail_threshold=ml_detail_threshold,
    ).normalized()


def extract_contours_result(
    image_path: str | Path,
    *,
    config: ContourConfig | None = None,
    strategy: ContourStrategy | str = DEFAULT_CONTOUR_CONFIG.strategy,
    resize: int | None = DEFAULT_CONTOUR_CONFIG.resize,
    min_contour_length: int = DEFAULT_CONTOUR_CONFIG.min_contour_length,
    blur_sigma: float = DEFAULT_CONTOUR_CONFIG.blur_sigma,
    canny_sigma: float = DEFAULT_CONTOUR_CONFIG.canny_sigma,
    closing_radius: int = DEFAULT_CONTOUR_CONFIG.closing_radius,
    n_classes: int = DEFAULT_CONTOUR_CONFIG.n_classes,
    min_contour_area: float = DEFAULT_CONTOUR_CONFIG.min_contour_area,
    max_contours: int | None = DEFAULT_CONTOUR_CONFIG.max_contours,
    smooth_contours: float = DEFAULT_CONTOUR_CONFIG.smooth_contours,
    contrast_enhance: bool = DEFAULT_CONTOUR_CONFIG.contrast_enhance,
    canny_low: float | None = DEFAULT_CONTOUR_CONFIG.canny_low,
    canny_high: float | None = DEFAULT_CONTOUR_CONFIG.canny_high,
    alpha_mode: AlphaMode | str = DEFAULT_CONTOUR_CONFIG.alpha_mode,
    ml_threshold: float = DEFAULT_CONTOUR_CONFIG.ml_threshold,
    ml_detail_threshold: float = DEFAULT_CONTOUR_CONFIG.ml_detail_threshold,
) -> ContourExtractionResult:
    """Extract contours plus ordered-path diagnostics."""
    contour_config = _coerce_config(
        config,
        strategy=strategy,
        resize=resize,
        min_contour_length=min_contour_length,
        blur_sigma=blur_sigma,
        canny_sigma=canny_sigma,
        closing_radius=closing_radius,
        n_classes=n_classes,
        min_contour_area=min_contour_area,
        max_contours=max_contours,
        smooth_contours=smooth_contours,
        contrast_enhance=contrast_enhance,
        canny_low=canny_low,
        canny_high=canny_high,
        alpha_mode=alpha_mode,
        ml_threshold=ml_threshold,
        ml_detail_threshold=ml_detail_threshold,
    )
    image = load_image_inputs(image_path, contour_config)

    if contour_config.strategy == ContourStrategy.AUTO:
        selected, candidate_diags, notes = _select_auto_candidate(image, contour_config)
    else:
        selected, candidate_diags, notes = _select_explicit_candidate(image, contour_config)

    if selected is None:
        diagnostics = ContourDiagnostics(
            requested_strategy=_enum_value(contour_config.strategy),
            selected_strategy="none",
            selected_candidate="none",
            alpha_mode=_enum_value(contour_config.alpha_mode),
            used_alpha=False,
            contour_count=0,
            total_points=0,
            retained_area_fraction=0.0,
            secondary_area_fraction=0.0,
            primary_span_fraction=0.0,
            max_jump=0.0,
            mean_jump=0.0,
            score=-1e9,
            notes=notes,
            candidates=candidate_diags,
        )
        return ContourExtractionResult(
            config=contour_config,
            contours=[],
            ordered_path=np.array([], dtype=np.complex128),
            diagnostics=diagnostics,
        )

    diagnostics = ContourDiagnostics(
        requested_strategy=_enum_value(contour_config.strategy),
        selected_strategy=selected.strategy,
        selected_candidate=selected.label,
        alpha_mode=_enum_value(contour_config.alpha_mode),
        used_alpha=selected.used_alpha,
        contour_count=selected.diagnostics.contour_count,
        total_points=selected.diagnostics.total_points,
        retained_area_fraction=min(1.0, selected.diagnostics.retained_area_fraction),
        secondary_area_fraction=selected.diagnostics.secondary_area_fraction,
        primary_span_fraction=selected.diagnostics.primary_span_fraction,
        max_jump=selected.diagnostics.max_jump,
        mean_jump=selected.diagnostics.mean_jump,
        score=selected.diagnostics.score,
        notes=notes,
        candidates=candidate_diags,
    )
    return ContourExtractionResult(
        config=contour_config,
        contours=list(selected.contours),
        ordered_path=selected.tour.path.copy(),
        diagnostics=diagnostics,
    )


def extract_contours(
    image_path: str | Path,
    *,
    config: ContourConfig | None = None,
    strategy: ContourStrategy | str = DEFAULT_CONTOUR_CONFIG.strategy,
    resize: int | None = DEFAULT_CONTOUR_CONFIG.resize,
    min_contour_length: int = DEFAULT_CONTOUR_CONFIG.min_contour_length,
    blur_sigma: float = DEFAULT_CONTOUR_CONFIG.blur_sigma,
    canny_sigma: float = DEFAULT_CONTOUR_CONFIG.canny_sigma,
    closing_radius: int = DEFAULT_CONTOUR_CONFIG.closing_radius,
    n_classes: int = DEFAULT_CONTOUR_CONFIG.n_classes,
    min_contour_area: float = DEFAULT_CONTOUR_CONFIG.min_contour_area,
    max_contours: int | None = DEFAULT_CONTOUR_CONFIG.max_contours,
    smooth_contours: float = DEFAULT_CONTOUR_CONFIG.smooth_contours,
    contrast_enhance: bool = DEFAULT_CONTOUR_CONFIG.contrast_enhance,
    canny_low: float | None = DEFAULT_CONTOUR_CONFIG.canny_low,
    canny_high: float | None = DEFAULT_CONTOUR_CONFIG.canny_high,
    alpha_mode: AlphaMode | str = DEFAULT_CONTOUR_CONFIG.alpha_mode,
    ml_threshold: float = DEFAULT_CONTOUR_CONFIG.ml_threshold,
    ml_detail_threshold: float = DEFAULT_CONTOUR_CONFIG.ml_detail_threshold,
) -> list[NDArray[np.complex128]]:
    """Extract contours and return only the selected contour list."""
    return extract_contours_result(
        image_path,
        config=config,
        strategy=strategy,
        resize=resize,
        min_contour_length=min_contour_length,
        blur_sigma=blur_sigma,
        canny_sigma=canny_sigma,
        closing_radius=closing_radius,
        n_classes=n_classes,
        min_contour_area=min_contour_area,
        max_contours=max_contours,
        smooth_contours=smooth_contours,
        contrast_enhance=contrast_enhance,
        canny_low=canny_low,
        canny_high=canny_high,
        alpha_mode=alpha_mode,
        ml_threshold=ml_threshold,
        ml_detail_threshold=ml_detail_threshold,
    ).contours
