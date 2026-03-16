#!/usr/bin/env python3
"""Pre-compute Fourier decompositions for navigation dropdown icons.

Generates simple icon shapes as closed contour point arrays, runs Fourier
decomposition, and outputs JSON files matching the FourierPathData interface
expected by prepareFourierShape() in web/src/lib/svg-fourier.ts.

Usage:
    python scripts/precompute_nav_icons.py

Outputs:
    web/src/assets/fourier-paths/{paper,visualize,gallery,equation,morph}.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fourier_analysis.bases_evaluation import (
    _serialize_decomposition,
    evaluate_partial_sum,
)
from fourier_analysis.bases_fitting import fourier_decomposition
from fourier_analysis.contours import resample_arc_length


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _arc(cx: float, cy: float, r: float, a0: float, a1: float, n: int) -> list[tuple[float, float]]:
    """Generate n points along a circular arc from angle a0 to a1."""
    return [
        (cx + r * np.cos(a), cy + r * np.sin(a))
        for a in np.linspace(a0, a1, n, endpoint=False)
    ]


def _line(x0: float, y0: float, x1: float, y1: float, n: int) -> list[tuple[float, float]]:
    """Generate n points along a line segment (excluding endpoint)."""
    return [
        (x0 + t * (x1 - x0), y0 + t * (y1 - y0))
        for t in np.linspace(0, 1, n, endpoint=False)
    ]


def _rounded_rect(cx: float, cy: float, w: float, h: float, r: float, n: int = 80) -> np.ndarray:
    """Generate points for a rounded rectangle, well-distributed."""
    # Perimeter breakdown: 4 quarter-arcs + 4 straight edges
    arc_len = np.pi * r / 2  # each corner arc
    edge_h = h - 2 * r
    edge_w = w - 2 * r
    total = 4 * arc_len + 2 * edge_h + 2 * edge_w

    n_arc = max(6, int(n * arc_len / total))
    n_edge_h = max(3, int(n * edge_h / total))
    n_edge_w = max(3, int(n * edge_w / total))

    pts: list[tuple[float, float]] = []

    # Top edge (left to right)
    pts += _line(cx - w / 2 + r, cy - h / 2, cx + w / 2 - r, cy - h / 2, n_edge_w)
    # Top-right arc
    pts += _arc(cx + w / 2 - r, cy - h / 2 + r, r, -np.pi / 2, 0, n_arc)
    # Right edge
    pts += _line(cx + w / 2, cy - h / 2 + r, cx + w / 2, cy + h / 2 - r, n_edge_h)
    # Bottom-right arc
    pts += _arc(cx + w / 2 - r, cy + h / 2 - r, r, 0, np.pi / 2, n_arc)
    # Bottom edge (right to left)
    pts += _line(cx + w / 2 - r, cy + h / 2, cx - w / 2 + r, cy + h / 2, n_edge_w)
    # Bottom-left arc
    pts += _arc(cx - w / 2 + r, cy + h / 2 - r, r, np.pi / 2, np.pi, n_arc)
    # Left edge
    pts += _line(cx - w / 2, cy + h / 2 - r, cx - w / 2, cy - h / 2 + r, n_edge_h)
    # Top-left arc
    pts += _arc(cx - w / 2 + r, cy - h / 2 + r, r, np.pi, 3 * np.pi / 2, n_arc)

    return np.array(pts)


# ---------------------------------------------------------------------------
# Icon shape definitions (centered in 200x200 viewbox)
# ---------------------------------------------------------------------------


def make_paper_icon(n: int = 200) -> np.ndarray:
    """Document/page outline with folded corner — smooth rounded version."""
    left, right = 50, 150
    top, bottom = 25, 175
    fold = 28
    r = 8  # corner radius for the three non-folded corners

    pts: list[tuple[float, float]] = []
    seg = n // 10

    # Top edge to fold start
    pts += _line(left + r, top, right - fold, top, seg * 2)
    # Fold diagonal (smooth quadratic-ish bend)
    for i in range(seg * 2):
        t = i / (seg * 2)
        # Quadratic bezier: top-edge → inner-corner → right-edge
        p0 = (right - fold, top)
        p1 = (right - fold + fold * 0.15, top + fold * 0.15)  # control point
        p2 = (right, top + fold)
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t ** 2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t ** 2 * p2[1]
        pts.append((x, y))
    # Right edge down to bottom-right corner
    pts += _line(right, top + fold, right, bottom - r, seg)
    # Bottom-right corner
    pts += _arc(right - r, bottom - r, r, 0, np.pi / 2, seg // 2)
    # Bottom edge
    pts += _line(right - r, bottom, left + r, bottom, seg)
    # Bottom-left corner
    pts += _arc(left + r, bottom - r, r, np.pi / 2, np.pi, seg // 2)
    # Left edge up to top-left corner
    pts += _line(left, bottom - r, left, top + r, seg)
    # Top-left corner
    pts += _arc(left + r, top + r, r, np.pi, 3 * np.pi / 2, seg // 2)

    return np.array(pts)


def make_visualize_icon(n: int = 200) -> np.ndarray:
    """Eye shape — smooth sinusoidal lids with a pupil bulge."""
    cx, cy = 100, 100
    eye_w = 65
    eye_h = 32

    pts: list[tuple[float, float]] = []

    # Upper lid (cosine-based for smoother tips)
    n_half = n // 2
    for i in range(n_half):
        t = i / n_half  # 0 → 1
        x = cx - eye_w + 2 * eye_w * t
        # Cosine lid shape: 0 at tips, max at center
        s = np.sin(np.pi * t)
        y = cy - eye_h * s
        pts.append((x, y))

    # Lower lid
    for i in range(n - n_half):
        t = i / (n - n_half)
        x = cx + eye_w - 2 * eye_w * t
        s = np.sin(np.pi * t)
        y = cy + eye_h * s
        pts.append((x, y))

    return np.array(pts)


def make_gallery_icon(n: int = 200) -> np.ndarray:
    """Grid icon — 2x2 grid of rounded squares traced as a single continuous path.

    Uses a space-filling path that visits all 4 cells.
    """
    cx, cy = 100, 100
    cell = 48   # cell size
    gap = 10    # gap between cells
    r = 8       # corner radius

    # Centers of the 4 cells
    half = (cell + gap) / 2
    cells = [
        (cx - half, cy - half),  # top-left
        (cx + half, cy - half),  # top-right
        (cx + half, cy + half),  # bottom-right
        (cx - half, cy + half),  # bottom-left
    ]

    pts_per_cell = n // 4
    all_pts: list[tuple[float, float]] = []

    for i, (ccx, ccy) in enumerate(cells):
        rect = _rounded_rect(ccx, ccy, cell, cell, r, pts_per_cell)
        # Connect to next cell: find closest entry/exit points
        if i > 0:
            last = all_pts[-1]
            dists = np.sqrt((rect[:, 0] - last[0]) ** 2 + (rect[:, 1] - last[1]) ** 2)
            start = np.argmin(dists)
            rect = np.roll(rect, -start, axis=0)
        all_pts.extend(rect.tolist())

    return np.array(all_pts)


def make_equation_icon(n: int = 200) -> np.ndarray:
    """Sigma (Σ) summation symbol — thick, smooth outline."""
    left, right = 55, 145
    top, bottom = 30, 170
    mid_y = 100
    indent = 70   # how far left the center V goes
    thick = 14     # stroke thickness
    bar_h = 14     # bar thickness
    r = 4          # fillet radius at sharp corners

    seg = n // 12

    pts: list[tuple[float, float]] = []

    # Outer path (clockwise from top-right)
    # Top bar
    pts += _line(right, top, left, top, seg)
    # Diagonal to center V
    pts += _line(left, top, indent, mid_y, seg * 2)
    # Diagonal to bottom-left
    pts += _line(indent, mid_y, left, bottom, seg * 2)
    # Bottom bar
    pts += _line(left, bottom, right, bottom, seg)

    # Inner path (counter-clockwise, offset inward by stroke thickness)
    # Right side of bottom bar, going left
    pts += _line(right, bottom - bar_h, left + thick, bottom - bar_h, seg)
    # Inner diagonal up to center
    pts += _line(left + thick, bottom - bar_h, indent + thick, mid_y, seg * 2)
    # Inner diagonal up to top bar
    pts += _line(indent + thick, mid_y, left + thick, top + bar_h, seg * 2)
    # Top bar inner, going right
    pts += _line(left + thick, top + bar_h, right, top + bar_h, seg)

    return np.array(pts)


def make_morph_icon(n: int = 200) -> np.ndarray:
    """Infinity symbol — thick lemniscate of Bernoulli."""
    cx, cy = 100, 100
    a = 50  # scale

    pts: list[tuple[float, float]] = []
    for i in range(n):
        t = 2 * np.pi * i / n
        denom = 1 + np.sin(t) ** 2
        x = cx + a * np.cos(t) / denom
        y = cy + a * np.sin(t) * np.cos(t) / denom
        pts.append((x, y))

    return np.array(pts)


# ---------------------------------------------------------------------------
# Fourier processing pipeline
# ---------------------------------------------------------------------------

ICON_SHAPES = {
    "paper": make_paper_icon,
    "visualize": make_visualize_icon,
    "gallery": make_gallery_icon,
    "equation": make_equation_icon,
    "morph": make_morph_icon,
}

N_HARMONICS = 80
N_SAMPLES = 512
N_EVAL = 512
LEVELS = [1, 2, 3, 5, 8, 12, 18, 25, 35, 50, 65, 80]


def build_icon_fourier(points: np.ndarray) -> dict:
    """Convert a point array to FourierPathData JSON structure."""
    contour = points[:, 0] + 1j * points[:, 1]
    contour = resample_arc_length(contour, N_SAMPLES)
    decomp = fourier_decomposition(contour, n_harmonics=N_HARMONICS)

    partial_sums: dict[int, dict[str, list[float]]] = {}
    for level in LEVELS:
        if level > N_HARMONICS:
            continue
        vals = evaluate_partial_sum(decomp, level, N_EVAL)
        partial_sums[level] = {
            "x": vals.real.tolist(),
            "y": vals.imag.tolist(),
        }

    return {
        "original": {
            "x": contour.real.tolist(),
            "y": contour.imag.tolist(),
        },
        "decomposition": _serialize_decomposition(decomp),
        "partial_sums": partial_sums,
        "eval_points": np.linspace(0, 1, N_EVAL, endpoint=False).tolist(),
        "levels": [n for n in LEVELS if n <= N_HARMONICS],
        "n_harmonics": N_HARMONICS,
        "n_samples": N_SAMPLES,
        "n_eval": N_EVAL,
    }


def main() -> None:
    out_dir = PROJECT_ROOT / "web" / "src" / "assets" / "fourier-paths"
    out_dir.mkdir(parents=True, exist_ok=True)

    for name, make_fn in ICON_SHAPES.items():
        print(f"Computing Fourier decomposition for '{name}'...")

        points = make_fn()
        print(f"  {len(points)} raw points")

        data = build_icon_fourier(points)

        out_path = out_dir / f"{name}.json"
        with open(out_path, "w") as f:
            json.dump(data, f, separators=(",", ":"))

        n_components = len(data["decomposition"]["components"])
        n_levels = len(data["levels"])
        size_kb = out_path.stat().st_size / 1024
        print(f"  -> {out_path.relative_to(PROJECT_ROOT)} "
              f"({n_components} components, {n_levels} levels, {size_kb:.1f} KB)")

    print("Done.")


if __name__ == "__main__":
    main()
