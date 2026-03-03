"""F2: Partial sums of cosine series converging to f=1 on [-π/2, π/2].

Referenced after eq:f4 in §1.2.2. Shows how the Fourier cosine series
discovered by Fourier converges to the constant function 1.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from fourier_analysis.figures.style import COLORS, save_figure, setup_style


def generate() -> None:
    setup_style()
    fig, ax = plt.subplots(figsize=(7, 4.5))

    y = np.linspace(-np.pi / 2, np.pi / 2, 1000)
    ns_list = [1, 3, 7, 20, 50]

    for i, N in enumerate(ns_list):
        S = np.zeros_like(y)
        for n in range(N):
            c_n = 4 * (-1) ** n / ((2 * n + 1) * np.pi)
            S += c_n * np.cos((2 * n + 1) * y)
        ax.plot(y, S, color=COLORS[i % len(COLORS)], label=f"$N = {N}$", alpha=0.8)

    ax.axhline(1.0, color="black", linestyle="--", linewidth=0.8, alpha=0.5, label="$f(y) = 1$")
    ax.set_xlabel(r"$y$")
    ax.set_ylabel(r"$S_N(y)$")
    ax.set_title(r"Partial sums converging to $f(y) = 1$ on $[-\pi/2, \pi/2]$")
    ax.legend(loc="lower center", ncol=3)
    ax.set_xlim(-np.pi / 2, np.pi / 2)
    ax.set_ylim(-0.3, 1.4)

    save_figure(fig, "f02_partial_sums")


if __name__ == "__main__":
    generate()
