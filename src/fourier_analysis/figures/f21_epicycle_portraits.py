"""F21: Epicycle reconstruction of real portraits.

Referenced in §6.2. Multi-panel figure showing the full pipeline applied
to 2--3 historical portraits (Fourier, Cauchy, NES-ROB). Each panel
shows the original image as a small inset alongside the Fourier-
reconstructed contour at N = 200 harmonics.

This is the capstone figure for the applications chapter---the visual
payoff for the entire contour extraction + tour ordering + epicycle
chain machinery.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

from fourier_analysis.contours import extract_contours, resample_arc_length
from fourier_analysis.epicycles import EpicycleChain
from fourier_analysis.figures.style import COLORS, BLUE, save_figure, setup_style
from fourier_analysis.shortest_tour import build_contour_tour

PORTRAITS_DIR = Path(__file__).resolve().parents[3] / "assets" / "portraits"

SUBJECTS = [
    ("Joseph Fourier", "joseph-fourier.png", 200),
    ("Augustin-Louis Cauchy", "cauchy.png", 200),
    ("NES R.O.B.", "NES-ROB.png", 200),
]


def _process_portrait(
    image_path: Path,
    n_harmonics: int,
    n_points: int = 1024,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Extract contours, build epicycle chain, and reconstruct.

    Returns (original_image_array, contour_path, reconstruction).
    """
    img = Image.open(image_path)
    # Keep RGBA for transparent-background portraits; fall back to RGB
    if img.mode == "RGBA":
        img_arr = np.array(img)
    else:
        img_arr = np.array(img.convert("L"))

    contours = extract_contours(image_path, resize=256)
    path = build_contour_tour(contours).path
    path = resample_arc_length(path, n_points)

    chain = EpicycleChain.from_signal(path, n_harmonics=n_harmonics)
    ts = np.linspace(0, 1, 3000)
    recon = chain.evaluate(ts)

    return img_arr, path, recon


def generate() -> None:
    setup_style()

    available = [(name, PORTRAITS_DIR / fname, n) for name, fname, n in SUBJECTS if (PORTRAITS_DIR / fname).exists()]

    if not available:
        print("No portrait assets found; skipping F21.")
        return

    n_cols = len(available)
    fig, axes = plt.subplots(1, n_cols, figsize=(5 * n_cols, 6))
    if n_cols == 1:
        axes = [axes]

    for ax, (name, img_path, n_harm) in zip(axes, available):
        img_arr, path, recon = _process_portrait(img_path, n_harm)

        # Plot reconstruction
        ax.plot(recon.real, recon.imag, color=BLUE, linewidth=0.8)
        ax.set_aspect("equal")
        ax.set_title(f"{name} ($N = {n_harm}$)")
        ax.grid(True, alpha=0.15)
        ax.tick_params(labelsize=7)

        # Inset: original image
        inset = ax.inset_axes([0.02, 0.02, 0.28, 0.28])
        inset.imshow(img_arr, **({} if img_arr.ndim == 3 else {"cmap": "gray"}))
        inset.axis("off")

    fig.suptitle("Epicycle portrait reconstructions", fontsize=14)
    fig.tight_layout()
    save_figure(fig, "f21_epicycle_portraits")


if __name__ == "__main__":
    generate()
