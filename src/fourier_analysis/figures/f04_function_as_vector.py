"""F4: Function f as infinite-dimensional vector (intensity plot).

Referenced in Example 2.3.1. Shows how a continuous function can be
viewed as a vector of (infinitely many) samples.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from fourier_analysis.figures.style import save_figure, setup_style


def generate() -> None:
    setup_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, 3.5), gridspec_kw={"width_ratios": [1, 3]})

    x = np.linspace(-1, 1, 200)
    f = np.sin(3 * np.pi * x) + 0.5 * np.cos(5 * np.pi * x)

    # Left: vertical bar chart showing f as a "vector"
    x_coarse = np.linspace(-1, 1, 40)
    f_coarse = np.sin(3 * np.pi * x_coarse) + 0.5 * np.cos(5 * np.pi * x_coarse)
    colors = plt.cm.RdBu_r((f_coarse - f_coarse.min()) / (f_coarse.max() - f_coarse.min()))  # type: ignore[attr-defined]
    ax1.barh(range(len(f_coarse)), f_coarse, color=colors, height=0.8)
    ax1.set_ylabel("Component index $k$")
    ax1.set_xlabel(r"$f(x_k)$")
    ax1.set_title(r"$\vec{f}$")
    ax1.invert_yaxis()

    # Right: the continuous function
    ax2.plot(x, f, color="#2171b5", linewidth=1.5)
    ax2.fill_between(x, f, alpha=0.15, color="#2171b5")
    ax2.set_xlabel(r"$x$")
    ax2.set_ylabel(r"$f(x)$")
    ax2.set_title(r"$f(x) = \sin(3\pi x) + \frac{1}{2}\cos(5\pi x)$")

    fig.tight_layout()
    save_figure(fig, "f04_function_as_vector")


if __name__ == "__main__":
    generate()
