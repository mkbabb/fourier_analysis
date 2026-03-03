"""Tests for fourier_analysis.fft_backend."""

import numpy as np

from fourier_analysis.fft_backend import NumpyBackend, get_backend, set_backend


class TestNumpyBackend:
    def test_fft_ifft_roundtrip(self):
        backend = NumpyBackend()
        x = np.random.randn(64) + 1j * np.random.randn(64)
        X = backend.fft(x)
        x_rec = backend.ifft(X)
        np.testing.assert_allclose(x_rec, x, atol=1e-12)

    def test_known_fft(self):
        backend = NumpyBackend()
        # FFT of [1, 0, 0, 0] should be [1, 1, 1, 1]
        x = np.array([1, 0, 0, 0], dtype=np.complex128)
        X = backend.fft(x)
        np.testing.assert_allclose(X, [1, 1, 1, 1], atol=1e-12)


class TestBackendSelection:
    def test_default_is_numpy(self):
        backend = get_backend()
        assert isinstance(backend, NumpyBackend)

    def test_set_numpy(self):
        set_backend("numpy")
        backend = get_backend()
        assert isinstance(backend, NumpyBackend)

    def test_set_invalid_raises(self):
        import pytest

        with pytest.raises(ValueError):
            set_backend("invalid_backend")
