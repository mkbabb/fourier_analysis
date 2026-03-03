"""F20: Image → contour → Fourier pipeline.

Referenced in §6.2. 4-panel showing: (a) original image, (b) edge
detection, (c) ordered contour path, (d) Fourier reconstruction.

Note: This figure requires an input image. If no image is available,
it generates a synthetic shape instead.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from fourier_analysis.epicycles import EpicycleChain
from fourier_analysis.figures.style import BLUE, RED, save_figure, setup_style


def generate(image_path: str | Path | None = None) -> None:
    setup_style()
    fig, axes = plt.subplots(2, 2, figsize=(10, 10))

    if image_path is not None:
        from fourier_analysis.contours import extract_contours
        from fourier_analysis.shortest_tour import order_contours

        contours = extract_contours(image_path, canny_sigma=2.0, resize=256)
        path = order_contours(contours)

        # (a) Original image
        from PIL import Image

        img = Image.open(image_path).convert("L")
        axes[0, 0].imshow(np.array(img), cmap="gray")
        axes[0, 0].set_title("(a) Original image")

        # (b) Edge detection
        from skimage import feature  # type: ignore[import-untyped]

        edges = feature.canny(np.array(img.resize((256, 256)), dtype=np.float64), sigma=2.0)
        axes[0, 1].imshow(edges, cmap="gray")
        axes[0, 1].set_title("(b) Canny edge detection")
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
    n_harmonics = min(100, len(path) // 2)
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
