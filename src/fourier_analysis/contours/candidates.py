from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from fourier_analysis.contours.geometry import _polygon_area, _compactness, _contours_are_near_duplicates
from fourier_analysis.contours.image import LoadedImage
from fourier_analysis.contours.masks import mask_area_metrics
from fourier_analysis.contours.models import ContourCandidateDiagnostics, ContourConfig
from fourier_analysis.contours.processing import _contours_from_masks, _maybe_prune_large_jump, _postprocess_raw_contours
from fourier_analysis.contours.scoring import _score_candidate
from fourier_analysis.shortest_tour import ContourTour, build_contour_tour


@dataclass(frozen=True)
class _ContourCandidate:
    label: str
    strategy: str
    used_alpha: bool
    contours: tuple[NDArray[np.complex128], ...]
    areas: tuple[float, ...]
    tour: ContourTour
    diagnostics: ContourCandidateDiagnostics


def _build_candidate_from_processed(
    *,
    label: str,
    strategy: str,
    contours: list[NDArray[np.complex128]],
    areas: list[float],
    used_alpha: bool,
    image: LoadedImage,
    config: ContourConfig,
    pruned_large_jump: bool = False,
    nested_hybrid: bool = False,
    mask_retained_area_fraction: float | None = None,
    mask_secondary_area_fraction: float | None = None,
) -> _ContourCandidate:
    tour = build_contour_tour(contours, method=config.tour_method)
    contour_count = len(contours)
    total_points = int(sum(len(contour) for contour in contours))
    raw_total_area = float(sum(areas))
    total_area = raw_total_area
    retained_area_fraction = total_area / image.image_area if image.image_area > 0 else 0.0
    secondary_area_fraction = (
        float(sum(areas[1:])) / total_area if total_area > 0 and len(areas) > 1 else 0.0
    )
    if nested_hybrid and areas:
        outer_area = float(areas[0])
        secondary_area = min(float(sum(areas[1:])), outer_area * 0.5)
        total_area = min(image.image_area, outer_area + secondary_area)
        retained_area_fraction = total_area / image.image_area if image.image_area > 0 else 0.0
        secondary_area_fraction = secondary_area / total_area if total_area > 0 else 0.0
    if mask_retained_area_fraction is not None:
        retained_area_fraction = min(1.0, mask_retained_area_fraction)
    if mask_secondary_area_fraction is not None and contour_count > 1:
        secondary_area_fraction = max(secondary_area_fraction, mask_secondary_area_fraction)
    primary_span_fraction = 0.0
    if contours:
        span_fractions = []
        for contour in contours:
            x_span = float(contour.real.max() - contour.real.min()) / max(1.0, image.grayscale.shape[1])
            y_span = float(contour.imag.max() - contour.imag.min()) / max(1.0, image.grayscale.shape[0])
            span_fractions.append(min(1.0, max(0.0, min(x_span, y_span))))
        primary_span_fraction = max(span_fractions, default=0.0)
    envelope_border_count = 0
    if contours:
        widest_contour = max(
            contours,
            key=lambda contour: min(
                float(contour.real.max() - contour.real.min()) / max(1.0, image.grayscale.shape[1]),
                float(contour.imag.max() - contour.imag.min()) / max(1.0, image.grayscale.shape[0]),
            ),
        )
        cy, cx = image.grayscale.shape[0] / 2, image.grayscale.shape[1] / 2
        row_min = cy - float(widest_contour.imag.max())
        row_max = cy - float(widest_contour.imag.min())
        col_min = float(widest_contour.real.min()) + cx
        col_max = float(widest_contour.real.max()) + cx
        envelope_border_count = sum(
            [
                row_min <= 1.0,
                row_max >= image.grayscale.shape[0] - 2.0,
                col_min <= 1.0,
                col_max >= image.grayscale.shape[1] - 2.0,
            ]
        )

    compactness_area = total_area if nested_hybrid else raw_total_area
    if mask_retained_area_fraction is not None:
        compactness_area = max(compactness_area, image.image_area * mask_retained_area_fraction)
    if compactness_area > 0:
        weighted_compactness = float(
            sum(area * _compactness(contour, area) for contour, area in zip(contours, areas))
            / compactness_area
        )
    else:
        weighted_compactness = 0.0

    gap_lengths = np.array(tour.gap_lengths, dtype=np.float64)
    max_jump = float(gap_lengths.max()) if gap_lengths.size else 0.0
    mean_jump = float(gap_lengths.mean()) if gap_lengths.size else 0.0

    score = _score_candidate(
        contour_count=contour_count,
        total_points=total_points,
        retained_area_fraction=retained_area_fraction,
        secondary_area_fraction=secondary_area_fraction,
        primary_span_fraction=primary_span_fraction,
        envelope_border_count=envelope_border_count,
        weighted_compactness=weighted_compactness,
        max_jump=max_jump,
        mean_jump=mean_jump,
        used_alpha=used_alpha,
        image=image,
        config=config,
    )

    diagnostics = ContourCandidateDiagnostics(
        candidate=label,
        strategy=strategy,
        used_alpha=used_alpha,
        contour_count=contour_count,
        total_points=total_points,
        retained_area_fraction=retained_area_fraction,
        secondary_area_fraction=secondary_area_fraction,
        primary_span_fraction=primary_span_fraction,
        weighted_compactness=weighted_compactness,
        max_jump=max_jump,
        mean_jump=mean_jump,
        score=score,
        pruned_large_jump=pruned_large_jump,
    )
    return _ContourCandidate(
        label=label,
        strategy=strategy,
        used_alpha=used_alpha,
        contours=tuple(contours),
        areas=tuple(areas),
        tour=tour,
        diagnostics=diagnostics,
    )


