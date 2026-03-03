"""Contour ordering via shortest tour heuristic.

Orders a set of contours so that the transition between the end of one
contour and the start of the next is minimized. This produces a smoother
path for epicycle tracing (§6.2).
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def order_contours(
    contours: list[NDArray[np.complex128]],
    *,
    method: str = "nearest",
) -> NDArray[np.complex128]:
    """Order and concatenate contours into a single smooth path.

    Parameters
    ----------
    contours : list of NDArray[complex128]
        Individual contour segments.
    method : str
        Ordering method. Currently supports "nearest" (greedy nearest-neighbor).

    Returns
    -------
    NDArray[complex128]
        Single concatenated path.
    """
    if not contours:
        return np.array([], dtype=np.complex128)

    if len(contours) == 1:
        return contours[0]

    if method == "nearest":
        return _nearest_neighbor_order(contours)
    else:
        raise ValueError(f"Unknown method: {method!r}")


def _nearest_neighbor_order(
    contours: list[NDArray[np.complex128]],
) -> NDArray[np.complex128]:
    """Order contours using nearest-neighbor heuristic.

    At each step, choose the contour whose start or end point is closest
    to the current path endpoint. Reverse contours if needed.
    """
    remaining = list(range(len(contours)))
    ordered: list[NDArray[np.complex128]] = []

    # Start with the first contour
    current_idx = remaining.pop(0)
    ordered.append(contours[current_idx])

    while remaining:
        current_end = ordered[-1][-1]

        best_dist = np.inf
        best_idx = -1
        best_reverse = False

        for idx in remaining:
            c = contours[idx]
            d_start = abs(c[0] - current_end)
            d_end = abs(c[-1] - current_end)

            if d_start < best_dist:
                best_dist = d_start
                best_idx = idx
                best_reverse = False

            if d_end < best_dist:
                best_dist = d_end
                best_idx = idx
                best_reverse = True

        remaining.remove(best_idx)
        c = contours[best_idx]
        if best_reverse:
            c = c[::-1]
        ordered.append(c)

    return np.concatenate(ordered)
