"""Contour ordering via shortest tour heuristic.

Orders a set of contours so that the transition between the end of one
contour and the start of the next is minimized. This produces a smoother
concatenated path for epicycle tracing (§6.2).

Two methods are available:

- **nearest**: KDTree-accelerated nearest-neighbor, O(N log N). A solid
  baseline---typically within ~20-25% of optimal.
- **nearest_2opt** (default): nearest-neighbor initialization followed by
  2-opt local search. The 2-opt pass iteratively reverses sub-tours to
  reduce total gap distance, usually landing within ~5% of optimal.

The 2-opt operates on the *sequence of contour indices*, not individual
points. Each "edge" cost is ``|end_of_contour_i - start_of_contour_{i+1}|``.
A 2-opt swap reverses a subsequence of contours and flips each contour's
direction within that subsequence, since the traversal direction reverses.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.spatial import KDTree  # type: ignore[import-untyped]


@dataclass(frozen=True)
class ContourTour:
    """Result of ordering and concatenating contours.

    Attributes
    ----------
    ordered_contours : tuple of NDArray[complex128]
        Contours in traversal order (possibly reversed).
    gap_lengths : tuple of float
        Distance between the end of contour *i* and the start of *i+1*.
    path : NDArray[complex128]
        Single concatenated path (the main output).
    """

    ordered_contours: tuple[NDArray[np.complex128], ...]
    gap_lengths: tuple[float, ...]
    path: NDArray[np.complex128]


def build_contour_tour(
    contours: list[NDArray[np.complex128]],
    *,
    method: str = "nearest_2opt",
) -> ContourTour:
    """Order and concatenate contours into a smooth tour.

    Parameters
    ----------
    contours : list of NDArray[complex128]
        Individual contour segments.
    method : str
        ``"nearest"`` for KDTree nearest-neighbor, or ``"nearest_2opt"``
        (default) for NN + 2-opt refinement.

    Returns
    -------
    ContourTour
        Ordered contours, gap lengths, and concatenated path.
    """
    if not contours:
        return ContourTour(
            ordered_contours=(),
            gap_lengths=(),
            path=np.array([], dtype=np.complex128),
        )

    if method not in ("nearest", "nearest_2opt"):
        raise ValueError(f"Unknown method: {method!r}")

    if len(contours) == 1:
        c = contours[0].copy()
        return ContourTour(
            ordered_contours=(c,),
            gap_lengths=(),
            path=c,
        )

    if method == "nearest":
        order, reversed_flags = _nearest_neighbor(contours)
    else:
        order, reversed_flags = _nearest_neighbor(contours)
        order, reversed_flags = _two_opt(contours, order, reversed_flags)

    ordered: list[NDArray[np.complex128]] = []
    for idx, rev in zip(order, reversed_flags):
        c = contours[idx]
        ordered.append(c[::-1] if rev else c)

    gaps: list[float] = []
    for i in range(len(ordered) - 1):
        gaps.append(float(abs(ordered[i][-1] - ordered[i + 1][0])))

    return ContourTour(
        ordered_contours=tuple(ordered),
        gap_lengths=tuple(gaps),
        path=np.concatenate(ordered),
    )


def _complex_to_xy(z: complex) -> tuple[float, float]:
    """Convert a complex number to an (x, y) pair."""
    return (z.real, z.imag)


def _nearest_neighbor(
    contours: list[NDArray[np.complex128]],
) -> tuple[list[int], list[bool]]:
    """KDTree-accelerated nearest-neighbor ordering.

    For each contour, builds a KDTree from the start and end points of
    all unvisited contours, then queries for the nearest endpoint to the
    current path's tail. O(N log N) vs the old O(N^2) brute force.
    """
    n = len(contours)

    # Build endpoint arrays: even indices = start, odd indices = end
    endpoints = np.zeros((2 * n, 2))
    for i, c in enumerate(contours):
        endpoints[2 * i] = [c[0].real, c[0].imag]
        endpoints[2 * i + 1] = [c[-1].real, c[-1].imag]

    visited = [False] * n
    order: list[int] = []
    reversed_flags: list[bool] = []

    # Start with contour 0, unreversed
    visited[0] = True
    order.append(0)
    reversed_flags.append(False)
    current_end = contours[0][-1]

    for _ in range(n - 1):
        # Collect unvisited endpoint coords
        unvisited_indices: list[int] = []
        unvisited_coords: list[list[float]] = []
        for i in range(n):
            if not visited[i]:
                unvisited_indices.append(i)
                unvisited_coords.append(endpoints[2 * i].tolist())     # start
                unvisited_coords.append(endpoints[2 * i + 1].tolist()) # end

        tree = KDTree(unvisited_coords)
        _, nn_idx = tree.query([current_end.real, current_end.imag])

        # Decode: which contour and which endpoint?
        contour_local = nn_idx // 2
        is_end_point = (nn_idx % 2) == 1
        contour_idx = unvisited_indices[contour_local]

        visited[contour_idx] = True
        order.append(contour_idx)
        # If the nearest point was the *end*, we need to reverse
        reversed_flags.append(bool(is_end_point))

        c = contours[contour_idx]
        current_end = c[0] if is_end_point else c[-1]

    return order, reversed_flags


def _gap_cost(
    contours: list[NDArray[np.complex128]],
    order: list[int],
    reversed_flags: list[bool],
) -> float:
    """Total gap distance between consecutive contours."""
    total = 0.0
    for i in range(len(order) - 1):
        c_curr = contours[order[i]]
        c_next = contours[order[i + 1]]
        end = c_curr[0] if reversed_flags[i] else c_curr[-1]
        start = c_next[-1] if reversed_flags[i + 1] else c_next[0]
        total += abs(end - start)
    return total


def _two_opt(
    contours: list[NDArray[np.complex128]],
    order: list[int],
    reversed_flags: list[bool],
    max_iters: int = 50,
) -> tuple[list[int], list[bool]]:
    """2-opt local search over the contour sequence.

    Iteratively reverses sub-tours to reduce total gap distance. Each
    swap reverses both the ordering and the direction of every contour
    in the reversed segment (since traversal direction flips).
    """
    order = list(order)
    reversed_flags = list(reversed_flags)
    n = len(order)

    if n < 3:
        return order, reversed_flags

    improved = True
    iterations = 0

    while improved and iterations < max_iters:
        improved = False
        iterations += 1

        for i in range(n - 1):
            for j in range(i + 2, n):
                # Compute cost change for reversing segment [i+1 .. j]
                # Current edges: (i -> i+1) and (j -> j+1 if exists)
                # New edges: (i -> j) and (i+1 -> j+1 if exists)

                def _end_of(k: int) -> complex:
                    c = contours[order[k]]
                    return c[0] if reversed_flags[k] else c[-1]

                def _start_of(k: int) -> complex:
                    c = contours[order[k]]
                    return c[-1] if reversed_flags[k] else c[0]

                old_cost = abs(_end_of(i) - _start_of(i + 1))
                if j + 1 < n:
                    old_cost += abs(_end_of(j) - _start_of(j + 1))

                # After reversal: segment [i+1..j] is reversed
                # new edge from i to j (j was reversed)
                new_cost = abs(_end_of(i) - _end_of(j))
                if j + 1 < n:
                    new_cost += abs(_start_of(i + 1) - _start_of(j + 1))

                if new_cost < old_cost - 1e-10:
                    # Reverse the segment [i+1 .. j]
                    seg_order = order[i + 1 : j + 1]
                    seg_rev = reversed_flags[i + 1 : j + 1]
                    seg_order.reverse()
                    seg_rev.reverse()
                    seg_rev = [not r for r in seg_rev]
                    order[i + 1 : j + 1] = seg_order
                    reversed_flags[i + 1 : j + 1] = seg_rev
                    improved = True

    return order, reversed_flags
