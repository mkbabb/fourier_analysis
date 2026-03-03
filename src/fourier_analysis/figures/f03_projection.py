"""F3: Vector projection of u onto v in R².

Referenced at the Ch II opener. Illustrates the geometric interpretation
of the inner product as projection.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from fourier_analysis.figures.style import BLUE, RED, GRAY, save_figure, setup_style


def generate() -> None:
    setup_style()
    fig, ax = plt.subplots(figsize=(5, 4))

    u = np.array([3.0, 2.5])
    v = np.array([4.0, 1.0])

    # Projection of u onto v
    proj_scalar = np.dot(u, v) / np.dot(v, v)
    proj = proj_scalar * v

    # Draw vectors
    ax.annotate("", xy=u, xytext=(0, 0), arrowprops=dict(arrowstyle="->", color=BLUE, lw=2))
    ax.annotate("", xy=v, xytext=(0, 0), arrowprops=dict(arrowstyle="->", color=RED, lw=2))
    ax.annotate("", xy=proj, xytext=(0, 0), arrowprops=dict(arrowstyle="->", color=GRAY, lw=1.5))

    # Dashed line from u to proj
    ax.plot([u[0], proj[0]], [u[1], proj[1]], "--", color=GRAY, linewidth=0.8, alpha=0.6)

    # Right angle marker
    perp_size = 0.2
    perp_dir = (u - proj) / np.linalg.norm(u - proj) * perp_size
    par_dir = v / np.linalg.norm(v) * perp_size
    corner = proj + perp_dir
    ax.plot(
        [proj[0] + perp_dir[0], proj[0] + perp_dir[0] + par_dir[0], proj[0] + par_dir[0]],
        [proj[1] + perp_dir[1], proj[1] + perp_dir[1] + par_dir[1], proj[1] + par_dir[1]],
        color=GRAY,
        linewidth=0.6,
    )

    # Labels
    ax.text(u[0] + 0.1, u[1] + 0.1, r"$\vec{u}$", fontsize=14, color=BLUE)
    ax.text(v[0] + 0.1, v[1] - 0.2, r"$\vec{v}$", fontsize=14, color=RED)
    ax.text(
        proj[0] - 0.1,
        proj[1] - 0.35,
        r"$\mathrm{proj}_{\vec{v}}\vec{u}$",
        fontsize=11,
        color=GRAY,
    )

    ax.set_xlim(-0.5, 5)
    ax.set_ylim(-0.5, 3.5)
    ax.set_aspect("equal")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_xlabel(r"$x$")
    ax.set_ylabel(r"$y$")

    save_figure(fig, "f03_projection")


if __name__ == "__main__":
    generate()
