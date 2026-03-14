"""Stage 1: Subject isolation via ML saliency + optional alpha intersection."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from skimage import measure

from fourier_analysis.contours.image import LoadedImage
from fourier_analysis.contours.models import ContourConfig
from fourier_analysis.contours.ml import _predict_probability_map
from fourier_analysis.contours.processing import _postprocess_raw_contours


@dataclass(frozen=True)
class SubjectIsolation:
    """Result of subject isolation: mask, saliency, and optional silhouette."""

    subject_mask: NDArray[np.bool_] | None
    saliency_map: NDArray[np.float64]
    silhouette: NDArray[np.complex128] | None
    silhouette_area: float


def isolate_subject(
    image: LoadedImage,
    config: ContourConfig,
) -> SubjectIsolation:
    """Isolate the primary subject using ML saliency and optional alpha.

    1. Run U2-Net to get a probability map.
    2. Threshold at config.ml_threshold to get a subject mask.
    3. If alpha exists with 5-98% coverage, intersect with mask.
    4. If mask coverage < 12%, disable it (ML failed to isolate).
    5. Extract largest contour of mask as silhouette.
    """
    saliency = _predict_probability_map(image)
    subject_mask: NDArray[np.bool_] = saliency >= config.ml_threshold

    # Intersect with alpha if available and meaningful.
    if image.alpha is not None:
        alpha_mask = image.alpha > 0.5
        alpha_coverage = float(np.mean(alpha_mask))
        if 0.05 < alpha_coverage < 0.98:
            combined = alpha_mask & subject_mask
            if float(np.mean(combined)) > 0.05:
                subject_mask = combined

    coverage = float(np.mean(subject_mask))

    # Extract silhouette from subject mask.
    silhouette: NDArray[np.complex128] | None = None
    silhouette_area = 0.0
    if coverage >= 0.01:
        raw_contours = measure.find_contours(subject_mask.astype(float), level=0.5)
        if raw_contours:
            processed, areas = _postprocess_raw_contours(raw_contours, image, config)
            if processed:
                silhouette = processed[0]
                silhouette_area = areas[0]

    # Disable mask if ML failed to isolate a meaningful subject.
    if coverage < 0.12:
        return SubjectIsolation(
            subject_mask=None,
            saliency_map=saliency,
            silhouette=silhouette,
            silhouette_area=silhouette_area,
        )

    return SubjectIsolation(
        subject_mask=subject_mask,
        saliency_map=saliency,
        silhouette=silhouette,
        silhouette_area=silhouette_area,
    )
