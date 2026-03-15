from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from PIL import Image, ImageOps
from skimage import color as skcolor, exposure, filters

from fourier_analysis.contours.models import ContourConfig


@dataclass(frozen=True)
class LoadedImage:
    """Normalized image data shared across contour candidates."""

    grayscale: NDArray[np.float64]
    detail_grayscale: NDArray[np.float64]
    edge_grayscale: NDArray[np.float64]
    color_gradient: NDArray[np.float64]  # max gradient across color channels
    alpha: NDArray[np.float64] | None
    alpha_subject_std: float | None
    image_area: float
    diagonal: float
    source_path: Path | None = None


def load_image_inputs(
    image_path: str | Path,
    config: ContourConfig,
) -> LoadedImage:
    """Load and normalize grayscale/alpha inputs for contour extraction."""
    img_raw = Image.open(image_path)
    img_raw = ImageOps.exif_transpose(img_raw)

    alpha_arr: NDArray[np.float64] | None = None
    if img_raw.mode in ("RGBA", "LA", "PA"):
        alpha_arr = np.array(img_raw.split()[-1], dtype=np.float64) / 255.0
        opaque_frac = float(np.mean(alpha_arr > 0.5))
        if opaque_frac < 0.01 or opaque_frac > 0.99:
            alpha_arr = None

    # Compute color gradient before converting to grayscale.
    img_rgb = img_raw.convert("RGB")
    img = img_raw.convert("L")
    if config.resize is not None:
        ratio = config.resize / max(img.size)
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        img_rgb = img_rgb.resize(new_size, Image.Resampling.LANCZOS)
        if alpha_arr is not None:
            alpha_img = Image.fromarray((alpha_arr * 255).astype(np.uint8))
            alpha_img = alpha_img.resize(new_size, Image.Resampling.LANCZOS)
            alpha_arr = np.array(alpha_img, dtype=np.float64) / 255.0

    # Perceptual color gradient in CIELAB space.
    # L*a*b* is perceptually uniform — the b* channel (blue↔yellow axis)
    # produces huge gradients at color boundaries invisible in grayscale.
    rgb = np.array(img_rgb, dtype=np.float64) / 255.0
    lab = skcolor.rgb2lab(rgb)
    lab_norm = np.empty_like(lab)
    lab_norm[:, :, 0] = lab[:, :, 0] / 100.0          # L*: [0,100] → [0,1]
    lab_norm[:, :, 1] = (lab[:, :, 1] + 128.0) / 256.0  # a*: [-128,128] → [0,1]
    lab_norm[:, :, 2] = (lab[:, :, 2] + 128.0) / 256.0  # b*: [-128,128] → [0,1]
    channel_grads = [filters.sobel(lab_norm[:, :, ch]) for ch in range(3)]
    color_gradient = np.maximum.reduce(channel_grads)

    grayscale = np.array(img, dtype=np.float64)
    gray_max = float(grayscale.max())
    if gray_max > 0:
        grayscale = grayscale / gray_max

    # Edge-aware path: light blur (capped at 1.0) + optional CLAHE
    edge_sigma = min(config.blur_sigma, 1.0)
    edge_gray = filters.gaussian(grayscale, sigma=edge_sigma) if edge_sigma > 0 else grayscale.copy()
    if config.contrast_enhance:
        try:
            edge_gray = exposure.equalize_adapthist(edge_gray, clip_limit=0.03)
        except ValueError:
            pass

    # Standard path: full blur for threshold-based strategies
    if config.blur_sigma > 0:
        grayscale = filters.gaussian(grayscale, sigma=config.blur_sigma)

    detail_grayscale = _detail_enhanced_grayscale(grayscale)

    alpha_subject_std: float | None = None
    if alpha_arr is not None and np.any(alpha_arr > 0.5):
        alpha_subject_std = float(np.std(grayscale[alpha_arr > 0.5]))

    image_area = float(grayscale.shape[0] * grayscale.shape[1])
    diagonal = float(np.hypot(grayscale.shape[0], grayscale.shape[1]))
    return LoadedImage(
        grayscale=grayscale,
        detail_grayscale=detail_grayscale,
        edge_grayscale=edge_gray,
        color_gradient=color_gradient,
        alpha=alpha_arr,
        alpha_subject_std=alpha_subject_std,
        image_area=image_area,
        diagonal=diagonal,
        source_path=Path(image_path),
    )


def _detail_enhanced_grayscale(
    grayscale: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Local contrast enhancement to reveal subtle features.

    Uses CLAHE to amplify subtle intensity transitions (eyes, nose,
    mouth, folds) for better contour extraction.
    """
    if min(grayscale.shape) < 32:
        return grayscale

    try:
        equalized = exposure.equalize_adapthist(grayscale, clip_limit=0.04)
    except ValueError:
        return grayscale
    return np.clip(0.3 * grayscale + 0.7 * equalized, 0.0, 1.0)
