"""F7: Fourier transform projection visualization.

Referenced in Example 4.0.2. Shows the projection of e^{2πix} onto f,
illustrating the Fourier transform as an inner product.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from fourier_analysis.figures.style import BLUE, RED, PURPLE, save_figure, setup_style


def generate() -> None:
    setup_style()
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.5))

    x = np.linspace(-np.pi, np.pi, 1000)
    f = np.sin(10 * x) + np.cos(3 * x) ** 2
    basis = np.exp(2j * np.pi * x)

    # f(x)
    axes[0].plot(x, f, color=BLUE, linewidth=1.2)
    axes[0].set_title(r"$f(x) = \sin(10x) + \cos^2(3x)$")
    axes[0].set_xlabel(r"$x$")
    axes[0].set_ylabel(r"$f(x)$")

    # basis function
    axes[1].plot(x, basis.real, color=RED, linewidth=1.2, label=r"$\mathrm{Re}(e^{2\pi ix})$")
    axes[1].plot(
        x, basis.imag, color=RED, linewidth=1.2, linestyle="--", label=r"$\mathrm{Im}(e^{2\pi ix})$"
    )
    axes[1].set_title(r"$e^{2\pi ix}$")
    axes[1].set_xlabel(r"$x$")
    axes[1].legend(fontsize=8)

    # product f * conj(basis)
    product = f * np.conj(basis)
    axes[2].plot(x, product.real, color=PURPLE, linewidth=1.0, label="Real part")
    axes[2].plot(x, product.imag, color=PURPLE, linewidth=1.0, linestyle="--", label="Imag part")
    axes[2].fill_between(x, product.real, alpha=0.15, color=PURPLE)
    inner = np.trapezoid(product, x) / (2 * np.pi)
    axes[2].set_title(rf"$\langle f, e^{{2\pi ix}}\rangle / 2\pi \approx {inner:.3f}$")
    axes[2].set_xlabel(r"$x$")
    axes[2].legend(fontsize=8)

    for ax in axes:
        ax.set_xlim(-np.pi, np.pi)

    fig.tight_layout()
    save_figure(fig, "f07_fourier_projection")


if __name__ == "__main__":
    generate()