def _build_candidate(
    *,
    label: str,
    strategy: str,
    raw_contours: list[NDArray[np.floating]],
    used_alpha: bool,
    image: LoadedImage,
    config: ContourConfig,
    allow_jump_pruning: bool,
) -> _ContourCandidate:
    contours, areas = _postprocess_raw_contours(raw_contours, image, config)
    pruned_large_jump = False

    if allow_jump_pruning and contours:
        contours, areas, pruned_large_jump = _maybe_prune_large_jump(contours, image, config)

    return _build_candidate_from_processed(
        label=label,
        strategy=strategy,
        contours=contours,
        areas=areas,
        used_alpha=used_alpha,
        image=image,
        config=config,
        pruned_large_jump=pruned_large_jump,
    )


def _build_candidate_from_masks(
    *,
    label: str,
    strategy: str,
    masks: tuple[NDArray[np.bool_], ...],
    used_alpha: bool,
    image: LoadedImage,
    config: ContourConfig,
    allow_jump_pruning: bool,
) -> _ContourCandidate:
    raw_contours = _contours_from_masks(masks)
    contours, areas = _postprocess_raw_contours(raw_contours, image, config)
    pruned_large_jump = False

    if allow_jump_pruning and contours:
        contours, areas, pruned_large_jump = _maybe_prune_large_jump(contours, image, config)

    retained_area_fraction, secondary_area_fraction = mask_area_metrics(masks, image.image_area)
    return _build_candidate_from_processed(
        label=label,
        strategy=strategy,
        contours=contours,
        areas=areas,
        used_alpha=used_alpha,
        image=image,
        config=config,
        pruned_large_jump=pruned_large_jump,
        mask_retained_area_fraction=retained_area_fraction,
        mask_secondary_area_fraction=secondary_area_fraction,
    )


def _detail_hybrid_candidate(
    *,
    alpha_candidate: _ContourCandidate,
    detail_candidate: _ContourCandidate,
    image: LoadedImage,
    config: ContourConfig,
) -> _ContourCandidate | None:
    if not alpha_candidate.contours:
        return None

    return _hybridize_envelope_candidate(
        label=f"alpha_envelope_{detail_candidate.label}",
        strategy=detail_candidate.strategy,
        envelope_contour=alpha_candidate.contours[0],
        envelope_area=float(alpha_candidate.areas[0]),
        detail_candidate=detail_candidate,
        image=image,
        config=config,
        nested_hybrid=True,
    )


def _hybridize_envelope_candidate(
    *,
    label: str,
    strategy: str,
    envelope_contour: NDArray[np.complex128],
    envelope_area: float,
    detail_candidate: _ContourCandidate,
    image: LoadedImage,
    config: ContourConfig,
    nested_hybrid: bool,
) -> _ContourCandidate | None:
    if not detail_candidate.contours:
        return None

    total_detail_area = float(sum(detail_candidate.areas)) or 1.0
    hybrid_contours = [envelope_contour]
    hybrid_areas = [envelope_area]

    for contour, area in zip(detail_candidate.contours, detail_candidate.areas):
        if _contours_are_near_duplicates(contour, float(area), envelope_contour, envelope_area, image):
            continue
        x_span = float(contour.real.max() - contour.real.min()) / max(1.0, image.grayscale.shape[1])
        y_span = float(contour.imag.max() - contour.imag.min()) / max(1.0, image.grayscale.shape[0])
        span = min(1.0, max(0.0, min(x_span, y_span)))
        area_share = float(area) / total_detail_area
        if span >= 0.92 and area_share > 0.60:
            continue
        hybrid_contours.append(contour)
        hybrid_areas.append(float(area))

    if len(hybrid_contours) == 1:
        return None

    hybrid = _build_candidate_from_processed(
        label=label,
        strategy=strategy,
        contours=hybrid_contours,
        areas=hybrid_areas,
        used_alpha=False,
        image=image,
        config=config,
        pruned_large_jump=detail_candidate.diagnostics.pruned_large_jump,
        nested_hybrid=nested_hybrid,
    )
    if hybrid.diagnostics.max_jump > max(150.0, image.diagonal * 0.22):
        return None
    if hybrid.diagnostics.secondary_area_fraction < detail_candidate.diagnostics.secondary_area_fraction * 0.35:
        return None
    return hybrid
