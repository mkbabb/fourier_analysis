"""F8: Heat distribution on Fourier's rectangular plate.

Referenced in §1.2. Shows the steady-state temperature u(x,y) with
boundary conditions annotated.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from fourier_analysis.figures.style import save_figure, setup_style


def generate() -> None:
    setup_style()
    fig, ax = plt.subplots(figsize=(6, 5))

    x = np.linspace(0, 4, 200)
    y = np.linspace(-np.pi / 2, np.pi / 2, 200)
    X, Y = np.meshgrid(x, y)

    # Fourier solution: u(x,y) = Σ (4(-1)^n / ((2n+1)π)) e^{-(2n+1)x} cos((2n+1)y)
    U = np.zeros_like(X)
    for n in range(50):
        c_n = 4 * (-1) ** n / ((2 * n + 1) * np.pi)
        U += c_n * np.exp(-(2 * n + 1) * X) * np.cos((2 * n + 1) * Y)

    im = ax.pcolormesh(X, Y, U, cmap="inferno", shading="gouraud")
    cbar = fig.colorbar(im, ax=ax, label=r"$u(x, y)$")

    # Annotate boundary conditions
    ax.annotate(
        r"$u(0, y) = 1$",
        xy=(0, 0),
        xytext=(-0.8, 0),
        fontsize=10,
        ha="center",
        arrowprops=dict(arrowstyle="->", color="white"),
        color="white",
    )
    ax.annotate(
        r"$u(x, \pm\pi/2) = 0$",
        xy=(2, np.pi / 2),
        xytext=(2, np.pi / 2 + 0.3),
        fontsize=10,
        ha="center",
        color="white",
    )
    ax.annotate(
        r"$u \to 0$ as $x \to \infty$",
        xy=(3.8, 0),
        xytext=(3.5, -0.6),
        fontsize=10,
        ha="center",
        arrowprops=dict(arrowstyle="->", color="white"),
        color="white",
    )

    ax.set_xlabel(r"$x$")
    ax.set_ylabel(r"$y$")
    ax.set_title(r"Steady-state heat distribution $u(x, y)$")

    save_figure(fig, "f08_heat_plate")


if __name__ == "__main__":
    generate()
