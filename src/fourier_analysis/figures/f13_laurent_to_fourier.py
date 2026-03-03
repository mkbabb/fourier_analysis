"""F13: Unit circle parametrization z = e^{iθ}.

Referenced in §3.4. Shows how restricting the Laurent series to the
unit circle yields the Fourier series.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from fourier_analysis.figures.style import BLUE, RED, PURPLE, save_figure, setup_style


def generate() -> None:
    setup_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5))

    theta = np.linspace(0, 2 * np.pi, 300)

    # Left: unit circle in complex plane
    ax1.plot(np.cos(theta), np.sin(theta), color=BLUE, linewidth=2)

    # Mark some points
    for t, label in [(0, r"$1$"), (np.pi / 2, r"$i$"), (np.pi, r"$-1$"), (3 * np.pi / 2, r"$-i$")]:
        x, y = np.cos(t), np.sin(t)
        ax1.plot(x, y, "o", color=RED, markersize=6)
        ax1.annotate(label, xy=(x, y), xytext=(x * 1.2, y * 1.2), fontsize=11, ha="center", va="center")

    # Arrow showing direction
    t_arrow = np.pi / 3
    ax1.annotate(
        "",
        xy=(np.cos(t_arrow + 0.1), np.sin(t_arrow + 0.1)),
        xytext=(np.cos(t_arrow - 0.1), np.sin(t_arrow - 0.1)),
        arrowprops=dict(arrowstyle="->", color=PURPLE, lw=1.5),
    )
    ax1.text(0.35, 1.0, r"$z = e^{i\theta}$", fontsize=12, color=PURPLE)

    ax1.set_xlim(-1.6, 1.6)
    ax1.set_ylim(-1.6, 1.6)
    ax1.set_aspect("equal")
    ax1.axhline(0, color="black", linewidth=0.3)
    ax1.axvline(0, color="black", linewidth=0.3)
    ax1.set_xlabel(r"$\mathrm{Re}(z)$")
    ax1.set_ylabel(r"$\mathrm{Im}(z)$")
    ax1.set_title(r"Unit circle in $\mathbb{C}$")

    # Right: resulting periodic function f(θ)
    # Example: f(z) = 1/(z - 0.5) restricted to unit circle
    z = np.exp(1j * theta)
    f_theta = 1 / (z - 0.5)

    ax2.plot(theta, f_theta.real, color=BLUE, linewidth=1.5, label=r"$\mathrm{Re}(f(e^{i\theta}))$")
    ax2.plot(theta, f_theta.imag, color=RED, linewidth=1.5, linestyle="--", label=r"$\mathrm{Im}(f(e^{i\theta}))$")
    ax2.set_xlabel(r"$\theta$")
    ax2.set_ylabel(r"$f(e^{i\theta})$")
    ax2.set_title(r"Periodic function on $[0, 2\pi)$")
    ax2.set_xlim(0, 2 * np.pi)
    ax2.set_xticks([0, np.pi / 2, np.pi, 3 * np.pi / 2, 2 * np.pi])
    ax2.set_xticklabels([r"$0$", r"$\pi/2$", r"$\pi$", r"$3\pi/2$", r"$2\pi$"])
    ax2.legend(fontsize=9)

    fig.suptitle(r"$z = e^{i\theta}$: Laurent series $\longrightarrow$ Fourier series", fontsize=13)
    fig.tight_layout()
    save_figure(fig, "f13_laurent_to_fourier")


if __name__ == "__main__":
    generate()
