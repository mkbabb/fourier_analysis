"""Tests for fourier_analysis.series."""

import numpy as np
import pytest

from fourier_analysis.series import fourier_coefficients, fourier_reconstruct, partial_sum


class TestFourierCoefficients:
    def test_dc_signal(self):
        """A constant signal should have only a DC coefficient."""
        signal = np.ones(64) * 5.0
        coeffs = fourier_coefficients(signal)
        assert abs(coeffs[0] - 5.0) < 1e-10
        assert np.max(np.abs(coeffs[1:])) < 1e-10

    def test_pure_sinusoid(self):
        """A pure complex exponential e^{2πi·k·n/N} should have a single nonzero coefficient."""
        N = 128
        k = 3
        n = np.arange(N)
        signal = np.exp(2j * np.pi * k * n / N)
        coeffs = fourier_coefficients(signal)
        assert abs(abs(coeffs[k]) - 1.0) < 1e-10
        # All others should be near zero
        mask = np.ones(len(coeffs), dtype=bool)
        mask[k] = False
        assert np.max(np.abs(coeffs[mask])) < 1e-10

    def test_n_harmonics_truncation(self):
        """With n_harmonics, should return 2*n_harmonics + 1 coefficients."""
        signal = np.random.randn(256)
        n_harmonics = 10
        coeffs = fourier_coefficients(signal, n_harmonics=n_harmonics)
        assert len(coeffs) == 2 * n_harmonics + 1


class TestFourierReconstruct:
    def test_roundtrip(self):
        """FFT → IFFT should recover the original signal."""
        N = 64
        signal = np.random.randn(N) + 1j * np.random.randn(N)
        coeffs = fourier_coefficients(signal)
        reconstructed = fourier_reconstruct(coeffs, N)
        np.testing.assert_allclose(reconstructed, signal, atol=1e-10)

    def test_upsampling(self):
        """Reconstructing with more points should interpolate smoothly."""
        N = 32
        signal = np.cos(2 * np.pi * np.arange(N) / N)
        coeffs = fourier_coefficients(signal)
        recon = fourier_reconstruct(coeffs, 128)
        # Should still be a cosine
        expected = np.cos(2 * np.pi * np.arange(128) / 128)
        np.testing.assert_allclose(recon.real, expected, atol=1e-10)


class TestPartialSum:
    def test_full_harmonics_recovers_signal(self):
        """Using all harmonics should recover the original signal."""
        N = 64
        signal = np.random.randn(N)
        recon = partial_sum(signal, n_harmonics=N // 2)
        np.testing.assert_allclose(recon.real, signal, atol=1e-10)

    def test_fewer_harmonics_is_smooth(self):
        """Fewer harmonics should produce a smoother signal."""
        N = 256
        n = np.arange(N)
        signal = np.sign(np.sin(2 * np.pi * n / N))  # square wave
        recon_few = partial_sum(signal, n_harmonics=5)
        recon_many = partial_sum(signal, n_harmonics=50)

        # Smoother = smaller total variation
        tv_few = np.sum(np.abs(np.diff(recon_few.real)))
        tv_many = np.sum(np.abs(np.diff(recon_many.real)))
        assert tv_few < tv_many


class TestParseval:
    def test_parseval_identity(self):
        """Verify Parseval's identity: (1/N)Σ|f|² = Σ|c_n|²."""
        N = 128
        signal = np.sin(2 * np.pi * 3 * np.arange(N) / N) + 0.5 * np.cos(2 * np.pi * 7 * np.arange(N) / N)
        coeffs = fourier_coefficients(signal)

        energy_time = np.sum(np.abs(signal) ** 2) / N
        energy_freq = np.sum(np.abs(coeffs) ** 2)

        np.testing.assert_allclose(energy_time, energy_freq, rtol=1e-10)
