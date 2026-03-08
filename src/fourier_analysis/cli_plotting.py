"""Plotting helpers for the CLI commands.

Extracted from cli.py to reduce file length and isolate matplotlib
dependencies from CLI argument parsing.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from numpy.typing import NDArray


def plot_reconstruction(
    original: np.ndarray,
    recon: np.ndarray,
    n_harmonics: int,
    output: str | Path | None,
) -> None:
    """Plot original contour vs epicycle reconstruction."""
    import matplotlib.pyplot as plt
    from fourier_analysis.figures.style import BLUE, setup_style

    setup_style()
    fig, ax = plt.subplots(figsize=(8, 8))
    ax.plot(original.real, original.imag, color="gray", linewidth=0.4, alpha=0.4, label="Contour")
    ax.plot(recon.real, recon.imag, color=BLUE, linewidth=0.8, label=f"$N = {n_harmonics}$")
    ax.set_aspect("equal")
    ax.set_xlabel(r"$\mathrm{Re}$")
    ax.set_ylabel(r"$\mathrm{Im}$")
    ax.legend()
    ax.grid(True, alpha=0.2)
    fig.tight_layout()

    if output:
        fig.savefig(output)
        plt.close(fig)
    else:
        plt.show()


def plot_series_reconstruction(
    signal: np.ndarray,
    recon: np.ndarray,
    n_harmonics: int,
    output: str | Path,
) -> None:
    """Plot original signal vs Fourier partial sum reconstruction."""
    import matplotlib.pyplot as plt
    from fourier_analysis.figures.style import BLUE, WOLFRAM_RED, setup_style

    setup_style()
    fig, ax = plt.subplots(figsize=(8, 4))
    t_orig = np.linspace(0, 1, len(signal), endpoint=False)
    t_recon = np.linspace(0, 1, len(recon), endpoint=False)
    ax.plot(t_orig, signal.real, color="gray", linewidth=0.5, alpha=0.5, label="Original")
    ax.plot(t_recon, recon.real, color=BLUE, linewidth=1.2, label=f"$N = {n_harmonics}$")
    ax.set_xlabel("$t$")
    ax.set_ylabel("$f(t)$")
    ax.legend()
    ax.grid(True, alpha=0.2)
    fig.tight_layout()
    fig.savefig(output)
    plt.close(fig)


def plot_basis_comparison(
    path: np.ndarray,
    approx,
    degrees: list[int],
    output: str | Path | None,
) -> None:
    """Plot basis comparison grid: Fourier, Chebyshev, Legendre at each degree."""
    import matplotlib.pyplot as plt
    from fourier_analysis.bases import evaluate_partial_sum
    from fourier_analysis.figures.style import BLUE, WOLFRAM_RED, setup_style

    setup_style()
    n_deg = len(degrees)
    fig, axes = plt.subplots(n_deg, 3, figsize=(15, 5 * n_deg))
    if n_deg == 1:
        axes = axes[np.newaxis, :]

    bases = ["fourier", "chebyshev", "legendre"]
    colors = [BLUE, WOLFRAM_RED, "#2ca02c"]

    for row, deg in enumerate(degrees):
        for col, (basis_name, color) in enumerate(zip(bases, colors)):
            ax = axes[row, col]
            ax.plot(path.real, path.imag, color="gray", linewidth=0.4, alpha=0.4)

            if basis_name == "fourier":
                vals = evaluate_partial_sum(approx.fourier, deg, len(path))
                ax.plot(vals.real, vals.imag, color=color, linewidth=0.8)
            else:
                x_vals = evaluate_partial_sum(approx.x[basis_name], deg, len(path))
                y_vals = evaluate_partial_sum(approx.y[basis_name], deg, len(path))
                ax.plot(x_vals, y_vals, color=color, linewidth=0.8)

            ax.set_aspect("equal")
            ax.set_title(f"{basis_name.title()}, $N = {deg}$")
            ax.grid(True, alpha=0.2)

    fig.tight_layout()
    if output:
        fig.savefig(output)
        plt.close(fig)
    else:
        plt.show()
