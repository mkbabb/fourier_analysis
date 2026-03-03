"""F6: f·g pointwise product and Riemann sum approximation of ⟨f,g⟩.

Referenced in Example 4.0.1. Shows the inner product as area under the
pointwise product curve, approximated by a Riemann sum.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from fourier_analysis.figures.style import BLUE, GREEN, save_figure, setup_style


def generate() -> None:
    setup_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

    N = 40000
    x = np.linspace(-np.pi, np.pi, N)
    dx = (2 * np.pi) / N

    f = np.sin(10 * x) + np.cos(3 * x) ** 2
    g = np.exp(x)
    fg = f * g

    # Exact value
    exact = 3098 * np.sinh(np.pi) / 3737

    # Riemann sum
    riemann = np.sum(fg) * dx

    # Left: f*g with filled area
    ax1.plot(x, fg, color=BLUE, linewidth=0.5, alpha=0.8)
    ax1.fill_between(x, fg, alpha=0.2, color=BLUE)
    ax1.set_xlabel(r"$x$")
    ax1.set_ylabel(r"$f(x) \cdot g(x)$")
    ax1.set_title(r"$f \cdot g$ pointwise product")
    ax1.set_xlim(-np.pi, np.pi)

    # Right: show the Riemann sum approximation
    x_coarse = np.linspace(-np.pi, np.pi, 50)
    dx_coarse = (2 * np.pi) / 50
    f_c = np.sin(10 * x_coarse) + np.cos(3 * x_coarse) ** 2
    g_c = np.exp(x_coarse)
    fg_c = f_c * g_c

    ax2.bar(x_coarse, fg_c, width=dx_coarse * 0.9, color=GREEN, alpha=0.5, align="center")
    ax2.plot(x, fg, color=BLUE, linewidth=0.8, alpha=0.6)
    ax2.set_xlabel(r"$x$")
    ax2.set_ylabel(r"$f(x) \cdot g(x)$")
    ax2.set_title(
        rf"Riemann sum $\approx {riemann:.4f}$, exact $= {exact:.4f}$"
        f"\n(error $= {abs(riemann - exact):.2e}$)"
    )
    ax2.set_xlim(-np.pi, np.pi)

    fig.tight_layout()
    save_figure(fig, "f06_inner_product_2")


if __name__ == "__main__":
    generate()
