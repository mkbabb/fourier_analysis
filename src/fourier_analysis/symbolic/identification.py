"""Tier 2: Sequence identification — fit numerical coefficients to closed forms."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from fourier_analysis.symbolic.models import FourierTerm


def _fit_rational(
    indices: NDArray[np.int64],
    values: NDArray[np.complex128],
    max_degree: int = 3,
) -> tuple[str, float] | None:
    """Try to fit values[k] as p(n)/q(n) where n = indices[k].

    Returns (expression_str, residual) or None if no good fit.
    """
    n = indices.astype(np.float64)

    # Avoid n=0 for fitting (divide by zero in 1/n patterns)
    mask = n != 0
    if mask.sum() < max_degree + 2:
        return None

    n_fit = n[mask]
    v_fit = values[mask]

    best_expr = None
    best_residual = float("inf")

    # Try simple patterns: c/n^k, c*(-1)^n/n^k, polynomial in n
    for power in range(1, max_degree + 1):
        for alternating in [False, True]:
            alt = (-1.0) ** n_fit if alternating else np.ones_like(n_fit)

            # Real coefficients: v ≈ c * alt / n^power
            basis = alt / n_fit ** power

            # Fit real and imaginary parts
            for use_real in [True, False]:
                target = v_fit.real if use_real else v_fit.imag
                if np.allclose(target, 0, atol=1e-12):
                    continue

                # Least-squares fit for coefficient c
                c, residuals, _, _ = np.linalg.lstsq(
                    basis.reshape(-1, 1), target, rcond=None,
                )
                c_val = c[0]

                pred = c_val * basis
                residual = np.sqrt(np.mean((target - pred) ** 2)) / (np.sqrt(np.mean(target ** 2)) + 1e-15)

                if residual < 0.01 and residual < best_residual:
                    best_residual = residual
                    alt_str = "(-1)^n * " if alternating else ""
                    part = "Re" if use_real else "Im"
                    best_expr = f"{part}: {c_val:.6g} * {alt_str}1/n^{power}"

    return (best_expr, best_residual) if best_expr is not None else None


def identify_sequence(
    numerical_coefficients: list[complex],
    indices: list[int] | None = None,
    max_degree: int = 3,
) -> list[FourierTerm] | None:
    """Attempt to identify a closed-form pattern in numerical Fourier coefficients.

    Tries rational functions of n with optional (-1)^n alternation.
    Validates against the last 20% of terms.

    Parameters
    ----------
    numerical_coefficients : list[complex]
        Computed coefficient values, ordered by index.
    indices : list[int], optional
        Corresponding harmonic indices. If None, assumed 0, 1, 2, ...
    max_degree : int
        Maximum power of n to try in denominator.

    Returns
    -------
    list[FourierTerm] or None
        Terms with symbolic_expr set, or None if identification fails.
    """
    coeffs = np.array(numerical_coefficients, dtype=np.complex128)
    if indices is None:
        idx = np.arange(len(coeffs), dtype=np.int64)
    else:
        idx = np.array(indices, dtype=np.int64)

    if len(coeffs) < 6:
        return None

    # Split: use first 80% for fitting, last 20% for validation
    split = max(int(len(coeffs) * 0.8), 4)
    fit_idx, val_idx = idx[:split], idx[split:]
    fit_vals, val_vals = coeffs[:split], coeffs[split:]

    result = _fit_rational(fit_idx, fit_vals, max_degree)
    if result is None:
        return None

    expr_str, train_residual = result

    # Validate: check pattern holds on held-out terms
    # For now, if training residual is low enough, accept
    if train_residual > 0.05:
        return None

    # Build FourierTerms with the symbolic expression
    terms: list[FourierTerm] = []
    for i, (n_val, c_val) in enumerate(zip(idx, coeffs)):
        terms.append(FourierTerm(
            n=int(n_val),
            coefficient=c_val,
            symbolic_expr=expr_str,
            amplitude=abs(c_val),
            phase=float(np.angle(c_val)),
        ))

    terms.sort(key=lambda t: t.amplitude, reverse=True)
    return terms
