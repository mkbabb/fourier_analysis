"""Tests for fourier_analysis.epicycles."""

import numpy as np

from fourier_analysis.epicycles import EpicycleChain, EpicycleComponent


class TestEpicycleComponent:
    def test_amplitude_and_phase(self):
        comp = EpicycleComponent(frequency=1, coefficient=1 + 1j)
        assert abs(comp.amplitude - np.sqrt(2)) < 1e-10
        assert abs(comp.phase - np.pi / 4) < 1e-10

    def test_zero_coefficient(self):
        comp = EpicycleComponent(frequency=0, coefficient=0j)
        assert comp.amplitude == 0.0


class TestEpicycleChain:
    def test_from_signal_roundtrip(self):
        """Epicycle chain should reconstruct the original signal."""
        N = 64
        t = np.linspace(0, 2 * np.pi, N, endpoint=False)
        signal = np.exp(1j * t)  # unit circle

        chain = EpicycleChain.from_signal(signal)
        ts = np.linspace(0, 1, N, endpoint=False)
        recon = chain.evaluate(ts)

        np.testing.assert_allclose(np.abs(recon), 1.0, atol=1e-6)

    def test_positions_at_starts_at_origin(self):
        signal = np.exp(1j * np.linspace(0, 2 * np.pi, 64, endpoint=False))
        chain = EpicycleChain.from_signal(signal, n_harmonics=5)
        positions = chain.positions_at(0.0)
        assert positions[0] == 0j

    def test_positions_at_last_equals_evaluate(self):
        signal = np.exp(1j * np.linspace(0, 2 * np.pi, 64, endpoint=False))
        chain = EpicycleChain.from_signal(signal, n_harmonics=5)
        t = 0.3
        positions = chain.positions_at(t)
        tip = chain.evaluate(t)
        assert abs(positions[-1] - tip) < 1e-10

    def test_sorted_by_amplitude(self):
        signal = np.random.randn(32) + 1j * np.random.randn(32)
        chain = EpicycleChain.from_signal(signal)
        amplitudes = [c.amplitude for c in chain.components]
        assert amplitudes == sorted(amplitudes, reverse=True)

    def test_len(self):
        signal = np.ones(16, dtype=complex)
        chain = EpicycleChain.from_signal(signal, n_harmonics=3)
        assert len(chain) > 0
