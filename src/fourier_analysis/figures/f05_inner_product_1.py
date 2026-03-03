"""F5: f(x) = sin(10x) + cos²(3x) with 1000 sample vectors vs continuous.

Referenced in Example 4.0.1. Shows the discrete vector representation
alongside the continuous function.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from fourier_analysis.figures.style import BLUE, RED, save_figure, setup_style


def generate() -> None:
    setup_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

    x_cont = np.linspace(-np.pi, np.pi, 2000)
    f_cont = np.sin(10 * x_cont) + np.cos(3 * x_cont) ** 2

    N = 1000
    x_disc = np.linspace(-np.pi, np.pi, N)
    f_disc = np.sin(10 * x_disc) + np.cos(3 * x_disc) ** 2

    # Left: discrete samples
    ax1.vlines(x_disc, 0, f_disc, colors=BLUE, linewidth=0.3, alpha=0.6)
    ax1.set_xlabel(r"$x$")
    ax1.set_ylabel(r"$f(x)$")
    ax1.set_title(f"$f$ with ${N}$ sample vectors")

    # Right: continuous
    ax2.plot(x_cont, f_cont, color=RED, linewidth=1.2)
    ax2.set_xlabel(r"$x$")
    ax2.set_ylabel(r"$f(x)$")
    ax2.set_title(r"$f(x) = \sin(10x) + \cos^2(3x)$")

    for ax in (ax1, ax2):
        ax.set_xlim(-np.pi, np.pi)

    fig.tight_layout()
    save_figure(fig, "f05_inner_product_1")


if __name__ == "__main__":
    generate()
