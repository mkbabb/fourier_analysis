"""F19: Epicycle reconstruction progression.

Referenced in §6.2. 4-panel showing reconstruction of a portrait contour
with 3, 10, 50, and 200 harmonics. Uses the Fourier portrait as input;
falls back to a synthetic shape if the image isn't available.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from fourier_analysis.contours import extract_contours, resample_arc_length
from fourier_analysis.epicycles import EpicycleChain
from fourier_analysis.figures.style import BLUE, save_figure, setup_style
from fourier_analysis.shortest_tour import order_contours

PORTRAIT_PATH = Path(__file__).resolve().parents[3] / "assets" / "portraits" / "joseph-fourier.png"


def _load_contour(n_points: int = 1024) -> np.ndarray:
    """Load the Fourier portrait contour, or fall back to a synthetic shape."""
    if PORTRAIT_PATH.exists():
        contours = extract_contours(PORTRAIT_PATH, resize=256)
        if contours:
            path = order_contours(contours)
            return resample_arc_length(path, n_points)

    # Fallback: parametric rounded-square
    t = np.linspace(0, 2 * np.pi, n_points, endpoint=False)
    return (
        np.sign(np.cos(t)) * (1 + 0.3 * np.abs(np.cos(t)))
        + 1j * np.sign(np.sin(t)) * (1 + 0.3 * np.abs(np.sin(t)))
    )


def generate() -> None:
    setup_style()

    signal = _load_contour()

    fig, axes = plt.subplots(2, 2, figsize=(8, 8))
    harmonics_list = [3, 10, 50, 200]

    for ax, n_harm in zip(axes.flat, harmonics_list):
        chain = EpicycleChain.from_signal(signal, n_harmonics=n_harm)
        ts = np.linspace(0, 1, 2000)
        path = chain.evaluate(ts)

        ax.plot(signal.real, signal.imag, color="gray", linewidth=0.5, alpha=0.4, label="Original")
        ax.plot(path.real, path.imag, color=BLUE, linewidth=1.2, label=f"$N = {n_harm}$")
        ax.set_aspect("equal")
        ax.set_title(f"$N = {n_harm}$ harmonics")
        ax.grid(True, alpha=0.2)
        ax.legend(fontsize=8, loc="upper right")

    fig.suptitle("Epicycle reconstruction with increasing harmonics", fontsize=13)
    fig.tight_layout()
    save_figure(fig, "f19_epicycle_convergence")


if __name__ == "__main__":
    generate()
