"""Stage 2: Iso-intensity contours for overall subject structure."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from skimage import measure

from fourier_analysis.contours.geometry import _bbox_iou, _contour_bbox
from fourier_analysis.contours.image import LoadedImage
from fourier_analysis.contours.isolation import SubjectIsolation
from fourier_analysis.contours.models import ContourConfig
from fourier_analysis.contours.processing import _postprocess_raw_contours


def extract_structure_contours(
    image: LoadedImage,
    isolation: SubjectIsolation,
    budget: int,
    config: ContourConfig,
) -> list[tuple[NDArray[np.complex128], float]]:
    """Extract iso-intensity contours within the subject region.

    Computes 16 quantile thresholds from subject pixels on detail_grayscale,
    extracts contours at each level via marching squares, filters by subject
    overlap (>50% of contour points inside mask), deduplicates, and returns
    up to *budget* contours sorted by area descending.
    """
    source = image.detail_grayscale
    n_levels = 16
    percentiles = np.linspace(5, 95, n_levels)

    # Focus quantile levels on subject pixels if we have a mask.
    if isolation.subject_mask is not None and np.any(isolation.subject_mask):
        subject_pixels = source[isolation.subject_mask]
        levels = np.percentile(subject_pixels, percentiles)
    else:
        levels = np.percentile(source, percentiles)

    # Deduplicate near-identical thresholds.
    levels = sorted(set(round(float(v), 4) for v in levels))

    min_length = config.min_contour_length
    min_area = config.min_contour_area * image.image_area

    raw_contours: list[NDArray[np.floating]] = []
    for level in levels:
        contours = measure.find_contours(source, level=level)
        for c in contours:
            if len(c) < min_length:
                continue
            # Filter by subject overlap: >70% of contour points inside mask.
            # Stricter than 50% to prevent background leakage where
            # iso-contours extend through background areas of similar intensity.
            if isolation.subject_mask is not None:
                rows = np.clip(c[:, 0].astype(int), 0, isolation.subject_mask.shape[0] - 1)
                cols = np.clip(c[:, 1].astype(int), 0, isolation.subject_mask.shape[1] - 1)
                if np.mean(isolation.subject_mask[rows, cols]) <= 0.7:
                    continue
            raw_contours.append(c)

    # Postprocess: convert to complex, smooth, resample, simplify, dedup.
    processed, areas = _postprocess_raw_contours(raw_contours, image, config)

    # Filter by minimum area.
    result: list[tuple[NDArray[np.complex128], float]] = [
        (c, a) for c, a in zip(processed, areas) if a >= min_area
    ]

    # Collapse nested near-concentric blobs (e.g. iso-levels of a uniform body).
    result = _deduplicate_nested(result)

    # Already sorted by area descending from _postprocess_raw_contours.
    return result[:budget]


def _deduplicate_nested(
    contours: list[tuple[NDArray[np.complex128], float]],
) -> list[tuple[NDArray[np.complex128], float]]:
    """Remove redundant structure contours that trace near-identical shapes.

    Two contours are redundant if they have similar area (ratio 0.65–1.55)
    and high bbox overlap (IoU >= 0.55). The kept contour is the one seen
    first (i.e. the larger, since we iterate area-descending).

    This catches iso-level duplicates: e.g. porthole rings or body blobs
    traced at adjacent intensity thresholds, which have nearly the same shape
    and position but slightly different areas.
    """
    if len(contours) <= 1:
        return contours

    # Sort by area descending so we keep the larger of any redundant pair.
    sorted_contours = sorted(contours, key=lambda p: p[1], reverse=True)
    keep: list[tuple[NDArray[np.complex128], float]] = []

    for c, a in sorted_contours:
        is_redundant = False
        c_bbox = _contour_bbox(c)

        for kc, ka in keep:
            area_ratio = a / ka if ka > 0 else 0.0
            if not (0.65 <= area_ratio <= 1.55):
                continue
            if _bbox_iou(c_bbox, _contour_bbox(kc)) >= 0.55:
                is_redundant = True
                break

        if not is_redundant:
            keep.append((c, a))

    return keep
