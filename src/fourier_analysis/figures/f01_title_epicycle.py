"""F01: Title page epicycle — chef portrait via epicycle reconstruction."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from fourier_analysis.contours import extract_contours, resample_arc_length
from fourier_analysis.epicycles import EpicycleChain
from fourier_analysis.figures.style import BLUE, save_figure, setup_style
from fourier_analysis.shortest_tour import build_contour_tour

PORTRAIT_PATH = Path(__file__).resolve().parents[3] / "assets" / "portraits" / "chef.png"


def generate() -> None:
    setup_style()

    contours = extract_contours(
        PORTRAIT_PATH,
        resize=512,
        blur_sigma=1.4,
        min_contour_length=50,
        n_classes=5,
    )
    path = build_contour_tour(contours).path
    signal = resample_arc_length(path, 4096)

    N_HARM = 200
    chain = EpicycleChain.from_signal(signal, n_harmonics=N_HARM)
    ts = np.linspace(0, 1, 16000)
    recon = chain.evaluate(ts)

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot(recon.real, recon.imag, color=BLUE, linewidth=0.5, label=rf"$N = {N_HARM}$")
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.2)
    ax.legend(fontsize=9, loc="upper right")
    ax.set_title(rf"Epicycle reconstruction ($N = {N_HARM}$ harmonics)", fontsize=12)
    fig.tight_layout()
    save_figure(fig, "f01_title_epicycle")


if __name__ == "__main__":
    generate()
