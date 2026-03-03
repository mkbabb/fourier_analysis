"""Shared matplotlib style for publication-quality figures.

All figure scripts import this module to get consistent styling:
Computer Modern fonts, LaTeX math rendering, matched sizing.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

# Output directory for generated figures
ASSETS_DIR = Path(__file__).resolve().parents[3] / "assets"

# Color palette
BLUE = "#2171b5"
RED = "#cb181d"
GREEN = "#238b45"
ORANGE = "#d94801"
PURPLE = "#6a51a3"
GRAY = "#636363"
COLORS = [BLUE, RED, GREEN, ORANGE, PURPLE, GRAY]


def setup_style() -> None:
    """Configure matplotlib for publication-quality output."""
    mpl.rcParams.update(
        {
            "text.usetex": True,
            "font.family": "serif",
            "font.serif": ["Computer Modern Roman"],
            "font.size": 11,
            "axes.labelsize": 12,
            "axes.titlesize": 13,
            "legend.fontsize": 10,
            "xtick.labelsize": 10,
            "ytick.labelsize": 10,
            "figure.figsize": (6, 4),
            "figure.dpi": 150,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.05,
            "lines.linewidth": 1.5,
            "axes.linewidth": 0.8,
            "axes.grid": False,
            "grid.alpha": 0.3,
        }
    )


def save_figure(fig: plt.Figure, name: str) -> None:
    """Save a figure as both PDF and PNG to the assets directory."""
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(ASSETS_DIR / f"{name}.pdf")
    fig.savefig(ASSETS_DIR / f"{name}.png")
    plt.close(fig)
    print(f"Saved: {ASSETS_DIR / name}.{{pdf,png}}")
