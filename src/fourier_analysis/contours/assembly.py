"""Stage 4: Deterministic merge of silhouette, structure, and feature contours."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from fourier_analysis.contours.geometry import _contours_are_near_duplicates
from fourier_analysis.contours.image import LoadedImage
from fourier_analysis.contours.isolation import SubjectIsolation


def assemble_contours(
    isolation: SubjectIsolation,
    structure: list[tuple[NDArray[np.complex128], float]],
    features: list[tuple[NDArray[np.complex128], float]],
    max_contours: int,
    image: LoadedImage,
) -> list[NDArray[np.complex128]]:
    """Deterministically merge silhouette, structure, and feature contours.

    1. Always prepend silhouette (ML mask boundary traces the true subject outline).
    2. Add structure contours (up to half remaining budget), deduped against silhouette.
    3. Add feature contours (remaining budget).
    4. If either pool underflows, surplus goes to the other.
    5. Spatial outlier pruning using silhouette bbox + 25% margin.
    """
    merged: list[tuple[NDArray[np.complex128], float]] = []

    # Always include silhouette — it traces the actual subject boundary
    # (including thin features like sun rays, giraffe legs, etc.) that
    # iso-intensity structure contours may smooth over.
    if isolation.silhouette is not None:
        merged.append((isolation.silhouette, isolation.silhouette_area))

    # Proportional budget split based on actual yield from each stage.
    # When structure yields many contours, split is ~even.
    # When structure yields few (e.g. post-dedup uniform subjects), features get more.
    remaining = max_contours - len(merged)
    total_available = len(structure) + len(features)
    if total_available > 0:
        structure_budget = max(1, round(remaining * len(structure) / total_available))
        feature_budget = remaining - structure_budget
    else:
        structure_budget = remaining // 2
        feature_budget = remaining - structure_budget

    # Add structure contours, deduplicating against silhouette.
    structure_added = 0
    for c, a in structure:
        if structure_added >= structure_budget:
            break
        is_dup = any(
            _contours_are_near_duplicates(c, a, mc, ma, image)
            for mc, ma in merged
        )
        if not is_dup:
            merged.append((c, a))
            structure_added += 1

    # Surplus from structure underflow goes to features.
    feature_budget += max(0, structure_budget - structure_added)

    # Add feature contours.
    feature_added = 0
    for c, a in features:
        if feature_added >= feature_budget:
            break
        is_dup = any(
            _contours_are_near_duplicates(c, a, mc, ma, image)
            for mc, ma in merged
        )
        if not is_dup:
            merged.append((c, a))
            feature_added += 1

    # Surplus from feature underflow goes back to structure.
    extra_structure = max(0, feature_budget - feature_added)
    if extra_structure > 0 and structure_added < len(structure):
        for c, a in structure[structure_added:]:
            if extra_structure <= 0:
                break
            is_dup = any(
                _contours_are_near_duplicates(c, a, mc, ma, image)
                for mc, ma in merged
            )
            if not is_dup:
                merged.append((c, a))
                extra_structure -= 1

    # Spatial outlier pruning using silhouette bbox if available.
    merged = _prune_spatial_outliers(merged, isolation)

    return [c for c, _ in merged]


def _prune_spatial_outliers(
    contours: list[tuple[NDArray[np.complex128], float]],
    isolation: SubjectIsolation,
) -> list[tuple[NDArray[np.complex128], float]]:
    """Remove contours whose centroid falls outside the reference bbox + 25% margin.

    Uses the union of silhouette bbox and top-3 contour bboxes.  This is robust
    when the silhouette only covers part of the subject (e.g. ML saliency
    underestimates extent) — the top-3 structure contours expand the reference.
    """
    if len(contours) <= 3:
        return contours

    # Start with top-3 contour bboxes (by area, which is how they're sorted).
    n_ref = min(3, len(contours))
    re_min = min(float(c.real.min()) for c, _ in contours[:n_ref])
    re_max = max(float(c.real.max()) for c, _ in contours[:n_ref])
    im_min = min(float(c.imag.min()) for c, _ in contours[:n_ref])
    im_max = max(float(c.imag.max()) for c, _ in contours[:n_ref])

    # Expand with silhouette bbox if available.
    if isolation.silhouette is not None:
        s = isolation.silhouette
        re_min = min(re_min, float(s.real.min()))
        re_max = max(re_max, float(s.real.max()))
        im_min = min(im_min, float(s.imag.min()))
        im_max = max(im_max, float(s.imag.max()))

    margin_re = (re_max - re_min) * 0.25
    margin_im = (im_max - im_min) * 0.25
    bbox = (re_min - margin_re, im_min - margin_im,
            re_max + margin_re, im_max + margin_im)

    # Always keep the first contour (silhouette).
    pruned = [contours[0]]
    for c, a in contours[1:]:
        cx, cy = float(c.real.mean()), float(c.imag.mean())
        if bbox[0] <= cx <= bbox[2] and bbox[1] <= cy <= bbox[3]:
            pruned.append((c, a))

    return pruned
