"""F19: Epicycle reconstruction progression.

Referenced in §6.2. 4-panel showing reconstruction of a shape
with 3, 10, 50, 200 harmonics.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from fourier_analysis.epicycles import EpicycleChain
from fourier_analysis.figures.style import BLUE, save_figure, setup_style


def generate() -> None:
    setup_style()

    # Create a square-ish shape as the target
    N = 512
    t = np.linspace(0, 2 * np.pi, N, endpoint=False)
    # Parametric square (rounded)
    signal = np.sign(np.cos(t)) * (1 + 0.3 * np.abs(np.cos(t))) + \
             1j * np.sign(np.sin(t)) * (1 + 0.3 * np.abs(np.sin(t)))

    fig, axes = plt.subplots(2, 2, figsize=(8, 8))
    harmonics_list = [3, 10, 50, 200]

    for ax, n_harm in zip(axes.flat, harmonics_list):
        chain = EpicycleChain.from_signal(signal, n_harmonics=n_harm)
        ts = np.linspace(0, 1, 1000)
        path = chain.evaluate(ts)

        ax.plot(signal.real, signal.imag, color="gray", linewidth=0.5, alpha=0.4, label="Original")
        ax.plot(path.real, path.imag, color=BLUE, linewidth=1.2, label=f"$N = {n_harm}$")
        ax.set_aspect("equal")
        ax.set_title(f"$N = {n_harm}$ harmonics")
        ax.grid(True, alpha=0.2)
        ax.legend(fontsize=8, loc="upper right")

    fig.suptitle("Epicycle reconstruction with increasing harmonics", fontsize=13)
    fig.tight_layout()
    save_figure(fig, "f19_epicycle_convergence")


if __name__ == "__main__":
    generate()
