"""FFT backend abstraction.

Provides a protocol-based backend system so that the package can use
either NumPy's FFT or an optional mdarray-based FFT.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

import numpy as np
from numpy.typing import NDArray


@runtime_checkable
class FFTBackend(Protocol):
    """Protocol for FFT backends."""

    def fft(self, x: NDArray[np.complex128]) -> NDArray[np.complex128]: ...
    def ifft(self, x: NDArray[np.complex128]) -> NDArray[np.complex128]: ...


class NumpyBackend:
    """FFT backend using numpy.fft."""

    def fft(self, x: NDArray[np.complex128]) -> NDArray[np.complex128]:
        return np.fft.fft(x)

    def ifft(self, x: NDArray[np.complex128]) -> NDArray[np.complex128]:
        return np.fft.ifft(x)


class MdarrayBackend:
    """FFT backend using mdarray (optional dependency)."""

    def __init__(self) -> None:
        try:
            import mdarray  # noqa: F401

            self._mdarray = mdarray
        except ImportError as e:
            raise ImportError(
                "mdarray is not installed. Install with: pip install mdarray"
            ) from e

    def fft(self, x: NDArray[np.complex128]) -> NDArray[np.complex128]:
        return np.asarray(self._mdarray.fft.fft(x), dtype=np.complex128)

    def ifft(self, x: NDArray[np.complex128]) -> NDArray[np.complex128]:
        return np.asarray(self._mdarray.fft.ifft(x), dtype=np.complex128)


_current_backend: FFTBackend = NumpyBackend()


def set_backend(name: str) -> None:
    """Set the global FFT backend.

    Parameters
    ----------
    name : str
        One of "numpy" or "mdarray".
    """
    global _current_backend
    if name == "numpy":
        _current_backend = NumpyBackend()
    elif name == "mdarray":
        _current_backend = MdarrayBackend()
    else:
        raise ValueError(f"Unknown backend: {name!r}. Use 'numpy' or 'mdarray'.")


def get_backend() -> FFTBackend:
    """Return the current FFT backend."""
    return _current_backend
