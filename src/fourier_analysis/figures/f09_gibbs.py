"""F9: Gibbs phenomenon — partial sums of a square wave.

Referenced in §2.8. Shows the ~9% overshoot at discontinuities that
persists regardless of how many terms are included.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from fourier_analysis.figures.style import COLORS, save_figure, setup_style


def _square_wave_partial_sum(x: np.ndarray, N: int) -> np.ndarray:
    """Partial sum of the Fourier series of a square wave."""
    result = np.zeros_like(x)
    for n in range(1, N + 1, 2):  # odd harmonics only
        result += (4 / (n * np.pi)) * np.sin(n * x)
    return result


def generate() -> None:
    setup_style()
    fig, ax = plt.subplots(figsize=(8, 4.5))

    x = np.linspace(-np.pi, np.pi, 2000)
    square = np.sign(x)

    ax.plot(x, square, "k--", linewidth=0.8, alpha=0.5, label="Square wave")

    for i, N in enumerate([5, 10, 25, 100]):
        S = _square_wave_partial_sum(x, N)
        ax.plot(x, S, color=COLORS[i], linewidth=1.2, label=f"$N = {N}$", alpha=0.85)

    # Annotate overshoot
    ax.annotate(
        r"$\approx 9\%$ overshoot",
        xy=(0.05, 1.18),
        xytext=(0.8, 1.35),
        fontsize=10,
        arrowprops=dict(arrowstyle="->", color="black"),
    )

    ax.set_xlabel(r"$x$")
    ax.set_ylabel(r"$S_N(x)$")
    ax.set_title("Gibbs Phenomenon: Fourier partial sums of a square wave")
    ax.legend(loc="lower right")
    ax.set_xlim(-np.pi, np.pi)
    ax.set_ylim(-1.5, 1.5)

    save_figure(fig, "f09_gibbs")


if __name__ == "__main__":
    generate()
