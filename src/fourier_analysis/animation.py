"""Matplotlib-based animation of epicycle chains.

Renders the rotating-vector representation of Fourier series as an
animation, showing the individual epicycles, their connecting lines,
and the traced path.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation

from fourier_analysis.epicycles import EpicycleChain


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
    """

    def __init__(
        self,
        chain: EpicycleChain,
        *,
        fps: int = 30,
        trail_length: int = 200,
        figsize: tuple[float, float] = (8, 8),
        duration: float = 10.0,
    ) -> None:
        self.chain = chain
        self.fps = fps
        self.trail_length = trail_length
        self.figsize = figsize
        self.duration = duration
        self.n_frames = int(fps * duration)

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
            Animation writer (e.g., "ffmpeg", "pillow").

        Returns
        -------
        FuncAnimation
            The matplotlib animation object.
        """
        fig, ax = plt.subplots(1, 1, figsize=self.figsize)
        ax.set_aspect("equal")
        ax.set_facecolor("black")
        fig.patch.set_facecolor("black")

        # Precompute the full trace
        ts = np.linspace(0, 1, self.n_frames, endpoint=False)
        full_trace = self.chain.evaluate(ts)

        # Determine axis limits from the full trace
        margin = 0.1
        xmin = float(np.min(full_trace.real)) - margin * abs(float(np.ptp(full_trace.real)))
        xmax = float(np.max(full_trace.real)) + margin * abs(float(np.ptp(full_trace.real)))
        ymin = float(np.min(full_trace.imag)) - margin * abs(float(np.ptp(full_trace.imag)))
        ymax = float(np.max(full_trace.imag)) + margin * abs(float(np.ptp(full_trace.imag)))
        ax.set_xlim(xmin, xmax)
        ax.set_ylim(ymin, ymax)
        ax.axis("off")

        # Artists
        (trail_line,) = ax.plot([], [], color="cyan", linewidth=1.0, alpha=0.8)
        (arm_line,) = ax.plot([], [], color="white", linewidth=0.5, alpha=0.6)
        circles: list[plt.Circle] = []

        def init():
            trail_line.set_data([], [])
            arm_line.set_data([], [])
            return (trail_line, arm_line)

        def update(frame: int):
            t = ts[frame]

            # Trail
            start = max(0, frame - self.trail_length)
            trail = full_trace[start : frame + 1]
            trail_line.set_data(trail.real, trail.imag)

            # Epicycle arms and circles
            positions = self.chain.positions_at(t)
            xs = [p.real for p in positions]
            ys = [p.imag for p in positions]
            arm_line.set_data(xs, ys)

            # Remove old circles
            for c in circles:
                c.remove()
            circles.clear()

            # Draw new circles
            for i, comp in enumerate(self.chain.components):
                center = positions[i]
                radius = comp.amplitude
                if radius > 0.001:
                    circle = plt.Circle(
                        (center.real, center.imag),
                        radius,
                        fill=False,
                        color="gray",
                        linewidth=0.3,
                        alpha=0.4,
                    )
                    ax.add_patch(circle)
                    circles.append(circle)

            return (trail_line, arm_line, *circles)

        anim = FuncAnimation(
            fig,
            update,
            init_func=init,
            frames=self.n_frames,
            interval=1000 / self.fps,
            blit=False,
        )

        if output is not None:
            anim.save(str(output), writer=writer, fps=self.fps, dpi=150)
            plt.close(fig)
        else:
            plt.show()

        return anim
