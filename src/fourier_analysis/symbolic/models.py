"""Domain dataclasses for the symbolic Fourier engine."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FourierTerm:
    """One term in a Fourier series."""

    n: int
    coefficient: complex
    symbolic_expr: str | None  # sympy expression string for c_n as f(n)
    amplitude: float
    phase: float


@dataclass(frozen=True, slots=True)
class ClosedFormResult:
    """Complete result of a closed-form Fourier computation."""

    terms: list[FourierTerm]
    latex: str
    tier: str  # "symbolic" | "identified" | "spline"
    energy_captured: float
    domain: tuple[float, float]
    period: float
    original_points: dict[str, list[float]]  # {x: [...], y: [...]}
    reconstructed_points: dict[str, list[float]]  # {x: [...], y: [...]}
