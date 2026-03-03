"""Epicycle representation of Fourier series.

An epicycle decomposition represents a periodic function as a chain of
rotating vectors (phasors) in the complex plane. Each vector has:
- frequency n (integer rotations per period)
- amplitude |c_n| (radius of the circle)
- phase arg(c_n) (initial angle)

This corresponds to the Fourier series f(t) = Σ c_n e^{2πint} (§2.6).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from fourier_analysis.series import fourier_coefficients


@dataclass(frozen=True, slots=True)
class EpicycleComponent:
    """A single rotating vector in an epicycle chain.

    Attributes
    ----------
    frequency : int
        The harmonic number n.
    coefficient : complex
        The Fourier coefficient c_n = |c_n| e^{i·arg(c_n)}.
    """

    frequency: int
    coefficient: complex

    @property
    def amplitude(self) -> float:
        return abs(self.coefficient)

    @property
    def phase(self) -> float:
        return float(np.angle(self.coefficient))


class EpicycleChain:
    """A chain of epicycle components, ordered by descending amplitude.

    The chain evaluates the partial Fourier sum at any time t ∈ [0, 1):
        f(t) = Σ c_n · e^{2πi·n·t}
    """

    def __init__(self, components: list[EpicycleComponent]) -> None:
        self.components = sorted(components, key=lambda c: c.amplitude, reverse=True)

    @classmethod
    def from_signal(
        cls,
        signal: NDArray[np.complexfloating] | NDArray[np.floating],
        n_harmonics: int | None = None,
    ) -> EpicycleChain:
        """Build an epicycle chain from a discrete signal.

        Parameters
        ----------
        signal : array-like
            The input signal (1D, complex or real).
        n_harmonics : int, optional
            Max number of positive/negative harmonics.
            If None, uses all available harmonics.
        """
        signal = np.asarray(signal, dtype=np.complex128)
        N = len(signal)
        coeffs = fourier_coefficients(signal)

        if n_harmonics is None:
            n_harmonics = N // 2

        components: list[EpicycleComponent] = []

        # DC term
        components.append(EpicycleComponent(frequency=0, coefficient=complex(coeffs[0])))

        # Positive and negative frequencies
        for n in range(1, n_harmonics + 1):
            if n < len(coeffs):
                components.append(
                    EpicycleComponent(frequency=n, coefficient=complex(coeffs[n]))
                )
            neg_idx = -n % N
            if neg_idx < len(coeffs) and neg_idx != n:
                components.append(
                    EpicycleComponent(frequency=-n, coefficient=complex(coeffs[neg_idx]))
                )

        return cls(components)

    def evaluate(self, t: float | NDArray[np.floating]) -> complex | NDArray[np.complex128]:
        """Evaluate the epicycle chain at time(s) t ∈ [0, 1).

        Returns the position of the tip of the last vector.
        """
        t = np.asarray(t)
        result = np.zeros_like(t, dtype=np.complex128)
        for comp in self.components:
            result = result + comp.coefficient * np.exp(2j * np.pi * comp.frequency * t)
        return complex(result) if result.ndim == 0 else result

    def positions_at(self, t: float) -> list[complex]:
        """Return cumulative center positions at time t.

        positions[0] = 0 (origin)
        positions[k] = sum of first k vectors

        Used for drawing the chain of circles.
        """
        positions: list[complex] = [0j]
        cumulative = 0j
        for comp in self.components:
            cumulative += comp.coefficient * np.exp(2j * np.pi * comp.frequency * t)
            positions.append(cumulative)
        return positions

    def __len__(self) -> int:
        return len(self.components)
