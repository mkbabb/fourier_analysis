"""Stage 3: Edge feature contours for facial/detail features."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from skimage import feature, filters, measure, morphology

from fourier_analysis.contours.geometry import (
    _compactness,
    _contours_are_near_duplicates,
    _polygon_area,
)
from fourier_analysis.contours.image import LoadedImage
from fourier_analysis.contours.isolation import SubjectIsolation
from fourier_analysis.contours.models import ContourConfig
from fourier_analysis.contours.processing import _postprocess_raw_contours


def extract_feature_contours(
    image: LoadedImage,
    isolation: SubjectIsolation,
    structure_contours: list[tuple[NDArray[np.complex128], float]],
    budget: int,
    config: ContourConfig,
) -> list[tuple[NDArray[np.complex128], float]]:
    """Extract edge-density contours that trace facial features.

    Builds a density field from max(gaussian(color_gradient), gaussian(canny)),
    extracts iso-contours at 9 levels, filters to feature-scale band,
    deduplicates against structure contours, sorts by compactness,
    enforces spatial diversity, and returns up to *budget* contours.
    """
    # Build density field: color gradient + Canny edges.
    color_grad = image.color_gradient
    gray_edges = feature.canny(image.detail_grayscale, sigma=0.8)
    density = filters.gaussian(color_grad, sigma=1.5)
    canny_density = filters.gaussian(gray_edges.astype(np.float64), sigma=2.0)
    density = np.maximum(density, canny_density)

    # Normalize to [0, 1].
    d_max = float(density.max())
    if d_max > 0:
        density = density / d_max

    # Extract contours at multiple density levels.
    levels = [0.06, 0.10, 0.15, 0.22, 0.30, 0.40, 0.52, 0.65, 0.78]

    min_length = max(config.min_contour_length, 60)
    min_bbox_area = image.image_area * 0.0005
    # Feature-scale band: too small is noise, too large repeats silhouette.
    min_feature_area = image.image_area * 0.0003
    # Cap at 40% of silhouette area (if known) to allow large features
    # like mouths and eyes while excluding near-silhouette duplicates.
    if isolation.silhouette_area > 0:
        max_feature_area = isolation.silhouette_area * 0.40
    else:
        max_feature_area = image.image_area * 0.15

    raw_contours: list[NDArray[np.floating]] = []
    for level in levels:
        contours = measure.find_contours(density, level=level)
        for c in contours:
            if len(c) < min_length:
                continue
            # Filter by bbox area.
            rows, cols = c[:, 0], c[:, 1]
            bbox_area = (rows.max() - rows.min()) * (cols.max() - cols.min())
            if bbox_area < min_bbox_area:
                continue
            # Filter by subject overlap.
            if isolation.subject_mask is not None:
                r = np.clip(c[:, 0].astype(int), 0, isolation.subject_mask.shape[0] - 1)
                cl = np.clip(c[:, 1].astype(int), 0, isolation.subject_mask.shape[1] - 1)
                if np.mean(isolation.subject_mask[r, cl]) <= 0.5:
                    continue
            raw_contours.append(c)

    # Postprocess: convert to complex, smooth, resample, simplify, dedup.
    # Use uncapped max_contours so small features survive.
    from dataclasses import replace as _replace
    uncapped_config = _replace(config, max_contours=None)
    processed, areas = _postprocess_raw_contours(raw_contours, image, uncapped_config)

    # Filter to feature-scale band.
    candidates: list[tuple[NDArray[np.complex128], float]] = [
        (c, a) for c, a in zip(processed, areas)
        if min_feature_area <= a <= max_feature_area
    ]

    # Merge in region-based feature candidates (dark/light patches).
    region_candidates = _extract_region_features(image, isolation, config)
    for rc, ra in region_candidates:
        # Dedup region candidates against edge candidates.
        is_dup = any(
            _contours_are_near_duplicates(rc, ra, ec, ea, image)
            for ec, ea in candidates
        )
        if not is_dup:
            candidates.append((rc, ra))

    # Deduplicate against structure contours.
    if structure_contours:
        deduped: list[tuple[NDArray[np.complex128], float]] = []
        for c, a in candidates:
            is_dup = any(
                _contours_are_near_duplicates(c, a, sc, sa, image)
                for sc, sa in structure_contours
            )
            if not is_dup:
                deduped.append((c, a))
        candidates = deduped

    # Sort by compactness × proximity to subject center.
    # Features near the subject centroid (face area) rank higher than
    # peripheral features (background objects, ground).
    if isolation.silhouette is not None and isolation.silhouette_area > 0:
        ref_center = complex(
            float(isolation.silhouette.real.mean()),
            float(isolation.silhouette.imag.mean()),
        )
        subject_radius = max(1.0, (isolation.silhouette_area / np.pi) ** 0.5)
    else:
        ref_center = 0j
        subject_radius = image.diagonal * 0.5

    def _compactness_key(pair: tuple[NDArray[np.complex128], float]) -> float:
        contour, area = pair
        comp = _compactness(contour, area)
        center = complex(float(contour.real.mean()), float(contour.imag.mean()))
        dist = abs(center - ref_center)
        proximity = max(0.5, 1.0 - 0.5 * (dist / subject_radius))
        return comp * proximity

    candidates.sort(key=_compactness_key, reverse=True)

    # Enforce spatial diversity: min 4% diagonal between picked features.
    min_spacing = image.diagonal * 0.04
    picked: list[tuple[NDArray[np.complex128], float]] = []
    picked_centers: list[complex] = []

    for c, a in candidates:
        if len(picked) >= budget:
            break
        center = complex(float(c.real.mean()), float(c.imag.mean()))
        if any(abs(center - pc) < min_spacing for pc in picked_centers):
            continue
        picked.append((c, a))
        picked_centers.append(center)

    return picked


def _extract_region_features(
    image: LoadedImage,
    isolation: SubjectIsolation,
    config: ContourConfig,
) -> list[tuple[NDArray[np.complex128], float]]:
    """Find dark/light patches within the subject that deviate from the subject median.

    Detects filled regions (eyes, mouths) as connected components where pixel
    intensity deviates from the subject median by >= 1 std. Morphological
    opening removes noise fragments from textured subjects.
    """
    source = image.detail_grayscale
    if isolation.subject_mask is None or not np.any(isolation.subject_mask):
        return []

    subject_pixels = source[isolation.subject_mask]
    median = float(np.median(subject_pixels))
    std = float(np.std(subject_pixels))
    if std < 1e-6:
        return []

    # Dark and light masks within the subject.
    dark_mask = (source < median - std) & isolation.subject_mask
    light_mask = (source > median + std) & isolation.subject_mask

    # Morphological cleanup: remove noise fragments.
    selem = morphology.disk(2)
    dark_mask = morphology.opening(dark_mask, selem)
    light_mask = morphology.opening(light_mask, selem)

    # Feature-scale bounds.
    min_feature_area = image.image_area * 0.0003
    if isolation.silhouette_area > 0:
        max_feature_area = isolation.silhouette_area * 0.40
    else:
        max_feature_area = image.image_area * 0.15

    min_length = max(config.min_contour_length, 60)

    raw_contours: list[NDArray[np.floating]] = []
    for mask in (dark_mask, light_mask):
        # Find contours on the binary mask at 0.5 level.
        contours = measure.find_contours(mask.astype(np.float64), level=0.5)
        for c in contours:
            if len(c) < min_length:
                continue
            raw_contours.append(c)

    if not raw_contours:
        return []

    # Postprocess: convert to complex, smooth, resample, simplify, dedup.
    from dataclasses import replace as _replace
    uncapped_config = _replace(config, max_contours=None)
    processed, areas = _postprocess_raw_contours(raw_contours, image, uncapped_config)

    # Filter to feature-scale band.
    candidates: list[tuple[NDArray[np.complex128], float]] = [
        (c, a) for c, a in zip(processed, areas)
        if min_feature_area <= a <= max_feature_area
    ]

    return candidates
