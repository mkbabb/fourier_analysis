"""Contour extraction from images.

Extracts edge contours from images and represents them as complex-valued
paths suitable for Fourier analysis. Used in the epicycle image tracing
pipeline (§6.2).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from PIL import Image
from skimage import feature  # type: ignore[import-untyped]


def extract_contours(
    image_path: str | Path,
    *,
    canny_sigma: float = 2.0,
    resize: int | None = 512,
) -> list[NDArray[np.complex128]]:
    """Extract edge contours from an image as complex paths.

    Parameters
    ----------
    image_path : str or Path
        Path to the input image.
    canny_sigma : float
        Gaussian sigma for Canny edge detection.
    resize : int, optional
        Resize the longest dimension to this value. None to skip.

    Returns
    -------
    list of NDArray[complex128]
        Each array is a contour represented as complex numbers (x + iy).
    """
    img = Image.open(image_path).convert("L")

    if resize is not None:
        ratio = resize / max(img.size)
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)

    arr = np.array(img, dtype=np.float64)

    edges = feature.canny(arr, sigma=canny_sigma)

    # Extract contour coordinates from edge pixels
    ys, xs = np.where(edges)

    if len(xs) == 0:
        return []

    # Convert to complex, centered at origin
    cx, cy = arr.shape[1] / 2, arr.shape[0] / 2
    points = (xs - cx) + 1j * (cy - ys)  # flip y for standard math orientation

    # Cluster into connected contours via nearest-neighbor walk
    contours = _trace_contours(points)

    return [c for c in contours if len(c) > 10]


def _trace_contours(
    points: NDArray[np.complex128],
    max_gap: float = 3.0,
) -> list[NDArray[np.complex128]]:
    """Trace connected contours from a set of edge points.

    Uses a greedy nearest-neighbor walk: starting from an unvisited point,
    repeatedly jump to the nearest unvisited neighbor within max_gap pixels.
    """
    remaining = set(range(len(points)))
    contours: list[NDArray[np.complex128]] = []

    while remaining:
        start = next(iter(remaining))
        remaining.discard(start)
        chain = [points[start]]

        while remaining:
            current = chain[-1]
            # Find nearest unvisited point
            rem_indices = np.array(list(remaining))
            dists = np.abs(points[rem_indices] - current)
            nearest_local = int(np.argmin(dists))

            if dists[nearest_local] > max_gap:
                break

            nearest_idx = rem_indices[nearest_local]
            remaining.discard(nearest_idx)
            chain.append(points[nearest_idx])

        contours.append(np.array(chain, dtype=np.complex128))

    return contours
