"""F20: Image -> contour -> Fourier pipeline.

Referenced in §6.2. 4-panel showing: (a) original image, (b) edge
detection / Otsu threshold, (c) ordered contour path, (d) Fourier
reconstruction.

Uses the Fourier portrait as the default input image. Falls back to
a synthetic trefoil if no portrait is available.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from skimage import filters, measure  # type: ignore[import-untyped]

from fourier_analysis.contours import extract_contours, resample_arc_length
from fourier_analysis.epicycles import EpicycleChain
from fourier_analysis.figures.style import BLUE, RED, save_figure, setup_style
from fourier_analysis.shortest_tour import build_contour_tour

PORTRAIT_PATH = Path(__file__).resolve().parents[3] / "assets" / "portraits" / "joseph-fourier.png"


def generate(image_path: str | Path | None = None) -> None:
    setup_style()

    if image_path is None and PORTRAIT_PATH.exists():
        image_path = PORTRAIT_PATH

    fig, axes = plt.subplots(2, 2, figsize=(10, 10))

    if image_path is not None:
        contours = extract_contours(image_path, resize=256)
        path = build_contour_tour(contours).path
        path = resample_arc_length(path, 1024)

        # (a) Original image
        img_orig = Image.open(image_path)
        if img_orig.mode == "RGBA":
            axes[0, 0].imshow(np.array(img_orig))
        else:
            axes[0, 0].imshow(np.array(img_orig.convert("L")), cmap="gray")
        axes[0, 0].set_title("(a) Original image")
        axes[0, 0].axis("off")

        # (b) Otsu threshold visualization
        img = img_orig.convert("L")
        ratio = 256 / max(img.size)
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img_resized = img.resize(new_size, Image.Resampling.LANCZOS)
        arr = np.array(img_resized, dtype=np.float64)
        arr = arr / arr.max() if arr.max() > 0 else arr
        thresh = filters.threshold_otsu(arr)
        binary = arr < thresh
        contours_vis = measure.find_contours(binary.astype(float), level=0.5)
        axes[0, 1].imshow(binary, cmap="gray")
        for cv in contours_vis:
            axes[0, 1].plot(cv[:, 1], cv[:, 0], color=RED, linewidth=0.5, alpha=0.6)
        axes[0, 1].set_title("(b) Otsu threshold + marching squares")
        axes[0, 1].axis("off")
    else:
        # Synthetic shape: trefoil knot
        N = 1024
        t = np.linspace(0, 2 * np.pi, N, endpoint=False)
        path = (np.sin(t) + 2 * np.sin(2 * t)) + 1j * (np.cos(t) - 2 * np.cos(2 * t))

        axes[0, 0].plot(path.real, path.imag, color="gray", linewidth=2)
        axes[0, 0].set_aspect("equal")
        axes[0, 0].set_title("(a) Target shape (trefoil)")
        axes[0, 0].grid(True, alpha=0.2)

        axes[0, 1].scatter(path.real, path.imag, c=np.arange(len(path)), cmap="viridis", s=1)
        axes[0, 1].set_aspect("equal")
        axes[0, 1].set_title("(b) Ordered contour points")
        axes[0, 1].grid(True, alpha=0.2)

    # (c) Ordered contour path
    axes[1, 0].plot(path.real, path.imag, color=RED, linewidth=0.5, alpha=0.8)
    axes[1, 0].set_aspect("equal")
    axes[1, 0].set_title(f"(c) Contour path ({len(path)} points)")
    axes[1, 0].grid(True, alpha=0.2)

    # (d) Fourier reconstruction
    n_harmonics = min(200, len(path) // 2)
    chain = EpicycleChain.from_signal(path, n_harmonics=n_harmonics)
    ts = np.linspace(0, 1, 2000)
    recon = chain.evaluate(ts)

    axes[1, 1].plot(path.real, path.imag, color="gray", linewidth=0.5, alpha=0.3, label="Original")
    axes[1, 1].plot(recon.real, recon.imag, color=BLUE, linewidth=1.0, label=f"$N = {n_harmonics}$")
    axes[1, 1].set_aspect("equal")
    axes[1, 1].set_title(f"(d) Fourier reconstruction ($N = {n_harmonics}$)")
    axes[1, 1].legend(fontsize=8)
    axes[1, 1].grid(True, alpha=0.2)

    fig.suptitle("Contour Tracing Pipeline", fontsize=14)
    fig.tight_layout()
    save_figure(fig, "f20_contour_pipeline")


if __name__ == "__main__":
    generate()
