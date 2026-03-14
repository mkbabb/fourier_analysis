"""Tests for fourier_analysis.contour_ml."""

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from fourier_analysis.contours import ContourStrategy, ContourConfig


def _save_image(arr: np.ndarray, path: Path) -> Path:
    """Save a numpy array as a grayscale PNG."""
    img = Image.fromarray(arr.astype(np.uint8), mode="L")
    img.save(path)
    return path


class TestContourML:
    def test_ml_enum_exists(self):
        """ContourStrategy.ML should be a valid enum member."""
        assert ContourStrategy.ML.value == "ml"

    def test_config_ml_fields(self):
        """ContourConfig should have ml_threshold and ml_detail_threshold."""
        config = ContourConfig()
        assert config.ml_threshold == 0.5
        assert config.ml_detail_threshold == 0.3

    def test_config_normalized_clamps_ml(self):
        """Normalized config should clamp ML thresholds to [0, 1]."""
        config = ContourConfig(ml_threshold=1.5, ml_detail_threshold=-0.1)
        normed = config.normalized()
        assert normed.ml_threshold == 1.0
        assert normed.ml_detail_threshold == 0.0

    def test_explicit_ml_strategy_import(self):
        """ML strategy should be dispatchable."""
        from fourier_analysis.contours.extraction import _select_explicit_candidate
        assert ContourStrategy.ML.value == "ml"

    def test_auto_uses_ml_isolation(self, tmp_path: Path):
        """AUTO pipeline should use ML for subject isolation."""
        from fourier_analysis.contours import extract_contours_result

        size = 128
        arr = np.zeros((size, size), dtype=np.uint8)
        arr[30:100, 30:100] = 200
        img_path = _save_image(arr, tmp_path / "test.png")

        result = extract_contours_result(img_path, strategy="auto", resize=None)
        assert isinstance(result.contours, list)
        # Pipeline should produce contours via ML-guided isolation.
        assert result.diagnostics.selected_candidate == "pipeline"

    def test_ml_masks_returns_multiple_thresholds(self, tmp_path: Path):
        """ml_masks should return multiple nested masks at different thresholds."""
        from fourier_analysis.contours.image import load_image_inputs
        from fourier_analysis.contours.ml import ml_masks

        # Use a real image for meaningful saliency
        portraits = Path(__file__).resolve().parents[1] / "assets" / "portraits"
        img_path = portraits / "joseph-fourier.png"
        if not img_path.exists():
            pytest.skip("Portrait assets not available")

        config = ContourConfig().normalized()
        image = load_image_inputs(img_path, config)
        masks = ml_masks(image, config)

        assert len(masks) >= 2, "ML should produce multiple iso-probability masks"
        # Masks should be nested: broader mask contains tighter ones
        for i in range(1, len(masks)):
            broader = np.count_nonzero(masks[i - 1])
            tighter = np.count_nonzero(masks[i])
            assert broader >= tighter
