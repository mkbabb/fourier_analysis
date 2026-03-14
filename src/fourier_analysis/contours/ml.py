"""Salient object detection via U2-Net-lite ONNX for contour extraction."""

from __future__ import annotations

import hashlib
import threading
import urllib.request
from pathlib import Path

import numpy as np
from numpy.typing import NDArray
from PIL import Image

from fourier_analysis.contours.image import LoadedImage
from fourier_analysis.contours.models import ContourConfig

_MODEL_URL = (
    "https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2netp.onnx"
)
_MODEL_SHA256 = "309c8469258dda742793dce0ebea8e6dd393174f89934733ecc8b14c76f4ddd8"
_MODEL_INPUT_SIZE = 320

_CACHE_DIR = Path.home() / ".cache" / "fourier-analysis" / "models"

_session_lock = threading.Lock()
_session = None


def _model_path() -> Path:
    return _CACHE_DIR / "u2netp.onnx"


def ensure_model_downloaded() -> Path:
    """Download the U2-Net-lite ONNX weights if not already cached.

    Returns the path to the cached model file.
    """
    path = _model_path()
    if path.exists():
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest == _MODEL_SHA256:
            return path
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    urllib.request.urlretrieve(_MODEL_URL, tmp)  # noqa: S310
    digest = hashlib.sha256(tmp.read_bytes()).hexdigest()
    if digest != _MODEL_SHA256:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(
            f"SHA-256 mismatch for u2netp.onnx: expected {_MODEL_SHA256}, got {digest}"
        )
    tmp.rename(path)
    return path


def _get_session():
    """Lazy singleton ONNX inference session."""
    global _session
    if _session is not None:
        return _session
    with _session_lock:
        if _session is not None:
            return _session
        try:
            import onnxruntime as ort
        except ImportError as exc:
            raise ImportError(
                "onnxruntime is required for ML contour extraction. "
                "Install with: pip install onnxruntime"
            ) from exc

        model = ensure_model_downloaded()
        _session = ort.InferenceSession(
            str(model), providers=["CPUExecutionProvider"]
        )
        return _session


def _predict_probability_map(image: LoadedImage) -> NDArray[np.float64]:
    """Run U2-Net-lite and return a [0, 1] probability map at the input resolution."""
    session = _get_session()
    h, w = image.grayscale.shape

    # Load original RGB from source path — U²-Net was trained on color images.
    if image.source_path is not None:
        pil = Image.open(image.source_path).convert("RGB")
    else:
        # Fallback: grayscale → 3-channel
        pil = Image.fromarray((image.grayscale * 255).astype(np.uint8)).convert("RGB")

    pil = pil.resize((_MODEL_INPUT_SIZE, _MODEL_INPUT_SIZE), Image.Resampling.BILINEAR)
    blob = np.array(pil, dtype=np.float32) / 255.0
    # HWC -> NCHW
    blob = blob.transpose(2, 0, 1)[np.newaxis, ...]

    input_name = session.get_inputs()[0].name
    outputs = session.run(None, {input_name: blob})
    # First output is the primary saliency map: (1, 1, 320, 320).
    # U²-Net outputs are already sigmoided — do NOT apply sigmoid again.
    prob = outputs[0].squeeze().astype(np.float64)
    prob = np.clip(prob, 0.0, 1.0)

    # Resize back to original (post-config-resize) resolution.
    prob_pil = Image.fromarray((prob * 255).astype(np.uint8))
    prob_pil = prob_pil.resize((w, h), Image.Resampling.BILINEAR)
    return np.array(prob_pil, dtype=np.float64) / 255.0


def ml_masks(
    image: LoadedImage,
    config: ContourConfig,
) -> tuple[NDArray[np.bool_], ...]:
    """Salient object masks via U2-Net-lite.

    Generates nested iso-probability contours at multiple thresholds
    to capture both the overall silhouette and interior detail.
    """
    prob = _predict_probability_map(image)

    # Multiple thresholds on the saliency map — analogous to multi-Otsu
    # but on the probability map instead of grayscale intensity.
    thresholds = [
        config.ml_detail_threshold,   # broad: peripheral detail
        config.ml_threshold,          # primary silhouette
        min(0.85, config.ml_threshold + 0.2),  # tighter core
    ]
    # Optionally add a very tight threshold for prominent features
    if config.ml_threshold < 0.7:
        thresholds.append(min(0.92, config.ml_threshold + 0.35))

    thresholds = sorted(set(thresholds))

    masks: list[NDArray[np.bool_]] = []
    prev_count = -1
    for t in thresholds:
        mask = prob >= t
        count = int(np.count_nonzero(mask))
        # Skip if too small or nearly identical to the previous level
        if count < 0.005 * image.image_area:
            continue
        if prev_count > 0 and abs(count - prev_count) < 0.01 * image.image_area:
            continue
        masks.append(mask)
        prev_count = count

    return tuple(masks) if masks else (prob >= config.ml_threshold,)
