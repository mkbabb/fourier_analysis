"""Matplotlib-based animation of epicycle chains.

Renders the rotating-vector representation of Fourier series as an
animation. Each epicycle is assigned a color from a rainbow spectrum
(``gist_rainbow``), sorted by descending amplitude---the largest
circle is red, progressing through orange, yellow, green, blue, and
into violet for the smallest visible harmonics.

The traced path is a continuous line in bright red-orange (``#ff3412``)
that builds up gradually as the tip sweeps through one full period.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from matplotlib.patches import Circle

from fourier_analysis.epicycles import EpicycleChain
from fourier_analysis.figures.style import setup_style


class FourierAnimation:
    """Animate an epicycle chain tracing a path.

    Parameters
    ----------
    chain : EpicycleChain
        The epicycle chain to animate.
    fps : int
        Frames per second.
    trail_length : int
        Number of frames of trail to show behind the tip.
    figsize : tuple of float
        Figure size in inches.
    duration : float
        Duration in seconds for one full period.
    dpi : int
        Output resolution.
    max_circles : int
        Max number of circles to render (largest amplitudes only).
        Keeps the animation snappy for high-harmonic chains.
    """

    def __init__(
        self,
        chain: EpicycleChain,
        *,
        fps: int = 30,
        trail_length: int = 200,
        figsize: tuple[float, float] = (8, 8),
        duration: float = 30.0,
        dpi: int = 150,
        max_circles: int = 80,
    ) -> None:
        self.chain = chain
        self.fps = fps
        self.trail_length = trail_length
        self.figsize = figsize
        self.duration = duration
        self.dpi = dpi
        self.n_frames = int(fps * duration)

        # Components are already sorted by descending amplitude.
        # Cap the visible circles so rendering doesn't crawl.
        self.n_visible = min(max_circles, len(chain.components))

    def render(
        self,
        output: str | Path | None = None,
        writer: str = "ffmpeg",
    ) -> FuncAnimation:
        """Render the animation.

        Parameters
        ----------
        output : str or Path, optional
            Output file path. If None, displays interactively.
        writer : str
            Animation writer (e.g., ``"ffmpeg"``, ``"pillow"``).

        Returns
        -------
        FuncAnimation
            The matplotlib animation object.
        """
        setup_style()

        fig, ax = plt.subplots(1, 1, figsize=self.figsize)
        ax.set_aspect("equal")

        # Precompute the full trace
        ts = np.linspace(0, 1, self.n_frames, endpoint=False)
        full_trace = self.chain.evaluate(ts)

        # Axis limits with margin
        margin = 0.15
        x_range = float(np.ptp(full_trace.real))
        y_range = float(np.ptp(full_trace.imag))
        ax.set_xlim(
            float(np.min(full_trace.real)) - margin * x_range,
            float(np.max(full_trace.real)) + margin * x_range,
        )
        ax.set_ylim(
            float(np.min(full_trace.imag)) - margin * y_range,
            float(np.max(full_trace.imag)) + margin * y_range,
        )
        ax.set_xlabel(r"$\mathrm{Re}$")
        ax.set_ylabel(r"$\mathrm{Im}$")
        ax.grid(True, alpha=0.2)

        # ---- Rainbow spectrum for circles ----
        # gist_rainbow from 1->0 gives red..violet, matching the original.
        n_vis = self.n_visible
        # Non-linear mapping biased by amplitude: stretch warm colors
        t = np.linspace(0, 1, max(n_vis, 1))
        curved = np.power(t, 0.6)
        spectrum = cm.gist_rainbow(1 - curved)

        # ---- Pre-create persistent artists (no per-frame create/destroy) ----

        # Circle outlines + center dots
        circle_patches: list[Circle] = []
        center_dots: list[Circle] = []

        for i in range(n_vis):
            color = spectrum[i]
            # Circle outline
            circ = Circle(
                (0, 0), 0,
                fill=False,
                color=color,
                linewidth=1.8,
                alpha=0.6,
            )
            ax.add_patch(circ)
            circle_patches.append(circ)

            # Center dot
            dot = Circle(
                (0, 0), 0,
                fill=True,
                color=color,
                alpha=0.7,
            )
            ax.add_patch(dot)
            center_dots.append(dot)

        # Arm segments: one Line2D per epicycle vector, colored to match
        arm_lines = []
        for i in range(n_vis):
            color = spectrum[i]
            (line,) = ax.plot([], [], color=color, linewidth=1.0, alpha=0.7)
            arm_lines.append(line)

        # Tip marker
        (tip_dot,) = ax.plot([], [], "o", color="#ff3412", markersize=5, zorder=10)

        # Trail: traced path as a continuous line that accumulates over time
        (trail_line,) = ax.plot(
            [], [],
            color="#ff3412",
            linewidth=1.2,
            alpha=0.9,
            solid_capstyle="round",
            solid_joinstyle="round",
        )

        def init():
            trail_line.set_data([], [])
            tip_dot.set_data([], [])
            for line in arm_lines:
                line.set_data([], [])
            return (trail_line, tip_dot, *arm_lines)

        def update(frame: int):
            t = ts[frame]

            # ---- Trail (accumulates from the start — no windowing) ----
            trail = full_trace[: frame + 1]
            trail_line.set_data(trail.real, trail.imag)

            # ---- Epicycle chain positions ----
            positions = self.chain.positions_at(t)

            # ---- Update circles, dots, and arm segments ----
            for i in range(n_vis):
                center = positions[i]
                tip = positions[i + 1]
                radius = self.chain.components[i].amplitude

                cx, cy = center.real, center.imag

                # Circle outline
                circle_patches[i].center = (cx, cy)
                circle_patches[i].set_radius(radius)

                # Center dot (small, fixed minimum for visibility)
                center_dots[i].center = (cx, cy)
                center_dots[i].set_radius(max(radius * 0.03, 0.15))

                # Arm segment: vector from center to tip
                arm_lines[i].set_data(
                    [cx, tip.real],
                    [cy, tip.imag],
                )

            # Tip marker
            final = positions[-1]
            tip_dot.set_data([final.real], [final.imag])

            return (
                trail_line,
                tip_dot,
                *arm_lines,
                *circle_patches,
                *center_dots,
            )

        anim = FuncAnimation(
            fig,
            update,
            init_func=init,
            frames=self.n_frames,
            interval=1000 / self.fps,
            blit=False,
        )

        if output is not None:
            anim.save(str(output), writer=writer, fps=self.fps, dpi=self.dpi)
            plt.close(fig)
        else:
            plt.show()

        return anim
