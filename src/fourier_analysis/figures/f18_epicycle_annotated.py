"""F18: Annotated epicycle decomposition (still frame).

Referenced in §6.2. Shows individual rotating vectors chained tip-to-tail
with labels for amplitude, frequency, and phase.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from fourier_analysis.epicycles import EpicycleChain
from fourier_analysis.figures.style import COLORS, save_figure, setup_style


def generate() -> None:
    setup_style()
    fig, ax = plt.subplots(figsize=(7, 7))

    # Create a simple signal: a cardioid-like shape
    N = 256
    t = np.linspace(0, 2 * np.pi, N, endpoint=False)
    signal = (1 + 0.5 * np.cos(t)) * np.exp(1j * t) + 0.3 * np.exp(3j * t)

    chain = EpicycleChain.from_signal(signal, n_harmonics=6)

    # Evaluate at a specific time
    t_eval = 0.15
    positions = chain.positions_at(t_eval)

    # Draw the full traced path
    ts = np.linspace(0, 1, 500)
    full_path = chain.evaluate(ts)
    ax.plot(full_path.real, full_path.imag, color="gray", linewidth=0.8, alpha=0.4)

    # Draw circles and arms
    for i, comp in enumerate(chain.components):
        center = positions[i]
        tip = positions[i + 1]
        radius = comp.amplitude

        if radius < 0.01:
            continue

        # Circle
        theta = np.linspace(0, 2 * np.pi, 100)
        cx = center.real + radius * np.cos(theta)
        cy = center.imag + radius * np.sin(theta)
        color = COLORS[i % len(COLORS)]
        ax.plot(cx, cy, color=color, linewidth=0.6, alpha=0.5)

        # Arm (vector)
        ax.annotate(
            "",
            xy=(tip.real, tip.imag),
            xytext=(center.real, center.imag),
            arrowprops=dict(arrowstyle="->", color=color, lw=1.5),
        )

        # Label
        mid_x = (center.real + tip.real) / 2
        mid_y = (center.imag + tip.imag) / 2
        ax.text(
            mid_x + 0.05,
            mid_y + 0.05,
            f"$n={comp.frequency}$\n$|c_n|={radius:.2f}$",
            fontsize=7,
            color=color,
        )

    # Mark the tip
    tip_pos = positions[-1]
    ax.plot(tip_pos.real, tip_pos.imag, "o", color="red", markersize=6, zorder=5)

    ax.set_aspect("equal")
    ax.set_xlabel(r"$\mathrm{Re}$")
    ax.set_ylabel(r"$\mathrm{Im}$")
    ax.set_title("Epicycle decomposition: rotating vectors chained tip-to-tail")
    ax.grid(True, alpha=0.2)

    save_figure(fig, "f18_epicycle_annotated")


if __name__ == "__main__":
    generate()
