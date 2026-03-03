"""F10: Fejér summation vs partial sums for a square wave.

Referenced in §2.8. Compares oscillating partial sums against smooth
Cesàro means (Fejér summation).
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from fourier_analysis.figures.style import BLUE, RED, save_figure, setup_style


def generate() -> None:
    setup_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4), sharey=True)

    x = np.linspace(-np.pi, np.pi, 2000)
    square = np.sign(x)
    N = 25

    # Partial sums (Dirichlet)
    S_N = np.zeros_like(x)
    for n in range(1, N + 1, 2):
        S_N += (4 / (n * np.pi)) * np.sin(n * x)

    # Cesàro means (Fejér)
    sigma_N = np.zeros_like(x)
    for k in range(1, N + 1):
        S_k = np.zeros_like(x)
        for n in range(1, k + 1, 2):
            S_k += (4 / (n * np.pi)) * np.sin(n * x)
        sigma_N += S_k
    sigma_N /= N

    ax1.plot(x, square, "k--", linewidth=0.8, alpha=0.4, label="Square wave")
    ax1.plot(x, S_N, color=BLUE, linewidth=1.2, label=f"$S_{{{N}}}(x)$")
    ax1.set_title(f"Partial sum ($N = {N}$)")
    ax1.set_xlabel(r"$x$")
    ax1.set_ylabel(r"Amplitude")
    ax1.legend()

    ax2.plot(x, square, "k--", linewidth=0.8, alpha=0.4, label="Square wave")
    ax2.plot(x, sigma_N, color=RED, linewidth=1.2, label=rf"$\sigma_{{{N}}}(x)$")
    ax2.set_title(rf"Fej\'er mean ($N = {N}$)")
    ax2.set_xlabel(r"$x$")
    ax2.legend()

    for ax in (ax1, ax2):
        ax.set_xlim(-np.pi, np.pi)
        ax.set_ylim(-1.5, 1.5)

    fig.tight_layout()
    save_figure(fig, "f10_fejer_vs_partial")


if __name__ == "__main__":
    generate()
