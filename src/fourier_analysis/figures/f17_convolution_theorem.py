"""F17: Convolution theorem visualization.

Referenced in §6.1. 2×2 grid showing f, g in time domain and
F{f}·F{g} in frequency domain, with convolution result.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from fourier_analysis.figures.style import BLUE, RED, PURPLE, GREEN, save_figure, setup_style


def generate() -> None:
    setup_style()
    fig, axes = plt.subplots(2, 2, figsize=(10, 7))

    N = 256
    x = np.linspace(-5, 5, N)

    # f = Gaussian, g = rectangular pulse
    f = np.exp(-x**2)
    g = np.where(np.abs(x) < 1, 1.0, 0.0)

    # FFTs
    F_f = np.fft.fftshift(np.fft.fft(f))
    F_g = np.fft.fftshift(np.fft.fft(g))
    freqs = np.fft.fftshift(np.fft.fftfreq(N, d=(x[1] - x[0])))

    # Convolution in time domain (via IFFT of product)
    conv_fg = np.fft.ifft(np.fft.fft(f) * np.fft.fft(g)).real
    conv_fg *= (x[1] - x[0])  # scale by dx

    # Top-left: f(x)
    axes[0, 0].plot(x, f, color=BLUE, linewidth=1.5)
    axes[0, 0].fill_between(x, f, alpha=0.15, color=BLUE)
    axes[0, 0].set_title(r"$f(x) = e^{-x^2}$")
    axes[0, 0].set_xlabel(r"$x$")

    # Top-right: g(x)
    axes[0, 1].plot(x, g, color=RED, linewidth=1.5)
    axes[0, 1].fill_between(x, g, alpha=0.15, color=RED)
    axes[0, 1].set_title(r"$g(x) = \mathrm{rect}(x)$")
    axes[0, 1].set_xlabel(r"$x$")

    # Bottom-left: |F{f}| · |F{g}|
    axes[1, 0].plot(freqs, np.abs(F_f), color=BLUE, linewidth=1.0, alpha=0.7, label=r"$|\hat{f}|$")
    axes[1, 0].plot(freqs, np.abs(F_g), color=RED, linewidth=1.0, alpha=0.7, label=r"$|\hat{g}|$")
    axes[1, 0].plot(freqs, np.abs(F_f * F_g) / N, color=PURPLE, linewidth=1.5, label=r"$|\hat{f} \cdot \hat{g}|$")
    axes[1, 0].set_title(r"Frequency domain")
    axes[1, 0].set_xlabel(r"Frequency $\xi$")
    axes[1, 0].legend(fontsize=8)
    axes[1, 0].set_xlim(-3, 3)

    # Bottom-right: (f * g)(x)
    axes[1, 1].plot(x, conv_fg, color=GREEN, linewidth=1.5)
    axes[1, 1].fill_between(x, conv_fg, alpha=0.15, color=GREEN)
    axes[1, 1].set_title(r"$(f * g)(x) = \mathcal{F}^{-1}\{\hat{f} \cdot \hat{g}\}$")
    axes[1, 1].set_xlabel(r"$x$")

    fig.suptitle("Convolution Theorem: $\\mathcal{F}\\{f * g\\} = \\hat{f} \\cdot \\hat{g}$", fontsize=14)
    fig.tight_layout()
    save_figure(fig, "f17_convolution_theorem")


if __name__ == "__main__":
    generate()
