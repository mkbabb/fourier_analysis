"""Fourier Analysis — companion code for 'An Introduction to Fourier Analysis'."""

from fourier_analysis.series import fourier_coefficients, fourier_reconstruct, partial_sum
from fourier_analysis.epicycles import EpicycleComponent, EpicycleChain
from fourier_analysis.bases import (
    BasisComponent,
    BasisDecomposition,
    CurveApproximation,
    approximate_curve,
)

__all__ = [
    "fourier_coefficients",
    "fourier_reconstruct",
    "partial_sum",
    "EpicycleComponent",
    "EpicycleChain",
    "BasisComponent",
    "BasisDecomposition",
    "CurveApproximation",
    "approximate_curve",
]
