"""Generalized eigenbasis decomposition for parametric curves.

Extends the Fourier-only pipeline with Chebyshev and Legendre polynomial
bases, enabling side-by-side comparison of how different orthogonal systems
approximate the same contour.

Algorithm
---------
Contour points (complex) -> separate to real x/y -> map t in [0,1) to
s in [-1,1] -> ``Chebyshev.fit(s, x, deg)`` -> ``.convert(kind=Legendre)``.
NumPy's built-in conversion (via monomial basis) is O(N^2) but stable
for N <= ~500.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.polynomial import chebyshev, legendre
from numpy.typing import NDArray

from fourier_analysis.series import fourier_coefficients


@dataclass(frozen=True, slots=True)
class BasisComponent:
    """One term in a basis expansion: c_k * phi_k(t)."""

    index: int
    coefficient: complex
    amplitude: float
    phase: float


@dataclass(frozen=True, slots=True)
class BasisDecomposition:
    """Complete decomposition of a signal or curve component in one basis."""

    basis: str
    components: list[BasisComponent]
    domain: tuple[float, float]


@dataclass(frozen=True, slots=True)
class CurveApproximation:
    """Decomposition of a parametric curve in multiple bases."""

    x: dict[str, BasisDecomposition]
    y: dict[str, BasisDecomposition]
    fourier: BasisDecomposition
    n_points: int
    max_degree: int


def _make_component(index: int, coeff: complex) -> BasisComponent:
    return BasisComponent(
        index=index,
        coefficient=coeff,
        amplitude=abs(coeff),
        phase=float(np.angle(coeff)),
    )


def fourier_decomposition(
    signal: NDArray[np.complexfloating] | NDArray[np.floating],
    n_harmonics: int | None = None,
) -> BasisDecomposition:
    """Decompose a complex signal into Fourier basis components."""
    coeffs = fourier_coefficients(signal, n_harmonics=n_harmonics)
    N = len(signal)
    nh = n_harmonics if n_harmonics is not None else N // 2

    components: list[BasisComponent] = []
    # DC term
    components.append(_make_component(0, complex(coeffs[0])))
    # Positive and negative frequencies
    for k in range(1, nh + 1):
        if k < len(coeffs):
            components.append(_make_component(k, complex(coeffs[k])))
        neg_idx = -k % N if n_harmonics is None else len(coeffs) - k
        if 0 < neg_idx < len(coeffs) and neg_idx != k:
            components.append(_make_component(-k, complex(coeffs[neg_idx])))

    components.sort(key=lambda c: c.amplitude, reverse=True)
    return BasisDecomposition(basis="fourier", components=components, domain=(0.0, 1.0))


def chebyshev_fit(
    signal: NDArray[np.floating],
    degree: int,
) -> NDArray[np.float64]:
    """Fit a real signal to Chebyshev polynomials of the first kind.

    Parameters
    ----------
    signal : 1-D real array
        Sampled values.
    degree : int
        Maximum polynomial degree.

    Returns
    -------
    NDArray[float64]
        Chebyshev coefficients c_0 .. c_degree.
    """
    n = len(signal)
    s = np.linspace(-1, 1, n)
    fit = chebyshev.Chebyshev.fit(s, signal, deg=degree, domain=[-1, 1])
    return np.asarray(fit.coef, dtype=np.float64)


def legendre_from_chebyshev(
    cheb_coeffs: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Convert Chebyshev coefficients to Legendre coefficients.

    Uses NumPy's polynomial conversion: Chebyshev -> Legendre via the
    monomial basis as intermediate.
    """
    cheb = chebyshev.Chebyshev(cheb_coeffs, domain=[-1, 1])
    leg = cheb.convert(kind=legendre.Legendre)
    return np.asarray(leg.coef, dtype=np.float64)


def _real_decomposition(
    signal: NDArray[np.floating],
    degree: int,
    basis_name: str,
    coeffs: NDArray[np.float64],
) -> BasisDecomposition:
    """Build a BasisDecomposition from real polynomial coefficients."""
    components = [_make_component(k, complex(c)) for k, c in enumerate(coeffs)]
    components.sort(key=lambda c: c.amplitude, reverse=True)
    domain = (-1.0, 1.0)
    return BasisDecomposition(basis=basis_name, components=components, domain=domain)


def chebyshev_decomposition(
    signal: NDArray[np.floating],
    degree: int,
) -> BasisDecomposition:
    """Decompose a real signal into Chebyshev basis."""
    coeffs = chebyshev_fit(signal, degree)
    return _real_decomposition(signal, degree, "chebyshev", coeffs)


def legendre_decomposition(
    signal: NDArray[np.floating],
    degree: int,
) -> BasisDecomposition:
    """Decompose a real signal into Legendre basis."""
    cheb_coeffs = chebyshev_fit(signal, degree)
    leg_coeffs = legendre_from_chebyshev(cheb_coeffs)
    return _real_decomposition(signal, degree, "legendre", leg_coeffs)


