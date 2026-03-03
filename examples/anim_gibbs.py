"""Animate the Gibbs phenomenon for a square wave.

Usage:
    uv run python examples/anim_gibbs.py [--output gibbs.mp4]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation


def main() -> None:
    parser = argparse.ArgumentParser(description="Animate Gibbs phenomenon")
    parser.add_argument("--output", type=Path, default=None, help="Output video path")
    args = parser.parse_args()

    fig, ax = plt.subplots(figsize=(8, 5))

    x = np.linspace(-np.pi, np.pi, 2000)
    square = np.sign(x)

    ax.plot(x, square, "k--", linewidth=0.8, alpha=0.5, label="Square wave")
    (line,) = ax.plot([], [], color="#cb181d", linewidth=1.5)
    title = ax.set_title("")
    ax.set_xlim(-np.pi, np.pi)
    ax.set_ylim(-1.5, 1.5)
    ax.set_xlabel(r"$x$")
    ax.set_ylabel(r"$S_N(x)$")
    ax.legend(loc="upper right")

    max_N = 150

    def update(frame):
        N = frame + 1
        S = np.zeros_like(x)
        for n in range(1, N + 1, 2):
            S += (4 / (n * np.pi)) * np.sin(n * x)
        line.set_data(x, S)
        title.set_text(f"Gibbs phenomenon: $N = {N}$")
        return (line, title)

    anim = FuncAnimation(fig, update, frames=max_N, interval=80, blit=False)

    if args.output:
        anim.save(str(args.output), writer="ffmpeg", fps=12, dpi=150)
        plt.close(fig)
    else:
        plt.show()


if __name__ == "__main__":
    main()
