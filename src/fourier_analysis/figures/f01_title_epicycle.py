"""F01: Title page epicycle — Fourier portrait at N = 200 harmonics."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from fourier_analysis.contours import extract_contours, resample_arc_length
from fourier_analysis.epicycles import EpicycleChain
from fourier_analysis.figures.style import BLUE, save_figure, setup_style
from fourier_analysis.shortest_tour import order_contours

PORTRAIT_PATH = Path(__file__).resolve().parents[3] / "assets" / "portraits" / "joseph-fourier.png"


def generate() -> None:
    setup_style()

    contours = extract_contours(PORTRAIT_PATH, resize=256)
    path = order_contours(contours)
    signal = resample_arc_length(path, 1024)

    chain = EpicycleChain.from_signal(signal, n_harmonics=200)
    ts = np.linspace(0, 1, 3000)
    recon = chain.evaluate(ts)

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot(signal.real, signal.imag, color="gray", linewidth=0.5, alpha=0.4, label="Original")
    ax.plot(recon.real, recon.imag, color=BLUE, linewidth=1.0, label=r"$N = 200$")
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.2)
    ax.legend(fontsize=9, loc="upper right")
    ax.set_title(r"Epicycle reconstruction ($N = 200$ harmonics)", fontsize=12)
    fig.tight_layout()
    save_figure(fig, "f01_title_epicycle")


if __name__ == "__main__":
    generate()