def approximate_curve(
    contour_points: NDArray[np.complex128],
    max_degree: int,
    n_harmonics: int | None = None,
) -> CurveApproximation:
    """Full pipeline: decompose a complex contour into all 3 bases.

    Parameters
    ----------
    contour_points : 1-D complex array
        Contour as complex numbers (x + iy).
    max_degree : int
        Maximum polynomial degree for Chebyshev/Legendre.
    n_harmonics : int, optional
        Number of Fourier harmonics. Defaults to max_degree.

    Returns
    -------
    CurveApproximation
    """
    if n_harmonics is None:
        n_harmonics = max_degree

    x_signal = contour_points.real.astype(np.float64)
    y_signal = contour_points.imag.astype(np.float64)

    fourier = fourier_decomposition(contour_points, n_harmonics=n_harmonics)

    x_decomps: dict[str, BasisDecomposition] = {}
    y_decomps: dict[str, BasisDecomposition] = {}

    for name, decomp_fn in [("chebyshev", chebyshev_decomposition), ("legendre", legendre_decomposition)]:
        x_decomps[name] = decomp_fn(x_signal, max_degree)
        y_decomps[name] = decomp_fn(y_signal, max_degree)

    return CurveApproximation(
        x=x_decomps,
        y=y_decomps,
        fourier=fourier,
        n_points=len(contour_points),
        max_degree=max_degree,
    )


def evaluate_partial_sum(
    decomposition: BasisDecomposition,
    degree: int,
    n_eval: int = 1000,
) -> NDArray[np.float64 | np.complex128]:
    """Evaluate a truncated series at evenly spaced points.

    Parameters
    ----------
    decomposition : BasisDecomposition
        The basis decomposition to evaluate.
    degree : int
        Number of terms to include.
    n_eval : int
        Number of evaluation points.

    Returns
    -------
    NDArray
        Evaluated values. Complex for Fourier, real for polynomial bases.
    """
    basis = decomposition.basis

    # Collect coefficients up to `degree`
    coeff_dict: dict[int, complex] = {}
    for comp in decomposition.components:
        if basis == "fourier":
            if abs(comp.index) <= degree:
                coeff_dict[comp.index] = comp.coefficient
        else:
            if 0 <= comp.index <= degree:
                coeff_dict[comp.index] = comp.coefficient

    if basis == "fourier":
        t = np.linspace(0, 1, n_eval, endpoint=False)
        result = np.zeros(n_eval, dtype=np.complex128)
        for k, c in coeff_dict.items():
            result += c * np.exp(2j * np.pi * k * t)
        return result

    # Polynomial bases
    s = np.linspace(-1, 1, n_eval)
    max_k = max(coeff_dict.keys()) if coeff_dict else 0
    coeffs_arr = np.zeros(max_k + 1, dtype=np.float64)
    for k, c in coeff_dict.items():
        coeffs_arr[k] = c.real

    if basis == "chebyshev":
        return chebyshev.chebval(s, coeffs_arr)
    elif basis == "legendre":
        return legendre.legval(s, coeffs_arr)
    else:
        raise ValueError(f"Unknown basis: {basis!r}")


def build_animation_data(
    contour_points: NDArray[np.complex128],
    max_degree: int,
    levels: list[int] | None = None,
    n_eval: int = 1000,
) -> dict:
    """Precompute all partial sums for frontend transfer.

    Parameters
    ----------
    contour_points : 1-D complex array
    max_degree : int
    levels : list of int, optional
        Truncation levels to precompute. Defaults to a geometric progression.
    n_eval : int
        Evaluation points per partial sum.

    Returns
    -------
    dict
        Serializable dictionary with original path, decompositions, and
        partial sums at each level for each basis.
    """
    if levels is None:
        levels = _default_levels(max_degree)

    approx = approximate_curve(contour_points, max_degree)

    partial_sums: dict[str, dict[int, dict[str, list[float]]]] = {}

    # Fourier partial sums (complex -> x, y)
    partial_sums["fourier"] = {}
    for n in levels:
        vals = evaluate_partial_sum(approx.fourier, n, n_eval)
        partial_sums["fourier"][n] = {
            "x": vals.real.tolist(),
            "y": vals.imag.tolist(),
        }

    # Polynomial basis partial sums
    for basis_name in ("chebyshev", "legendre"):
        partial_sums[basis_name] = {}
        for n in levels:
            x_vals = evaluate_partial_sum(approx.x[basis_name], n, n_eval)
            y_vals = evaluate_partial_sum(approx.y[basis_name], n, n_eval)
            partial_sums[basis_name][n] = {
                "x": x_vals.tolist(),
                "y": y_vals.tolist(),
            }

    # Serialize decompositions
    decompositions = {}
    decompositions["fourier"] = _serialize_decomposition(approx.fourier)
    for basis_name in ("chebyshev", "legendre"):
        decompositions[f"{basis_name}_x"] = _serialize_decomposition(approx.x[basis_name])
        decompositions[f"{basis_name}_y"] = _serialize_decomposition(approx.y[basis_name])

    return {
        "original": {
            "x": contour_points.real.tolist(),
            "y": contour_points.imag.tolist(),
        },
        "decompositions": decompositions,
        "partial_sums": partial_sums,
        "eval_points": np.linspace(0, 1, n_eval, endpoint=False).tolist(),
        "levels": levels,
    }


def _default_levels(max_degree: int) -> list[int]:
    """Generate a geometric progression of truncation levels."""
    levels = set()
    k = 1
    while k <= max_degree:
        levels.add(k)
        k = max(k + 1, int(k * 1.5))
    levels.add(max_degree)
    return sorted(levels)


def _serialize_decomposition(decomp: BasisDecomposition) -> dict:
    """Convert a BasisDecomposition to a JSON-serializable dict."""
    return {
        "basis": decomp.basis,
        "domain": list(decomp.domain),
        "components": [
            {
                "index": c.index,
                "coefficient": [c.coefficient.real, c.coefficient.imag],
                "amplitude": c.amplitude,
                "phase": c.phase,
            }
            for c in decomp.components
        ],
    }
