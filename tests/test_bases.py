"""Tests for the generalized eigenbasis decomposition module."""

from __future__ import annotations

import numpy as np
import pytest

from fourier_analysis.bases import (
    BasisComponent,
    BasisDecomposition,
    CurveApproximation,
    approximate_curve,
    build_animation_data,
    chebyshev_decomposition,
    chebyshev_fit,
    evaluate_partial_sum,
    fourier_decomposition,
    legendre_decomposition,
    legendre_from_chebyshev,
)


class TestChebyshevFit:
    def test_constant_signal(self):
        signal = np.ones(100)
        coeffs = chebyshev_fit(signal, degree=5)
        assert abs(coeffs[0] - 1.0) < 1e-10
        assert np.allclose(coeffs[1:], 0, atol=1e-10)

    def test_linear_signal(self):
        s = np.linspace(-1, 1, 200)
        signal = 3.0 * s + 2.0
        coeffs = chebyshev_fit(signal, degree=5)
        # T_0(s) = 1, T_1(s) = s, so f(s) = 2*T_0 + 3*T_1
        assert abs(coeffs[0] - 2.0) < 1e-8
        assert abs(coeffs[1] - 3.0) < 1e-8
        assert np.allclose(coeffs[2:], 0, atol=1e-8)

    def test_cosine_exact_in_chebyshev(self):
        """cos(arccos(s)) = s = T_1(s), so fitting T_1 should be exact."""
        s = np.linspace(-1, 1, 500)
        signal = s  # T_1(s) = s
        coeffs = chebyshev_fit(signal, degree=10)
        assert abs(coeffs[1] - 1.0) < 1e-8
        assert abs(coeffs[0]) < 1e-8
        assert np.allclose(coeffs[2:], 0, atol=1e-8)


class TestLegendreFromChebyshev:
    def test_constant(self):
        cheb = np.array([5.0])
        leg = legendre_from_chebyshev(cheb)
        assert abs(leg[0] - 5.0) < 1e-10

    def test_linear(self):
        # T_0 = 1, T_1 = s; P_0 = 1, P_1 = s
        # So coefficients should be identical for degree <= 1
        cheb = np.array([2.0, 3.0])
        leg = legendre_from_chebyshev(cheb)
        assert abs(leg[0] - 2.0) < 1e-10
        assert abs(leg[1] - 3.0) < 1e-10

    def test_roundtrip_evaluation(self):
        """Chebyshev and Legendre representations evaluate to the same values."""
        from numpy.polynomial import chebyshev as cheb_mod, legendre as leg_mod

        cheb_coeffs = np.array([1.0, 2.0, -0.5, 0.3])
        leg_coeffs = legendre_from_chebyshev(cheb_coeffs)

        s = np.linspace(-1, 1, 200)
        cheb_vals = cheb_mod.chebval(s, cheb_coeffs)
        leg_vals = leg_mod.legval(s, leg_coeffs)
        np.testing.assert_allclose(cheb_vals, leg_vals, atol=1e-10)


class TestDecompositions:
    def test_fourier_decomposition_basic(self):
        t = np.linspace(0, 1, 128, endpoint=False)
        signal = np.exp(2j * np.pi * t)  # pure frequency 1
        decomp = fourier_decomposition(signal, n_harmonics=10)
        assert decomp.basis == "fourier"
        assert decomp.domain == (0.0, 1.0)
        # Should have a dominant component at frequency 1
        top = decomp.components[0]
        assert top.index == 1
        assert abs(top.amplitude - 1.0) < 1e-10

    def test_chebyshev_decomposition(self):
        signal = np.ones(100, dtype=np.float64)
        decomp = chebyshev_decomposition(signal, degree=5)
        assert decomp.basis == "chebyshev"
        assert len(decomp.components) == 6  # degrees 0..5

    def test_legendre_decomposition(self):
        signal = np.ones(100, dtype=np.float64)
        decomp = legendre_decomposition(signal, degree=5)
        assert decomp.basis == "legendre"
        top = decomp.components[0]
        assert top.index == 0
        assert abs(top.amplitude - 1.0) < 1e-8


class TestApproximateCurve:
    def test_circle(self):
        """A circle should be perfectly captured by Fourier with 1 harmonic."""
        t = np.linspace(0, 1, 256, endpoint=False)
        circle = np.exp(2j * np.pi * t)
        approx = approximate_curve(circle, max_degree=50, n_harmonics=50)
        assert approx.n_points == 256
        assert approx.max_degree == 50
        assert "chebyshev" in approx.x
        assert "legendre" in approx.y
        assert approx.fourier.basis == "fourier"

    def test_has_all_bases(self):
        t = np.linspace(0, 1, 128, endpoint=False)
        signal = np.cos(2 * np.pi * t) + 1j * np.sin(4 * np.pi * t)
        approx = approximate_curve(signal, max_degree=20)
        assert set(approx.x.keys()) == {"chebyshev", "legendre"}
        assert set(approx.y.keys()) == {"chebyshev", "legendre"}


class TestEvaluatePartialSum:
    def test_fourier_partial_sum_convergence(self):
        """More terms -> closer approximation."""
        t = np.linspace(0, 1, 256, endpoint=False)
        # Square-ish wave
        signal = np.sign(np.sin(2 * np.pi * t)).astype(np.complex128)
        decomp = fourier_decomposition(signal, n_harmonics=100)

        err_5 = np.mean(np.abs(evaluate_partial_sum(decomp, 5, 256) - signal) ** 2)
        err_50 = np.mean(np.abs(evaluate_partial_sum(decomp, 50, 256) - signal) ** 2)
        assert err_50 < err_5

    def test_chebyshev_partial_sum(self):
        s = np.linspace(-1, 1, 200)
        signal = np.sin(3 * s)
        decomp = chebyshev_decomposition(signal, degree=20)
        result = evaluate_partial_sum(decomp, 20, 200)
        np.testing.assert_allclose(result, signal, atol=1e-4)

    def test_legendre_partial_sum(self):
        s = np.linspace(-1, 1, 200)
        signal = s**3 - 0.5 * s
        decomp = legendre_decomposition(signal, degree=10)
        result = evaluate_partial_sum(decomp, 10, 200)
        np.testing.assert_allclose(result, signal, atol=1e-4)


class TestBuildAnimationData:
    def test_structure(self):
        t = np.linspace(0, 1, 64, endpoint=False)
        signal = np.exp(2j * np.pi * t)
        data = build_animation_data(signal, max_degree=10, n_eval=100)

        assert "original" in data
        assert "decompositions" in data
        assert "partial_sums" in data
        assert "eval_points" in data
        assert "levels" in data

        assert "fourier" in data["partial_sums"]
        assert "chebyshev" in data["partial_sums"]
        assert "legendre" in data["partial_sums"]

        # Each partial sum level should have x and y arrays
        for basis in ("fourier", "chebyshev", "legendre"):
            for level, xy in data["partial_sums"][basis].items():
                assert "x" in xy
                assert "y" in xy
                assert len(xy["x"]) == 100

    def test_custom_levels(self):
        t = np.linspace(0, 1, 64, endpoint=False)
        signal = np.exp(2j * np.pi * t)
        data = build_animation_data(signal, max_degree=10, levels=[1, 5, 10])
        assert data["levels"] == [1, 5, 10]
        for basis in ("fourier", "chebyshev", "legendre"):
            assert set(data["partial_sums"][basis].keys()) == {1, 5, 10}
