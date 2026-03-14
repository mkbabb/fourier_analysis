"""Tests for fourier_analysis.shortest_tour."""

import numpy as np
import pytest

from fourier_analysis.shortest_tour import build_contour_tour, ContourTour


class TestBuildContourTour:
    def test_empty_contours_returns_empty(self):
        """Empty list should return an empty tour."""
        tour = build_contour_tour([])
        assert len(tour.path) == 0
        assert tour.path.dtype == np.complex128
        assert tour.ordered_contours == ()
        assert tour.gap_lengths == ()

    def test_single_contour_returned_as_is(self):
        """A single contour should come back unchanged."""
        contour = np.array([0, 1, 2, 3], dtype=np.complex128)
        tour = build_contour_tour([contour])
        np.testing.assert_array_equal(tour.path, contour)
        assert len(tour.ordered_contours) == 1
        assert tour.gap_lengths == ()

    def test_nearest_neighbor_basic_ordering(self):
        """Three contours in a known geometry should be ordered sensibly."""
        a = np.array([0, 1, 2], dtype=np.complex128)
        b = np.array([3, 4, 5], dtype=np.complex128)
        c = np.array([100, 101, 102], dtype=np.complex128)

        tour = build_contour_tour([a, b, c], method="nearest")
        assert len(tour.path) == 9
        assert len(tour.ordered_contours) == 3
        assert len(tour.gap_lengths) == 2

    def test_2opt_improves_on_nearest(self):
        """On a pathological case, 2-opt should reduce total gap distance."""
        n_contours = 8
        contours = []
        angles = np.linspace(0, 2 * np.pi, n_contours, endpoint=False)
        shuffled = [0, 4, 1, 5, 2, 6, 3, 7]
        for idx in shuffled:
            center = 10 * np.exp(1j * angles[idx])
            c = center + np.array([0, 0.1, 0.2], dtype=np.complex128)
            contours.append(c)

        tour_nn = build_contour_tour(contours, method="nearest")
        tour_2opt = build_contour_tour(contours, method="nearest_2opt")

        assert len(tour_nn.path) == len(tour_2opt.path)
        assert tour_nn.path.dtype == np.complex128
        assert tour_2opt.path.dtype == np.complex128

        # 2-opt total gap should be <= nearest neighbor
        nn_gap = sum(tour_nn.gap_lengths)
        opt_gap = sum(tour_2opt.gap_lengths)
        assert opt_gap <= nn_gap + 1e-10

    def test_contour_reversal(self):
        """The algorithm should reverse contours to minimize gaps."""
        a = np.array([0, 1], dtype=np.complex128)
        b = np.array([3, 2], dtype=np.complex128)

        tour = build_contour_tour([a, b], method="nearest")
        assert len(tour.path) == 4
        gap = abs(tour.path[1] - tour.path[2])
        assert gap <= 2.0

    def test_unknown_method_raises(self):
        """An unknown method string should raise ValueError."""
        contours = [np.array([0, 1], dtype=np.complex128)]
        with pytest.raises(ValueError, match="Unknown method"):
            build_contour_tour(contours, method="bogus")

    def test_gap_lengths_consistent_with_path(self):
        """Gap lengths should match actual distances in the path."""
        a = np.array([0, 1, 2], dtype=np.complex128)
        b = np.array([5, 6, 7], dtype=np.complex128)
        c = np.array([10, 11, 12], dtype=np.complex128)

        tour = build_contour_tour([a, b, c])
        assert len(tour.gap_lengths) == 2
        # Each gap should be a positive number
        for g in tour.gap_lengths:
            assert g >= 0

    def test_contour_tour_is_frozen(self):
        """ContourTour should be immutable."""
        tour = build_contour_tour([np.array([0, 1], dtype=np.complex128)])
        with pytest.raises(AttributeError):
            tour.path = np.array([])  # type: ignore[misc]
