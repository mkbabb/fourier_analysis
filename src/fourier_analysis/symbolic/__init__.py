"""Symbolic Fourier computation engine.

Provides closed-form Fourier series computation via three tiers:
  1. Symbolic integration (sympy)
  2. Sequence identification (rational fitting)
  3. Spline approximation (cubic spline + exact IBP)
"""

from __future__ import annotations

from fourier_analysis.symbolic.models import ClosedFormResult, FourierTerm
from fourier_analysis.symbolic.parsing import parse_expression
from fourier_analysis.symbolic.integration import symbolic_fourier_coefficients
from fourier_analysis.symbolic.spline import spline_fourier_coefficients
from fourier_analysis.symbolic.identification import identify_sequence
from fourier_analysis.symbolic.simplification import simplify_series, compute_effective_n
from fourier_analysis.symbolic.latex_rendering import render_latex, render_latex_sigma

__all__ = [
    "FourierTerm",
    "ClosedFormResult",
    "parse_expression",
    "symbolic_fourier_coefficients",
    "spline_fourier_coefficients",
    "identify_sequence",
    "simplify_series",
    "compute_effective_n",
    "render_latex",
    "render_latex_sigma",
]
