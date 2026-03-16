"""Tier 3: Cubic spline → exact integration by parts for Fourier coefficients."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from scipy.interpolate import CubicSpline

from fourier_analysis.symbolic.models import FourierTerm


def _spline_segment_integral(
    a_coeff: float, b_coeff: float, c_coeff: float, d_coeff: float,
    x0: float, x1: float, n: int, omega: float,
) -> complex:
    """Exact integral of (a + b*u + c*u² + d*u³) * e^{-inω(x0+u)} du over [0, x1-x0].

    Uses the closed-form for ∫ u^k e^{-iαu} du obtained by repeated IBP.
    """
    h = x1 - x0
    alpha = n * omega

    if abs(alpha) < 1e-14:
        # α ≈ 0: integral of polynomial
        val = (a_coeff * h
               + b_coeff * h ** 2 / 2
               + c_coeff * h ** 3 / 3
               + d_coeff * h ** 4 / 4)
        return complex(val)

    # Phase factor e^{-inωx0}
    phase = np.exp(-1j * alpha * x0)
    ia = 1j * alpha

    # ∫₀ʰ u^k e^{-iαu} du = I_k
    # I_0 = (1 - e^{-iαh}) / (iα)
    # I_k = (h^k e^{-iαh} - k I_{k-1}) / (-iα)   [IBP recurrence]
    eh = np.exp(-ia * h)

    I = [0j] * 4
    I[0] = (1.0 - eh) / ia
    for k in range(1, 4):
        I[k] = (h ** k * eh - k * I[k - 1]) / (-ia)

    # Combine: ∫ = phase * (a*I_0 + b*I_1 + c*I_2 + d*I_3)
    val = a_coeff * I[0] + b_coeff * I[1] + c_coeff * I[2] + d_coeff * I[3]
    return phase * val


def spline_fourier_coefficients(
    f_values: NDArray[np.floating],
    x_values: NDArray[np.floating],
    n_harmonics: int,
    period: float | None = None,
) -> list[FourierTerm]:
    """Compute Fourier coefficients via cubic spline integration.

    1. Fit a CubicSpline to (x_values, f_values)
    2. For each spline segment, compute the exact Fourier integral using IBP
    3. Sum over segments to get c_n

    Parameters
    ----------
    f_values : array
        Function values at sample points.
    x_values : array
        Sample points (must be sorted).
    n_harmonics : int
        Number of harmonics (positive and negative).
    period : float, optional
        Period T. Defaults to x_values[-1] - x_values[0].

    Returns
    -------
    list[FourierTerm]
        Sorted by amplitude (descending).
    """
    x = np.asarray(x_values, dtype=np.float64)
    y = np.asarray(f_values, dtype=np.float64)

    T = period if period is not None else float(x[-1] - x[0])
    omega = 2.0 * np.pi / T

    cs = CubicSpline(x, y)
    # cs.c has shape (4, n_segments) where cs.c[0] is the cubic coeff (highest power)
    # Polynomial on segment j: d*(u³) + c*(u²) + b*u + a   where u = x - x_j
    n_seg = len(x) - 1
    breakpoints = x

    terms: list[FourierTerm] = []

    for n_val in range(-n_harmonics, n_harmonics + 1):
        cn = 0j
        for j in range(n_seg):
            # cs.c columns: [d, c, b, a] for each segment (degree 3, 2, 1, 0)
            d_c = float(cs.c[0, j])
            c_c = float(cs.c[1, j])
            b_c = float(cs.c[2, j])
            a_c = float(cs.c[3, j])

            cn += _spline_segment_integral(
                a_c, b_c, c_c, d_c,
                breakpoints[j], breakpoints[j + 1],
                n_val, omega,
            )

        cn /= T
        terms.append(FourierTerm(
            n=n_val,
            coefficient=cn,
            symbolic_expr=None,
            amplitude=abs(cn),
            phase=float(np.angle(cn)),
        ))

    terms.sort(key=lambda t: t.amplitude, reverse=True)
    return terms
