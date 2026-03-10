"""Contour extraction from images.

Extracts edge contours from images and represents them as complex-valued
paths suitable for Fourier analysis. The pipeline replaces the old Canny +
greedy nearest-neighbor pixel walk with marching squares via
``skimage.measure.find_contours``, which produces properly ordered, closed
contour paths natively---no post-hoc stitching required.

Four strategies are available:

- **THRESHOLD** (Otsu binarization): best for portraits and high-contrast
  silhouettes where a clean foreground/background split exists.
- **MULTI_THRESHOLD** (multi-Otsu): partitions the histogram into *n*
  classes and extracts contours at each level boundary. Captures interior
  detail that a single threshold obliterates---essential for images with
  mid-tone structure (mechanical parts, shaded illustrations).
- **CANNY** (Canny edges + morphological closing): best for line drawings
  and images with subtle gradients.
- **AUTO** (default): uses MULTI_THRESHOLD, which subsumes plain
  THRESHOLD while also capturing interior detail when it exists.
  For images with an alpha channel (transparent PNGs), the alpha mask
  is used directly for a clean extraction.

Post-extraction filtering and smoothing:

- **min_contour_area**: discard contours whose enclosed area is below a
  fraction of the image area (removes background noise).
- **max_contours**: keep only the *N* largest contours by area.
- **smooth_contours**: apply Savitzky--Golay smoothing to contour paths
  before resampling, reducing jaggedness from texture edges.

Arc-length resampling uses cubic interpolation for smoother output.

Used in the epicycle image-tracing pipeline (§6.2).
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from PIL import Image
from scipy.interpolate import interp1d  # type: ignore[import-untyped]
from scipy.signal import savgol_filter  # type: ignore[import-untyped]
from skimage import feature, filters, measure, morphology  # type: ignore[import-untyped]


class ContourStrategy(Enum):
    """Strategy for contour extraction.

    THRESHOLD uses Otsu's method to binarize, then marching squares.
    MULTI_THRESHOLD uses multi-Otsu to partition the histogram into
    *n* classes and extracts contours at every level boundary.
    CANNY uses Canny edge detection + morphological closing, then marching squares.
    AUTO picks whichever suits the image's histogram.
    """

    THRESHOLD = "threshold"
    MULTI_THRESHOLD = "multi_threshold"
    CANNY = "canny"
    AUTO = "auto"


def _bimodality_coefficient(data: NDArray[np.floating]) -> float:
    """Compute the bimodality coefficient of a 1-D distribution.

    BC = (skewness^2 + 1) / kurtosis, where kurtosis here is the
    *excess* kurtosis + 3 (i.e., the regular kurtosis). A value > 0.555
    suggests bimodality---meaning Otsu thresholding is likely to produce
    a clean split.
    """
    n = len(data)
    if n < 4:
        return 0.0
    mean = np.mean(data)
    centered = data - mean
    m2 = np.mean(centered**2)
    if m2 < 1e-12:
        return 0.0
    m3 = np.mean(centered**3)
    m4 = np.mean(centered**4)
    skew = m3 / (m2**1.5)
    kurt = m4 / (m2**2)  # regular (not excess) kurtosis
    return float((skew**2 + 1) / kurt)


def _find_contours_padded(
    binary: NDArray[np.bool_],
    pad: int = 1,
) -> list[NDArray[np.floating]]:
    """Find contours on a binary mask, padding edges so border-touching
    shapes produce closed contours.

    ``skimage.measure.find_contours`` cannot close a contour that exits
    the image boundary — it returns two open segments instead. Padding
    the mask with a 1-pixel ring of ``False`` guarantees every shape
    boundary is fully enclosed, yielding proper closed contours. The
    coordinates are shifted back to the original frame afterwards.
    """
    padded = np.pad(binary, pad, mode="constant", constant_values=False)
    raw = measure.find_contours(padded.astype(float), level=0.5)
    # Shift coordinates back to the original image frame
    return [rc - pad for rc in raw]


def extract_contours(
    image_path: str | Path,
    *,
    strategy: ContourStrategy | str = ContourStrategy.AUTO,
    resize: int | None = 512,
    min_contour_length: int = 40,
    blur_sigma: float = 1.0,
    canny_sigma: float = 2.0,
    closing_radius: int = 3,
    n_classes: int = 3,
    min_contour_area: float = 0.0,
    max_contours: int | None = None,
    smooth_contours: float = 0.0,
) -> list[NDArray[np.complex128]]:
    """Extract edge contours from an image as complex paths.

    The heavy lifting is done by ``skimage.measure.find_contours``
    (marching squares), which returns contours that are *already ordered*
    as closed polylines---a massive improvement over the old scatter-then-
    stitch approach.

    Parameters
    ----------
    image_path : str or Path
        Path to the input image.
    strategy : ContourStrategy or str
        Extraction strategy. ``"auto"`` (default) inspects the histogram
        to pick THRESHOLD or MULTI_THRESHOLD automatically.
    resize : int, optional
        Resize the longest dimension to this value. ``None`` to skip.
    min_contour_length : int
        Discard contours with fewer points than this.
    blur_sigma : float
        Gaussian smoothing sigma applied before thresholding/edge
        detection. Merges fine texture into broad tonal regions,
        suppressing the tiny spurious contours that plague painted
        portraits under multi-Otsu. Set to 0 to disable.
    canny_sigma : float
        Gaussian sigma for Canny edge detection (CANNY strategy only).
    closing_radius : int
        Disk radius for morphological closing (CANNY strategy only).
    n_classes : int
        Number of intensity classes for MULTI_THRESHOLD (default 3).
    min_contour_area : float
        Minimum enclosed area as a fraction of total image area. Contours
        smaller than this are discarded. 0 disables filtering.
    max_contours : int or None
        Keep only the *N* largest contours by enclosed area. ``None``
        keeps all contours that pass the area filter.
    smooth_contours : float
        Savitzky--Golay smoothing strength (0--1). 0 disables. The value
        controls the window length as a fraction of contour length.

    Returns
    -------
    list of NDArray[complex128]
        Each array is a contour represented as complex numbers
        ``(col - cx) + 1j * (cy - row)``, centered and y-flipped.
    """
    if isinstance(strategy, str):
        strategy = ContourStrategy(strategy.lower())

    # Validate and clamp parameters
    blur_sigma = max(0.0, blur_sigma)
    min_contour_area = max(0.0, min(1.0, min_contour_area))
    smooth_contours = max(0.0, min(1.0, smooth_contours))
    if max_contours is not None:
        max_contours = max(0, max_contours) or None  # 0 → None (no limit)

    img_raw = Image.open(image_path)

    # Detect usable alpha channel *before* converting to grayscale.
    # PNGs with transparency (logos, rendered text, graphics) have a
    # perfect built-in mask that beats any luminance-based threshold.
    # However, simple convex masks (circle crops, rounded rects) are just
    # crop artifacts — fall through to luminance extraction for those.
    has_alpha = img_raw.mode in ("RGBA", "LA", "PA")
    alpha_arr: NDArray[np.float64] | None = None
    if has_alpha:
        alpha_arr = np.array(img_raw.split()[-1], dtype=np.float64) / 255.0
        opaque_frac = np.mean(alpha_arr > 0.5)
        if opaque_frac < 0.01 or opaque_frac > 0.99:
            alpha_arr = None  # degenerate — fall through to luminance
        elif alpha_arr is not None:
            # Check if the alpha mask is a simple convex shape (circle crop,
            # rounded rectangle, etc.) by measuring circularity. High
            # circularity means the mask is just a crop artifact, not a
            # meaningful subject outline — fall through to luminance.
            _alpha_contours = measure.find_contours(
                (alpha_arr > 0.5).astype(float), level=0.5
            )
            if len(_alpha_contours) <= 2:
                # Single/double contour — check if it's convex-ish
                _ac = max(_alpha_contours, key=len) if _alpha_contours else None
                if _ac is not None and len(_ac) > 10:
                    _area = 0.5 * abs(
                        np.sum(
                            _ac[:, 1] * np.roll(_ac[:, 0], -1)
                            - np.roll(_ac[:, 1], -1) * _ac[:, 0]
                        )
                    )
                    _perim = np.sum(
                        np.sqrt(np.sum(np.diff(_ac, axis=0) ** 2, axis=1))
                    )
                    _circularity = (
                        4 * np.pi * _area / (_perim**2) if _perim > 0 else 0
                    )
                    if _circularity > 0.7:
                        alpha_arr = None  # simple crop mask

    img = img_raw.convert("L")

    if resize is not None:
        ratio = resize / max(img.size)
        new_size = (int(img.size[0] * ratio), int(img.size[1] * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        if alpha_arr is not None:
            alpha_img = Image.fromarray((alpha_arr * 255).astype(np.uint8))
            alpha_img = alpha_img.resize(new_size, Image.Resampling.LANCZOS)
            alpha_arr = np.array(alpha_img, dtype=np.float64) / 255.0

    arr = np.array(img, dtype=np.float64)

    # Normalize to [0, 1] for skimage
    arr_max = arr.max()
    if arr_max > 0:
        arr = arr / arr_max

    # Gaussian pre-blur: merges fine texture into broad tonal regions,
    # dramatically reducing the small spurious contours that multi-Otsu
    # picks up on painted portraits (Fourier, Cauchy, etc.).
    if blur_sigma > 0:
        arr = filters.gaussian(arr, sigma=blur_sigma)

    # Strategy dispatch
    is_auto = strategy == ContourStrategy.AUTO

    # AUTO with alpha channel: use the alpha mask directly
    if is_auto and alpha_arr is not None:
        binary = alpha_arr > 0.5
        raw_contours = _find_contours_padded(binary)
    elif is_auto or strategy == ContourStrategy.MULTI_THRESHOLD:
        try:
            thresholds = filters.threshold_multiotsu(arr, classes=n_classes)
        except ValueError:
            thresholds = np.array([filters.threshold_otsu(arr)])
        regions = np.digitize(arr, bins=thresholds)
        raw_contours = []
        for level in range(len(thresholds)):
            binary_level = (regions > level).astype(float)
            raw_contours.extend(measure.find_contours(binary_level, level=0.5))
    elif strategy == ContourStrategy.THRESHOLD:
        thresh = filters.threshold_otsu(arr)
        binary = arr < thresh  # foreground = dark pixels (portraits)
        raw_contours = _find_contours_padded(binary)
    else:  # CANNY
        edges = feature.canny(arr, sigma=canny_sigma)
        closed = morphology.closing(edges, morphology.disk(closing_radius))
        raw_contours = _find_contours_padded(closed)

    # Center coordinates and convert to complex
    cy, cx = arr.shape[0] / 2, arr.shape[1] / 2
    image_area = arr.shape[0] * arr.shape[1]
    area_threshold = min_contour_area * image_area

    # Build (contour, area) pairs for filtering and ranking
    candidates: list[tuple[NDArray[np.complex128], float]] = []

    for rc in raw_contours:
        if len(rc) < min_contour_length:
            continue
        # rc is (N, 2) with columns (row, col)
        rows, cols = rc[:, 0], rc[:, 1]
        z = (cols - cx) + 1j * (cy - rows)

        # Enclosed area via shoelace formula
        area = 0.5 * abs(
            np.sum(z.real * np.roll(z.imag, -1) - np.roll(z.real, -1) * z.imag)
        )

        if area_threshold > 0 and area < area_threshold:
            continue
        # Discard border-hugging contours (area ≥ 90% of image area)
        if area > 0.9 * image_area:
            continue

        # Savitzky-Golay smoothing
        if smooth_contours > 0 and len(z) >= 5:
            window = int(smooth_contours * len(z))
            window = max(5, window)
            if window % 2 == 0:
                window += 1
            window = min(window, len(z))
            if window % 2 == 0:
                window -= 1
            if window >= 5:
                z = savgol_filter(z.real, window, 3) + 1j * savgol_filter(z.imag, window, 3)

        candidates.append((z, area))

    # Sort by area descending and apply max_contours limit
    candidates.sort(key=lambda pair: pair[1], reverse=True)

    if max_contours is not None and max_contours > 0:
        candidates = candidates[:max_contours]

    return [z for z, _ in candidates]


def resample_arc_length(
    contour: NDArray[np.complex128],
    n_points: int,
) -> NDArray[np.complex128]:
    """Resample a contour to uniform arc-length spacing.

    The FFT assumes uniform sampling in the parameter domain. If the
    original contour has variable point density (common after marching
    squares), this resampling step ensures the Fourier coefficients
    aren't aliased by non-uniform spacing.

    Parameters
    ----------
    contour : NDArray[complex128]
        The input contour as complex numbers.
    n_points : int
        Number of uniformly spaced output points.

    Returns
    -------
    NDArray[complex128]
        Resampled contour with ``n_points`` points.
    """
    if len(contour) < 2:
        return contour

    # Cumulative arc length
    diffs = np.abs(np.diff(contour))
    arc = np.concatenate([[0.0], np.cumsum(diffs)])
    total_length = arc[-1]

    if total_length < 1e-12:
        return contour[:n_points] if len(contour) >= n_points else contour

    # Normalize to [0, 1]
    arc_norm = arc / total_length

    # Interpolate real and imaginary parts independently
    interp_re = interp1d(arc_norm, contour.real, kind="cubic")
    interp_im = interp1d(arc_norm, contour.imag, kind="cubic")

    t_uniform = np.linspace(0, 1, n_points, endpoint=False)
    return interp_re(t_uniform) + 1j * interp_im(t_uniform)
