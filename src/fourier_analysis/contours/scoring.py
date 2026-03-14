from __future__ import annotations

import math

from fourier_analysis.contours.image import LoadedImage
from fourier_analysis.contours.models import AlphaMode, ContourConfig


def _score_candidate(
    *,
    contour_count: int,
    total_points: int,
    retained_area_fraction: float,
    secondary_area_fraction: float,
    primary_span_fraction: float,
    envelope_border_count: int,
    weighted_compactness: float,
    max_jump: float,
    mean_jump: float,
    used_alpha: bool,
    image: LoadedImage,
    config: ContourConfig,
) -> float:
    if contour_count == 0:
        return -1e9

    # --- Rewards ---
    detail_score = min(total_points / 600.0, 6.0)
    structure_bonus = min(contour_count, 16) * 0.30
    secondary_bonus = secondary_area_fraction * 4.0
    compactness_bonus = weighted_compactness * 0.4

    # Flat reward for 10%–65% coverage, moderate falloff outside.
    if 0.10 <= retained_area_fraction <= 0.65:
        area_score = 1.0
    elif retained_area_fraction > 0.65:
        area_score = 1.0 - (retained_area_fraction - 0.65) * 2.0
    else:
        area_score = 1.0 - (0.10 - retained_area_fraction) * 3.0

    # --- Jump penalty (scaled by contour count) ---
    # More contours naturally produce more inter-contour gaps.
    diagonal = max(image.diagonal, 1.0)
    raw_jump = (max_jump / diagonal) * 2.5 + (mean_jump / diagonal) * 2.0
    jump_threshold = max(100.0, diagonal * 0.15)
    if max_jump > jump_threshold:
        raw_jump += ((max_jump - jump_threshold) / diagonal) * 6.0
    jump_penalty = raw_jump / max(1.0, math.sqrt(contour_count))

    # --- Other penalties ---
    alpha_penalty = 0.0
    portrait_detail_penalty = 0.0
    local_fragment_penalty = 0.0
    if used_alpha and image.alpha_subject_std is not None:
        alpha_penalty += max(0.0, image.alpha_subject_std - 0.10) * 10.0
        if config.alpha_mode == AlphaMode.PREFER:
            alpha_penalty -= 0.75

    if primary_span_fraction < 0.35 and retained_area_fraction < 0.12:
        local_fragment_penalty += (0.35 - primary_span_fraction) * 8.0
        local_fragment_penalty += (0.12 - retained_area_fraction) * 6.0
        if contour_count <= 3 and primary_span_fraction < 0.25:
            local_fragment_penalty += 0.7
    if primary_span_fraction < 0.55 and retained_area_fraction < 0.15:
        local_fragment_penalty += (0.55 - primary_span_fraction) * 6.0
    if retained_area_fraction < 0.22 and primary_span_fraction < 0.75:
        local_fragment_penalty += (0.22 - retained_area_fraction) * 8.0
    if primary_span_fraction < 0.55 and retained_area_fraction > 0.25:
        local_fragment_penalty += (0.55 - primary_span_fraction) * 9.0
    if envelope_border_count >= 3 and retained_area_fraction > 0.35:
        local_fragment_penalty += 0.9 * (envelope_border_count - 2)
        local_fragment_penalty += (retained_area_fraction - 0.35) * 2.8

    portrait_like = image.alpha is not None and (image.alpha_subject_std or 0.0) > 0.14
    coverage_bonus = 0.0
    if portrait_like and not used_alpha:
        structure_bonus += min(contour_count, 10) * 0.12
        secondary_bonus += secondary_area_fraction * 3.0
        if primary_span_fraction >= 0.85:
            coverage_bonus += (primary_span_fraction - 0.85) * 4.0
        if secondary_area_fraction < 0.05:
            portrait_detail_penalty += 0.5

    return (
        detail_score
        + structure_bonus
        + secondary_bonus
        + coverage_bonus
        + compactness_bonus
        + area_score
        - jump_penalty
        - alpha_penalty
        - portrait_detail_penalty
        - local_fragment_penalty
    )
