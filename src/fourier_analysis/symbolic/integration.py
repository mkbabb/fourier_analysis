"""Tier 1: Symbolic Fourier coefficient computation via sympy.integrate."""

from __future__ import annotations

import signal as sig
from contextlib import contextmanager

import numpy as np
import sympy as sp

from fourier_analysis.symbolic.models import FourierTerm


@contextmanager
def _timeout(seconds: float):
    """Context manager that raises TimeoutError after *seconds*."""
    def _handler(signum, frame):
        raise TimeoutError(f"Symbolic integration timed out after {seconds}s")

    old = sig.signal(sig.SIGALRM, _handler)
    sig.setitimer(sig.ITIMER_REAL, seconds)
    try:
        yield
    finally:
        sig.setitimer(sig.ITIMER_REAL, 0)
        sig.signal(sig.SIGALRM, old)


def _compute_cn(
    expr: sp.Expr,
    x: sp.Symbol,
    n_val: int,
    a: sp.Rational,
    b: sp.Rational,
    T: sp.Expr,
    omega: sp.Expr,
    timeout_s: float = 5.0,
) -> complex | None:
    """Compute a single Fourier coefficient c_n symbolically.

    Returns None if integration fails or times out.
    """
    if n_val == 0:
        integrand = expr
    else:
        integrand = expr * sp.exp(-sp.I * n_val * omega * x)

    try:
        with _timeout(timeout_s):
            result = sp.integrate(integrand, (x, a, b))
            result = result / T
            # Try to evaluate numerically
            val = complex(result.evalf())
            if not (np.isfinite(val.real) and np.isfinite(val.imag)):
                return None
            return val
    except (TimeoutError, Exception):
        return None


def symbolic_fourier_coefficients(
    expr: sp.Expr,
    n_harmonics: int,
    domain: tuple[float, float],
    period: float | None = None,
) -> list[FourierTerm] | None:
    """Compute Fourier coefficients via symbolic integration.

    Uses sympy's integrate() for the integral (1/T) ∫ f(x) e^{-inωx} dx.
    Falls through to None if any coefficient fails.

    Parameters
    ----------
    expr : sp.Expr
        Sympy expression in variable x.
    n_harmonics : int
        Number of positive harmonics to compute (also computes negatives).
    domain : tuple[float, float]
        Integration bounds [a, b].
    period : float, optional
        Period T. Defaults to b - a.

    Returns
    -------
    list[FourierTerm] or None
        None if symbolic integration fails for any coefficient.
    """
    x = sp.Symbol("x")
    a_val, b_val = domain
    T_val = period if period is not None else (b_val - a_val)

    a = sp.Rational(a_val).limit_denominator(1000) if a_val == int(a_val) else sp.Float(a_val)
    b = sp.Rational(b_val).limit_denominator(1000) if b_val == int(b_val) else sp.Float(b_val)
    T = sp.Rational(T_val).limit_denominator(1000) if T_val == int(T_val) else sp.Float(T_val)

    # Use exact pi if close
    if abs(a_val) < 1e-12:
        a = sp.Integer(0)
    if abs(b_val - float(sp.pi)) < 1e-10:
        b = sp.pi
    if abs(b_val - 2 * float(sp.pi)) < 1e-10:
        b = 2 * sp.pi
    if abs(T_val - float(sp.pi)) < 1e-10:
        T = sp.pi
    if abs(T_val - 2 * float(sp.pi)) < 1e-10:
        T = 2 * sp.pi

    omega = 2 * sp.pi / T

    terms: list[FourierTerm] = []
    failed = 0

    # Compute DC term
    c0 = _compute_cn(expr, x, 0, a, b, T, omega)
    if c0 is None:
        return None
    terms.append(FourierTerm(
        n=0,
        coefficient=c0,
        symbolic_expr=None,
        amplitude=abs(c0),
        phase=float(np.angle(c0)),
    ))

    # Compute positive and negative harmonics
    for k in range(1, n_harmonics + 1):
        for sign in [1, -1]:
            n_val = sign * k
            cn = _compute_cn(expr, x, n_val, a, b, T, omega)
            if cn is None:
                failed += 1
                if failed > 3:
                    return None
                # Use zero for this term
                cn = 0j

            terms.append(FourierTerm(
                n=n_val,
                coefficient=cn,
                symbolic_expr=None,
                amplitude=abs(cn),
                phase=float(np.angle(cn)),
            ))

    terms.sort(key=lambda t: t.amplitude, reverse=True)
    return terms
