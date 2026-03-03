"""F15: Cooley-Tukey butterfly diagram for N=8.

Referenced in §5.2. Shows the decimation-in-time factorization stages.
"""

from __future__ import annotations

import matplotlib.pyplot as plt

from fourier_analysis.figures.style import BLUE, RED, GRAY, save_figure, setup_style


def generate() -> None:
    setup_style()
    N = 8
    stages = 3  # log2(8)

    fig, ax = plt.subplots(figsize=(10, 6))
    ax.set_xlim(-0.5, stages + 0.5)
    ax.set_ylim(-0.5, N - 0.5)
    ax.invert_yaxis()

    # Bit-reversed input order
    bit_rev = [0, 4, 2, 6, 1, 5, 3, 7]

    # Draw input labels
    for i in range(N):
        ax.text(-0.4, i, f"$x[{bit_rev[i]}]$", fontsize=10, ha="right", va="center")

    # Draw output labels
    for i in range(N):
        ax.text(stages + 0.4, i, f"$X[{i}]$", fontsize=10, ha="left", va="center")

    # Draw horizontal lines
    for i in range(N):
        ax.plot([-0.1, stages + 0.1], [i, i], color=GRAY, linewidth=0.5, alpha=0.5)

    # Draw butterfly connections for each stage
    for stage in range(stages):
        half_size = 2**stage
        full_size = 2 * half_size
        x_pos = stage + 0.5

        for group_start in range(0, N, full_size):
            for k in range(half_size):
                top = group_start + k
                bottom = group_start + k + half_size

                # Draw butterfly
                ax.plot([x_pos - 0.2, x_pos + 0.2], [top, top], color=BLUE, linewidth=1.2)
                ax.plot([x_pos - 0.2, x_pos + 0.2], [bottom, bottom], color=BLUE, linewidth=1.2)

                # Cross connections
                ax.annotate(
                    "",
                    xy=(x_pos + 0.2, top),
                    xytext=(x_pos - 0.2, bottom),
                    arrowprops=dict(arrowstyle="-", color=BLUE, lw=0.8),
                )
                ax.annotate(
                    "",
                    xy=(x_pos + 0.2, bottom),
                    xytext=(x_pos - 0.2, top),
                    arrowprops=dict(arrowstyle="-", color=RED, lw=0.8),
                )

                # Twiddle factor label
                twiddle_exp = k * (N // full_size)
                if twiddle_exp > 0:
                    ax.text(
                        x_pos,
                        (top + bottom) / 2,
                        f"$W^{{{twiddle_exp}}}_{{{N}}}$",
                        fontsize=7,
                        ha="center",
                        va="center",
                        bbox=dict(boxstyle="round,pad=0.1", facecolor="white", edgecolor="none"),
                    )

        # Stage label
        ax.text(x_pos, -0.3, f"Stage {stage + 1}", fontsize=10, ha="center", va="center")

    ax.axis("off")
    ax.set_title(f"Cooley-Tukey FFT Butterfly Diagram ($N = {N}$)", pad=20)

    save_figure(fig, "f15_butterfly")


if __name__ == "__main__":
    generate()
