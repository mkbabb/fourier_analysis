from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from scipy.interpolate import interp1d

from fourier_analysis.contours.image import LoadedImage


def _polygon_area(z: NDArray[np.complex128]) -> float:
    return float(
        0.5
        * abs(
            np.sum(
                z.real * np.roll(z.imag, -1)
                - np.roll(z.real, -1) * z.imag
            )
        )
    )


def _compactness(z: NDArray[np.complex128], area: float) -> float:
    perimeter = float(np.sum(np.abs(np.diff(z))))
    if perimeter <= 1e-12:
        return 0.0
    return float(4 * np.pi * area / (perimeter**2))


def _contour_bbox(contour: NDArray[np.complex128]) -> tuple[float, float, float, float]:
    return (
        float(contour.real.min()),
        float(contour.imag.min()),
        float(contour.real.max()),
        float(contour.imag.max()),
    )


def _bbox_iou(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float],
) -> float:
    left = max(first[0], second[0])
    bottom = max(first[1], second[1])
    right = min(first[2], second[2])
    top = min(first[3], second[3])
    if right <= left or top <= bottom:
        return 0.0

    intersection = (right - left) * (top - bottom)
    first_area = max(1e-9, (first[2] - first[0]) * (first[3] - first[1]))
    second_area = max(1e-9, (second[2] - second[0]) * (second[3] - second[1]))
    union = first_area + second_area - intersection
    return float(intersection / max(union, 1e-9))


def _contours_are_near_duplicates(
    contour: NDArray[np.complex128],
    area: float,
    other: NDArray[np.complex128],
    other_area: float,
    image: LoadedImage,
) -> bool:
    if area < 0.02 * image.image_area or other_area < 0.02 * image.image_area:
        return False

    area_ratio = min(area, other_area) / max(area, other_area)
    if area_ratio < 0.88:
        return False

    centroid_distance = abs(np.mean(contour) - np.mean(other)) / max(image.diagonal, 1.0)
    if centroid_distance > 0.035:
        return False

    return _bbox_iou(_contour_bbox(contour), _contour_bbox(other)) > 0.9


def _deduplicate_contours(
    candidates: list[tuple[NDArray[np.complex128], float]],
    image: LoadedImage,
) -> list[tuple[NDArray[np.complex128], float]]:
    deduped: list[tuple[NDArray[np.complex128], float]] = []
    for contour, area in candidates:
        if any(
            _contours_are_near_duplicates(contour, area, kept_contour, kept_area, image)
            for kept_contour, kept_area in deduped
        ):
            continue
        deduped.append((contour, area))
    return deduped


def resample_arc_length(
    contour: NDArray[np.complex128],
    n_points: int,
) -> NDArray[np.complex128]:
    """Resample a contour to uniform arc-length spacing."""
    if len(contour) < 2:
        return contour

    diffs = np.abs(np.diff(contour))
    arc = np.concatenate([[0.0], np.cumsum(diffs)])
    total_length = arc[-1]
    if total_length < 1e-12:
        return contour[:n_points] if len(contour) >= n_points else contour

    arc_norm = arc / total_length
    # Remove duplicate arc-length positions (zero-length segments)
    unique_mask = np.concatenate([[True], np.diff(arc_norm) > 0])
    arc_norm = arc_norm[unique_mask]
    contour_clean = contour[unique_mask]
    if len(arc_norm) < 2:
        return contour[:n_points] if len(contour) >= n_points else contour

    interp_re = interp1d(arc_norm, contour_clean.real, kind="cubic")
    interp_im = interp1d(arc_norm, contour_clean.imag, kind="cubic")

    t_uniform = np.linspace(0, 1, n_points, endpoint=False)
    return interp_re(t_uniform) + 1j * interp_im(t_uniform)
