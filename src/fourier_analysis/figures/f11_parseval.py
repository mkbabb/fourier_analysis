"""F11: Parseval's identity — energy conservation.

Referenced in §2.8. Bar chart of |c_n|² showing that ||f||² = Σ|c_n|².
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from fourier_analysis.figures.style import BLUE, RED, save_figure, setup_style
from fourier_analysis.series import fourier_coefficients


def generate() -> None:
    setup_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

    # f(x) = sin(10x) + cos²(3x) on [-π, π]
    N = 512
    x = np.linspace(-np.pi, np.pi, N, endpoint=False)
    f = np.sin(10 * x) + np.cos(3 * x) ** 2

    coeffs = fourier_coefficients(f)

    # Energy in time domain
    energy_time = np.sum(np.abs(f) ** 2) / N

    # Energy in frequency domain
    energy_freq = np.sum(np.abs(coeffs) ** 2)

    # Plot |c_n|²
    freqs = np.fft.fftfreq(N, d=1.0 / N)
    magnitudes_sq = np.abs(coeffs) ** 2

    # Only show the significant terms
    mask = magnitudes_sq > 1e-6 * np.max(magnitudes_sq)
    ax1.bar(freqs[mask], magnitudes_sq[mask], width=0.8, color=BLUE, alpha=0.7)
    ax1.set_xlabel(r"Frequency $n$")
    ax1.set_ylabel(r"$|c_n|^2$")
    ax1.set_title(r"Fourier coefficient magnitudes squared")
    ax1.set_xlim(-20, 20)

    # Show energy comparison
    labels = [r"$\frac{1}{N}\sum|f(x_k)|^2$", r"$\sum |c_n|^2$"]
    values = [energy_time, energy_freq]
    bars = ax2.bar(labels, values, color=[BLUE, RED], alpha=0.7, width=0.5)
    ax2.set_ylabel("Energy")
    ax2.set_title(
        f"Parseval's identity\n"
        f"Time: {energy_time:.4f}, Freq: {energy_freq:.4f}"
    )

    for bar, val in zip(bars, values):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.01,
            f"{val:.4f}",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    fig.tight_layout()
    save_figure(fig, "f11_parseval")


if __name__ == "__main__":
    generate()
