"""Fourier series computation via FFT.

Implements the core operations from the paper:
- Fourier coefficients via FFT (§2.6, Definition: Fourier Transform)
- Reconstruction from coefficients (§2.6, Definition: Fourier Series; Complex Form)
- Partial sums (§2.8, Convergence of Fourier Series)
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from fourier_analysis.fft_backend import get_backend


def fourier_coefficients(
    signal: NDArray[np.complexfloating] | NDArray[np.floating],
    n_harmonics: int | None = None,
) -> NDArray[np.complex128]:
    """Compute Fourier coefficients of a discrete signal.

    Uses the FFT to compute c_n = (1/N) * sum_k f(k) * exp(-2πi n k / N).
    Coefficients are ordered as [c_0, c_1, ..., c_{N/2}, c_{-N/2+1}, ..., c_{-1}]
    (standard FFT ordering).

    Parameters
    ----------
    signal : array-like
        The input signal (1D).
    n_harmonics : int, optional
        If given, return only the first n_harmonics positive and negative
        frequencies (2*n_harmonics + 1 coefficients total, centered at DC).

    Returns
    -------
    NDArray[complex128]
        Fourier coefficients.
    """
    backend = get_backend()
    signal = np.asarray(signal, dtype=np.complex128)
    N = len(signal)
    coeffs = backend.fft(signal) / N

    if n_harmonics is not None:
        n_harmonics = min(n_harmonics, N // 2)
        pos = coeffs[: n_harmonics + 1]
        neg = coeffs[-(n_harmonics):]
        coeffs = np.concatenate([pos, neg])

    return coeffs


def fourier_reconstruct(
    coefficients: NDArray[np.complexfloating],
    n_points: int,
) -> NDArray[np.complex128]:
    """Reconstruct a signal from Fourier coefficients.

    Computes f(x) = sum_n c_n * exp(2πi n x / N) at n_points equally spaced
    points on [0, 1).

    Parameters
    ----------
    coefficients : array-like
        Fourier coefficients in FFT ordering.
    n_points : int
        Number of output points.

    Returns
    -------
    NDArray[complex128]
        Reconstructed signal.
    """
    backend = get_backend()
    coefficients = np.asarray(coefficients, dtype=np.complex128)

    # Pad or truncate to n_points, then IFFT
    padded = np.zeros(n_points, dtype=np.complex128)
    n_coeffs = len(coefficients)

    if n_coeffs <= n_points:
        # Split into positive and negative frequencies
        half = (n_coeffs + 1) // 2
        padded[:half] = coefficients[:half]
        padded[-(n_coeffs - half) :] = coefficients[half:]
    else:
        half = (n_points + 1) // 2
        padded[:half] = coefficients[:half]
        padded[-(n_points - half) :] = coefficients[-(n_points - half) :]

    return backend.ifft(padded * n_points)


def partial_sum(
    signal: NDArray[np.complexfloating] | NDArray[np.floating],
    n_harmonics: int,
    n_points: int | None = None,
) -> NDArray[np.complex128]:
    """Compute a partial Fourier sum truncated to n_harmonics.

    This is the S_N(x) from the convergence discussion (§2.8):
    S_N(x) = sum_{n=-N}^{N} c_n e^{inx}

    Parameters
    ----------
    signal : array-like
        The input signal.
    n_harmonics : int
        Number of harmonics to include (N in S_N).
    n_points : int, optional
        Number of output points. Defaults to len(signal).

    Returns
    -------
    NDArray[complex128]
        The partial sum reconstruction.
    """
    signal = np.asarray(signal, dtype=np.complex128)
    if n_points is None:
        n_points = len(signal)

    coeffs = fourier_coefficients(signal, n_harmonics=n_harmonics)
    return fourier_reconstruct(coeffs, n_points)
