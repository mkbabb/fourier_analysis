"""Simplification and budget truncation for Fourier series."""

from __future__ import annotations

import numpy as np

from fourier_analysis.symbolic.models import FourierTerm


def compute_energy(terms: list[FourierTerm]) -> float:
    """Total energy Σ|c_n|²."""
    return sum(t.amplitude ** 2 for t in terms)


def truncate_by_budget(terms: list[FourierTerm], budget: int) -> list[FourierTerm]:
    """Keep top *budget* terms by amplitude (always includes DC if present)."""
    if len(terms) <= budget:
        return terms

    # Separate DC term
    dc = [t for t in terms if t.n == 0]
    non_dc = [t for t in terms if t.n != 0]

    # Sort by amplitude
    non_dc.sort(key=lambda t: t.amplitude, reverse=True)

    remaining = budget - len(dc)
    kept = dc + non_dc[:remaining]
    # Re-sort by index for display
    kept.sort(key=lambda t: (abs(t.n), -t.n))
    return kept


def simplify_series(
    terms: list[FourierTerm],
    budget: int,
    notation: str = "trig",
) -> tuple[str, float]:
    """Truncate terms by budget and compute energy fraction.

    Parameters
    ----------
    terms : list[FourierTerm]
        All computed terms.
    budget : int
        Maximum terms to keep.
    notation : str
        Notation mode for rendering (passed through).

    Returns
    -------
    tuple[str, float]
        (latex_string, energy_fraction) where energy_fraction is the
        fraction of total Σ|c_n|² captured by the kept terms.
    """
    from fourier_analysis.symbolic.latex_rendering import render_latex

    total_energy = compute_energy(terms)
    kept = truncate_by_budget(terms, budget)
    kept_energy = compute_energy(kept)

    energy_fraction = kept_energy / total_energy if total_energy > 0 else 1.0

    latex = render_latex(kept, notation, budget)
    return latex, energy_fraction


def compute_effective_n(
    terms: list[FourierTerm],
    threshold: float = 0.999,
    minimum: int = 3,
) -> int:
    """Find the minimum number of harmonics capturing ≥ threshold of total energy.

    Groups ±n pairs so each unique |n| is counted once.  Returns at least
    *minimum* harmonics for visual utility even if the series converges
    faster.
    """
    total_energy = compute_energy(terms)
    if total_energy <= 0:
        return minimum

    # Group energy by |n|
    energy_by_k: dict[int, float] = {}
    for t in terms:
        k = abs(t.n)
        energy_by_k[k] = energy_by_k.get(k, 0) + t.amplitude ** 2

    dc_energy = energy_by_k.pop(0, 0)
    cumulative = dc_energy
    max_k = max(energy_by_k.keys()) if energy_by_k else 1

    for k in sorted(energy_by_k.keys()):
        cumulative += energy_by_k[k]
        if cumulative / total_energy >= threshold:
            return max(minimum, k)

    return max(minimum, max_k)


def simplify_numerical_coefficients(
    coefficients: list[dict],
    budget: int = 6,
    notation: str = "trig",
) -> tuple[str, float, int]:
    """Simplify raw numerical DFT coefficients for display.

    Used by the 2D visualizer to show a simplified equation overlay.

    Parameters
    ----------
    coefficients : list[dict]
        Each dict has: n, coefficient_re, coefficient_im, amplitude, phase.
    budget : int
        Max terms to display.
    notation : str
        "trig", "exponential", or "polar".

    Returns
    -------
    tuple[str, float, int]
        (latex, energy_captured, term_count).
    """
    terms = [
        FourierTerm(
            n=c["n"],
            coefficient=complex(c["coefficient_re"], c["coefficient_im"]),
            symbolic_expr=None,
            amplitude=c["amplitude"],
            phase=c["phase"],
        )
        for c in coefficients
    ]

    latex, energy = simplify_series(terms, budget, notation)
    kept = truncate_by_budget(terms, budget)
    return latex, energy, len(kept)
