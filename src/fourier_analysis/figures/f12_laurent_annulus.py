"""F12: Annulus in the complex plane for Laurent series.

Referenced in §3.3. Shows the annulus of convergence with the unit circle
highlighted and Laurent series terms annotated.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from fourier_analysis.figures.style import BLUE, RED, GRAY, save_figure, setup_style


def generate() -> None:
    setup_style()
    fig, ax = plt.subplots(figsize=(6, 6))

    theta = np.linspace(0, 2 * np.pi, 300)

    r1, r2 = 0.5, 2.0

    # Fill annulus
    theta_fill = np.linspace(0, 2 * np.pi, 100)
    for r in np.linspace(r1, r2, 50):
        ax.plot(r * np.cos(theta_fill), r * np.sin(theta_fill), color=BLUE, alpha=0.03, linewidth=0.5)

    # Boundaries
    ax.plot(r1 * np.cos(theta), r1 * np.sin(theta), color=RED, linewidth=1.5, linestyle="--", label=f"$r_1 = {r1}$")
    ax.plot(r2 * np.cos(theta), r2 * np.sin(theta), color=RED, linewidth=1.5, linestyle="--", label=f"$r_2 = {r2}$")

    # Unit circle
    ax.plot(np.cos(theta), np.sin(theta), color=BLUE, linewidth=2.0, label=r"$|z| = 1$")

    # Singularity at origin
    ax.plot(0, 0, "x", color=RED, markersize=10, markeredgewidth=2)
    ax.annotate(r"$z_0$", xy=(0, 0), xytext=(0.15, -0.2), fontsize=12, color=RED)

    # Annotations
    ax.annotate(
        "",
        xy=(r1 * np.cos(np.pi / 4), r1 * np.sin(np.pi / 4)),
        xytext=(0, 0),
        arrowprops=dict(arrowstyle="<->", color=GRAY),
    )
    ax.text(0.12, 0.25, r"$r_1$", fontsize=11, color=GRAY)

    ax.annotate(
        "",
        xy=(r2 * np.cos(-np.pi / 6), r2 * np.sin(-np.pi / 6)),
        xytext=(0, 0),
        arrowprops=dict(arrowstyle="<->", color=GRAY),
    )
    ax.text(0.9, -0.6, r"$r_2$", fontsize=11, color=GRAY)

    # Label the annulus
    ax.text(1.1, 1.1, r"$A = \{z : r_1 < |z - z_0| < r_2\}$", fontsize=11, color=BLUE)

    ax.set_xlim(-2.5, 2.5)
    ax.set_ylim(-2.5, 2.5)
    ax.set_aspect("equal")
    ax.legend(loc="lower left", fontsize=9)
    ax.set_xlabel(r"$\mathrm{Re}(z)$")
    ax.set_ylabel(r"$\mathrm{Im}(z)$")
    ax.set_title("Annulus of convergence for Laurent series")
    ax.axhline(0, color="black", linewidth=0.3)
    ax.axvline(0, color="black", linewidth=0.3)

    save_figure(fig, "f12_laurent_annulus")


if __name__ == "__main__":
    generate()
