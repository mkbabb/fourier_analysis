"""Command-line interface for the fourier-analysis package.

Thin CLI exposing the core library: figure generation, epicycle
reconstruction from images, Fourier coefficient computation, and
animation rendering.

Usage::

    fourier figures [--only F02 F19 ...]
    fourier epicycles IMAGE [-n 200] [-o out.png] [--strategy auto]
    fourier series FILE [-n 50] [-o out.png]
    fourier animate IMAGE [-n 200] [--duration 30] [-o out.mp4]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def _cmd_figures(args: argparse.Namespace) -> int:
    """Generate paper figures."""
    from fourier_analysis.figures.generate_all import GENERATORS, main as gen_main

    if args.only:
        names = {s.upper() for s in args.only}
        valid = {name for name, _ in GENERATORS}
        unknown = names - valid
        if unknown:
            print(f"Unknown figure(s): {', '.join(sorted(unknown))}")
            print(f"Available: {', '.join(sorted(valid))}")
            return 1

        import traceback

        failed: list[str] = []
        for name, module in GENERATORS:
            if name not in names:
                continue
            print(f"Generating {name}...", end=" ", flush=True)
            try:
                module.generate()
                print("OK")
            except Exception:
                print("FAILED")
                traceback.print_exc()
                failed.append(name)
        if failed:
            print(f"\n{len(failed)} figure(s) failed: {', '.join(failed)}")
            return 1
        print("Done.")
        return 0

    return gen_main()


def _cmd_epicycles(args: argparse.Namespace) -> int:
    """Extract contours from an image and reconstruct via epicycles."""
    from fourier_analysis.contours import (
        ContourStrategy,
        extract_contours,
        resample_arc_length,
    )
    from fourier_analysis.epicycles import EpicycleChain
    from fourier_analysis.shortest_tour import order_contours

    image_path = Path(args.image)
    if not image_path.exists():
        print(f"Image not found: {image_path}")
        return 1

    contours = extract_contours(
        image_path,
        strategy=args.strategy,
        resize=args.resize,
        blur_sigma=args.blur,
        min_contour_length=args.min_length,
    )

    if not contours:
        print("No contours extracted.")
        return 1

    print(f"Extracted {len(contours)} contour(s), "
          f"{sum(len(c) for c in contours)} total points")

    path = order_contours(contours)
    path = resample_arc_length(path, args.points)

    chain = EpicycleChain.from_signal(path, n_harmonics=args.harmonics)
    print(f"Epicycle chain: {len(chain)} components, "
          f"N={args.harmonics} harmonics")

    ts = np.linspace(0, 1, 3000)
    recon = chain.evaluate(ts)

    if args.output:
        _plot_reconstruction(path, recon, args.harmonics, args.output)
        print(f"Saved: {args.output}")
    else:
        _plot_reconstruction(path, recon, args.harmonics, None)

    return 0


def _cmd_series(args: argparse.Namespace) -> int:
    """Compute Fourier coefficients of a signal from a text file."""
    from fourier_analysis.series import fourier_coefficients, partial_sum

    data_path = Path(args.file)
    if not data_path.exists():
        print(f"File not found: {data_path}")
        return 1

    signal = np.loadtxt(data_path, dtype=np.complex128)
    if signal.ndim != 1:
        print(f"Expected 1-D signal, got shape {signal.shape}")
        return 1

    print(f"Signal: {len(signal)} samples")

    coeffs = fourier_coefficients(signal, n_harmonics=args.harmonics)
    print(f"Coefficients (N={args.harmonics or 'all'}):")

    n_show = min(len(coeffs), 10)
    for i in range(n_show):
        c = coeffs[i]
        print(f"  c[{i:>3d}] = {c.real:+.6f} {c.imag:+.6f}j  "
              f"(|c| = {abs(c):.6f})")
    if len(coeffs) > n_show:
        print(f"  ... ({len(coeffs) - n_show} more)")

    if args.output:
        n_pts = args.points or len(signal)
        recon = partial_sum(signal, args.harmonics or len(signal) // 2, n_pts)

        import matplotlib.pyplot as plt
        from fourier_analysis.figures.style import BLUE, WOLFRAM_RED, setup_style

        setup_style()
        fig, ax = plt.subplots(figsize=(8, 4))
        t_orig = np.linspace(0, 1, len(signal), endpoint=False)
        t_recon = np.linspace(0, 1, n_pts, endpoint=False)
        ax.plot(t_orig, signal.real, color="gray", linewidth=0.5, alpha=0.5, label="Original")
        ax.plot(t_recon, recon.real, color=BLUE, linewidth=1.2, label=f"$N = {args.harmonics}$")
        ax.set_xlabel("$t$")
        ax.set_ylabel("$f(t)$")
        ax.legend()
        ax.grid(True, alpha=0.2)
        fig.tight_layout()
        fig.savefig(args.output)
        plt.close(fig)
        print(f"Saved: {args.output}")

    return 0


def _cmd_animate(args: argparse.Namespace) -> int:
    """Render an epicycle animation from an image."""
    from fourier_analysis.animation import FourierAnimation
    from fourier_analysis.contours import extract_contours, resample_arc_length
    from fourier_analysis.epicycles import EpicycleChain
    from fourier_analysis.shortest_tour import order_contours

    image_path = Path(args.image)
    if not image_path.exists():
        print(f"Image not found: {image_path}")
        return 1

    contours = extract_contours(
        image_path,
        strategy=args.strategy,
        resize=args.resize,
        blur_sigma=args.blur,
    )

    if not contours:
        print("No contours extracted.")
        return 1

    print(f"Extracted {len(contours)} contour(s)")

    path = order_contours(contours)
    path = resample_arc_length(path, args.points)

    chain = EpicycleChain.from_signal(path, n_harmonics=args.harmonics)
    print(f"Epicycle chain: {len(chain)} components")

    output = Path(args.output) if args.output else None
    writer = "pillow" if output and output.suffix == ".gif" else "ffmpeg"

    anim = FourierAnimation(
        chain,
        fps=args.fps,
        duration=args.duration,
        max_circles=args.max_circles,
    )
    anim.render(output=output, writer=writer)

    if output:
        print(f"Saved: {output}")
    return 0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _plot_reconstruction(
    original: np.ndarray,
    recon: np.ndarray,
    n_harmonics: int,
    output: str | Path | None,
) -> None:
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


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fourier",
        description="Companion CLI for 'An Introduction to Fourier Analysis'.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # -- figures --
    p_fig = sub.add_parser("figures", help="Generate paper figures")
    p_fig.add_argument(
        "--only", nargs="+", metavar="FIG",
        help="Generate only these figures (e.g. F02 F19)",
    )

    # -- epicycles --
    p_epi = sub.add_parser("epicycles", help="Epicycle reconstruction from image")
    p_epi.add_argument("image", help="Input image (PNG, JPG, BMP, TIFF)")
    p_epi.add_argument("-n", "--harmonics", type=int, default=200, help="Number of harmonics (default: 200)")
    p_epi.add_argument("-p", "--points", type=int, default=1024, help="Resampled contour points (default: 1024)")
    p_epi.add_argument("-o", "--output", help="Output image path (PNG/PDF); omit for interactive display")
    p_epi.add_argument("--strategy", default="auto", choices=["auto", "threshold", "multi_threshold", "canny"],
                        help="Contour extraction strategy (default: auto)")
    p_epi.add_argument("--resize", type=int, default=512, help="Resize longest dimension (default: 512)")
    p_epi.add_argument("--blur", type=float, default=1.0, help="Gaussian pre-blur sigma (default: 1.0)")
    p_epi.add_argument("--min-length", type=int, default=40, help="Minimum contour length (default: 40)")

    # -- series --
    p_ser = sub.add_parser("series", help="Fourier coefficients from signal file")
    p_ser.add_argument("file", help="Text file with one sample per line (complex: a+bj)")
    p_ser.add_argument("-n", "--harmonics", type=int, default=None, help="Number of harmonics (default: all)")
    p_ser.add_argument("-p", "--points", type=int, default=None, help="Reconstruction points (default: signal length)")
    p_ser.add_argument("-o", "--output", help="Output plot path (PNG/PDF)")

    # -- animate --
    p_anim = sub.add_parser("animate", help="Render epicycle animation from image")
    p_anim.add_argument("image", help="Input image (PNG, JPG, BMP, TIFF)")
    p_anim.add_argument("-n", "--harmonics", type=int, default=200, help="Number of harmonics (default: 200)")
    p_anim.add_argument("-p", "--points", type=int, default=1024, help="Resampled contour points (default: 1024)")
    p_anim.add_argument("-o", "--output", help="Output video path (MP4/GIF); omit for interactive")
    p_anim.add_argument("--strategy", default="auto", choices=["auto", "threshold", "multi_threshold", "canny"],
                        help="Contour extraction strategy (default: auto)")
    p_anim.add_argument("--resize", type=int, default=512, help="Resize longest dimension (default: 512)")
    p_anim.add_argument("--blur", type=float, default=1.0, help="Gaussian pre-blur sigma (default: 1.0)")
    p_anim.add_argument("--duration", type=float, default=30.0, help="Animation duration in seconds (default: 30)")
    p_anim.add_argument("--fps", type=int, default=30, help="Frames per second (default: 30)")
    p_anim.add_argument("--max-circles", type=int, default=80, help="Max visible epicycles (default: 80)")

    # -- bases --
    p_bases = sub.add_parser("bases", help="Compare basis approximations for an image")
    p_bases.add_argument("image", help="Input image (PNG, JPG, BMP, TIFF)")
    p_bases.add_argument("-n", "--harmonics", type=int, default=200, help="Number of harmonics (default: 200)")
    p_bases.add_argument("-p", "--points", type=int, default=1024, help="Resampled contour points (default: 1024)")
    p_bases.add_argument("-o", "--output", help="Output image path (PNG/PDF)")
    p_bases.add_argument("--degrees", default="3,10,50,200", help="Comma-separated degrees (default: 3,10,50,200)")
    p_bases.add_argument("--strategy", default="auto", choices=["auto", "threshold", "multi_threshold", "canny"])
    p_bases.add_argument("--resize", type=int, default=512)
    p_bases.add_argument("--blur", type=float, default=1.0)
    p_bases.add_argument("--min-length", type=int, default=40)

    return parser


def _cmd_bases(args: argparse.Namespace) -> int:
    """Compare basis approximations for an image contour."""
    from fourier_analysis.bases import approximate_curve, evaluate_partial_sum
    from fourier_analysis.contours import extract_contours, resample_arc_length
    from fourier_analysis.shortest_tour import order_contours

    image_path = Path(args.image)
    if not image_path.exists():
        print(f"Image not found: {image_path}")
        return 1

    contours = extract_contours(
        image_path,
        strategy=args.strategy,
        resize=args.resize,
        blur_sigma=args.blur,
        min_contour_length=args.min_length,
    )

    if not contours:
        print("No contours extracted.")
        return 1

    print(f"Extracted {len(contours)} contour(s)")
    path = order_contours(contours)
    path = resample_arc_length(path, args.points)

    degrees = [int(d) for d in args.degrees.split(",")]
    approx = approximate_curve(path, max_degree=max(degrees), n_harmonics=max(degrees))

    import matplotlib.pyplot as plt
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
    if args.output:
        fig.savefig(args.output)
        plt.close(fig)
        print(f"Saved: {args.output}")
    else:
        plt.show()

    return 0


DISPATCH = {
    "figures": _cmd_figures,
    "epicycles": _cmd_epicycles,
    "series": _cmd_series,
    "animate": _cmd_animate,
    "bases": _cmd_bases,
}


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return DISPATCH[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
