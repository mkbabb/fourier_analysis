"""F16: Bluestein chirp-z illustration.

Referenced in §5.3. Shows the chirp signal and the identity
nk = -(k-n)²/2 + n²/2 + k²/2 that converts DFT to convolution.
"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np

from fourier_analysis.figures.style import BLUE, RED, PURPLE, save_figure, setup_style


def generate() -> None:
    setup_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4))

    N = 32
    n = np.arange(N)

    # Chirp signal: w^{n²/2} where w = e^{-2πi/N}
    chirp = np.exp(-1j * np.pi * n**2 / N)

    ax1.stem(n, chirp.real, linefmt=f"{BLUE}-", markerfmt=f"{BLUE}o", basefmt="k-", label="Real")
    ax1.stem(n, chirp.imag, linefmt=f"{RED}--", markerfmt=f"{RED}s", basefmt="k-", label="Imag")
    ax1.set_xlabel(r"$n$")
    ax1.set_ylabel(r"Amplitude")
    ax1.set_title(rf"Chirp signal $\omega^{{n^2/2}}$, $N = {N}$")
    ax1.legend(fontsize=9)

    # Show the identity: nk = -(k-n)²/2 + n²/2 + k²/2
    k_vals = np.arange(N)
    n_val = 5  # example frequency
    direct = n_val * k_vals
    bluestein = -(k_vals - n_val) ** 2 / 2 + n_val**2 / 2 + k_vals**2 / 2

    ax2.plot(k_vals, direct, "o", color=BLUE, markersize=4, label=r"$nk$ (direct)")
    ax2.plot(
        k_vals,
        bluestein,
        "x",
        color=RED,
        markersize=5,
        label=r"$-\frac{(k-n)^2}{2} + \frac{n^2}{2} + \frac{k^2}{2}$",
    )
    ax2.set_xlabel(r"$k$")
    ax2.set_ylabel(r"Value")
    ax2.set_title(rf"Bluestein identity ($n = {n_val}$)")
    ax2.legend(fontsize=8)

    fig.tight_layout()
    save_figure(fig, "f16_bluestein")


if __name__ == "__main__":
    generate()
