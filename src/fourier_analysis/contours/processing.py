from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from scipy.signal import savgol_filter
from skimage import measure

from fourier_analysis.contours.geometry import _polygon_area, _deduplicate_contours, resample_arc_length
from fourier_analysis.contours.image import LoadedImage
from fourier_analysis.contours.models import ContourConfig
from fourier_analysis.shortest_tour import build_contour_tour


def _simplify_contour(
    z: NDArray[np.complex128],
    angle_threshold: float = 3.0,
) -> NDArray[np.complex128]:
    """Remove points on near-straight segments.

    Keeps points where the direction changes by more than *angle_threshold*
    degrees.  Preserves corners, eyes, sharp features while discarding
    redundant points on smooth arcs.
    """
    if len(z) < 5:
        return z
    diffs = np.diff(z)
    # Avoid division by zero for zero-length segments.
    lengths = np.abs(diffs)
    mask = lengths > 1e-12
    if np.sum(mask[:-1] & mask[1:]) < 3:
        return z

    angles = np.zeros(len(diffs) - 1)
    both = mask[:-1] & mask[1:]
    angles[both] = np.abs(np.angle(diffs[1:][both] / diffs[:-1][both]))

    threshold_rad = np.radians(angle_threshold)
    significant = angles > threshold_rad
    keep = np.concatenate([[True], significant, [True]])
    simplified = z[keep]
    # Ensure we keep at least 20 points for meaningful contours.
    if len(simplified) < 20:
        return z
    return simplified


def _find_contours_padded(
    binary: NDArray[np.bool_],
    pad: int = 1,
) -> list[NDArray[np.floating]]:
    """Pad masks so border-touching shapes produce closed contours."""
    padded = np.pad(binary, pad, mode="constant", constant_values=False)
    raw = measure.find_contours(padded.astype(float), level=0.5)
    return [rc - pad for rc in raw]


def _contours_from_masks(
    masks: tuple[NDArray[np.bool_], ...],
) -> list[NDArray[np.floating]]:
    raw_contours: list[NDArray[np.floating]] = []
    for mask in masks:
        raw_contours.extend(_find_contours_padded(mask))
    return raw_contours


def _postprocess_raw_contours(
    raw_contours: list[NDArray[np.floating]],
    image: LoadedImage,
    config: ContourConfig,
) -> tuple[list[NDArray[np.complex128]], list[float]]:
    cy, cx = image.grayscale.shape[0] / 2, image.grayscale.shape[1] / 2
    area_threshold = config.min_contour_area * image.image_area

    candidates: list[tuple[NDArray[np.complex128], float]] = []
    for rc in raw_contours:
        if len(rc) < config.min_contour_length:
            continue
        rows, cols = rc[:, 0], rc[:, 1]
        z = (cols - cx) + 1j * (cy - rows)
        area = _polygon_area(z)
        row_min, row_max = float(rows.min()), float(rows.max())
        col_min, col_max = float(cols.min()), float(cols.max())
        x_span = (col_max - col_min) / max(1.0, image.grayscale.shape[1] - 1.0)
        y_span = (row_max - row_min) / max(1.0, image.grayscale.shape[0] - 1.0)
        bbox_area = max(1.0, (row_max - row_min) * (col_max - col_min))
        bbox_fill_ratio = area / bbox_area
        frame_touching = (
            row_min <= 1.0
            and col_min <= 1.0
            and row_max >= image.grayscale.shape[0] - 2.0
            and col_max >= image.grayscale.shape[1] - 2.0
        )
        if area_threshold > 0 and area < area_threshold:
            continue
        if area > 0.92 * image.image_area:
            continue
        if (
            frame_touching
            and x_span > 0.97
            and y_span > 0.97
            and bbox_fill_ratio > 0.78
            and area > 0.45 * image.image_area
        ):
            continue

        if config.smooth_contours > 0 and len(z) >= 5:
            window = int(config.smooth_contours * len(z))
            window = max(5, window)
            if window % 2 == 0:
                window += 1
            window = min(window, len(z))
            if window % 2 == 0:
                window -= 1
            if window >= 5:
                z = (
                    savgol_filter(z.real, window, 3)
                    + 1j * savgol_filter(z.imag, window, 3)
                )

        # Downsample dense pixel-level traces to a reasonable resolution.
        perimeter = float(np.sum(np.abs(np.diff(z))))
        max_pts = max(200, min(2000, int(perimeter * 0.8)))
        if len(z) > max_pts:
            z = resample_arc_length(z, max_pts)

        # Simplify: remove points on near-straight segments.
        # Keeps corners and sharp features, discards redundant points.
        z = _simplify_contour(z, angle_threshold=2.0)

        if len(z) > 1 and abs(z[0] - z[-1]) > 1e-10:
            z = np.append(z, z[0])
        candidates.append((z, area))

    candidates.sort(key=lambda pair: pair[1], reverse=True)
    candidates = _deduplicate_contours(candidates, image)
    if config.max_contours is not None and config.max_contours > 0:
        candidates = candidates[: config.max_contours]

    return [z for z, _ in candidates], [area for _, area in candidates]


def _maybe_prune_large_jump(
    contours: list[NDArray[np.complex128]],
    image: LoadedImage,
    config: ContourConfig,
) -> tuple[list[NDArray[np.complex128]], list[float], bool]:
    if len(contours) < 2:
        return contours, [_polygon_area(contour) for contour in contours], False

    tour = build_contour_tour(contours, method=config.tour_method)
    jump_threshold = max(64.0, image.diagonal * 0.20)

    # Truncate at first gap exceeding threshold — guarantees contiguous prefix
    keep_until = len(tour.ordered_contours)
    for idx, gap in enumerate(tour.gap_lengths):
        if gap > jump_threshold:
            keep_until = idx + 1
            break

    if keep_until >= len(tour.ordered_contours):
        return contours, [_polygon_area(contour) for contour in contours], False

    pruned_contours = list(tour.ordered_contours[:keep_until])
    return pruned_contours, [_polygon_area(contour) for contour in pruned_contours], True
