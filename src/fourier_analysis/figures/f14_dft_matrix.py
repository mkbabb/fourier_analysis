"""F14: DFT matrix heatmap.

Referenced in §5.1. Shows the real part, imaginary part, and magnitude
of the DFT matrix entries for N=8.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from fourier_analysis.figures.style import save_figure, setup_style


def generate() -> None:
    setup_style()
    N = 8
    n = np.arange(N)
    k = np.arange(N)
    omega = np.exp(-2j * np.pi / N)
    F = omega ** (np.outer(k, n))

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))

    for ax, data, title, cmap in [
        (axes[0], F.real, r"$\mathrm{Re}(F_N)$", "RdBu_r"),
        (axes[1], F.imag, r"$\mathrm{Im}(F_N)$", "RdBu_r"),
        (axes[2], np.abs(F), r"$|F_N|$", "viridis"),
    ]:
        im = ax.imshow(data, cmap=cmap, aspect="equal", interpolation="nearest")
        ax.set_title(title)
        ax.set_xlabel("$n$")
        ax.set_ylabel("$k$")
        ax.set_xticks(range(N))
        ax.set_yticks(range(N))
        fig.colorbar(im, ax=ax, shrink=0.8)

    fig.suptitle(f"DFT Matrix $F_{{N}}$ for $N = {N}$", fontsize=13)
    fig.tight_layout()
    save_figure(fig, "f14_dft_matrix")


if __name__ == "__main__":
    generate()
