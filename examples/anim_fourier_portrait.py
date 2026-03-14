"""Animate epicycles tracing the Fourier portrait image.

Usage:
    uv run python examples/anim_fourier_portrait.py [--output fourier_portrait.mp4]
"""

from __future__ import annotations

import argparse
from pathlib import Path

from fourier_analysis.animation import FourierAnimation
from fourier_analysis.contours import extract_contours
from fourier_analysis.epicycles import EpicycleChain
from fourier_analysis.shortest_tour import build_contour_tour


def main() -> None:
    parser = argparse.ArgumentParser(description="Animate epicycles tracing Fourier portrait")
    parser.add_argument(
        "--image",
        type=Path,
        default=Path(__file__).parent.parent / "assets" / "fourier.png",
        help="Input image path",
    )
    parser.add_argument("--output", type=Path, default=None, help="Output video path")
    parser.add_argument("--harmonics", type=int, default=200, help="Number of harmonics")
    parser.add_argument("--duration", type=float, default=30.0, help="Duration in seconds")
    args = parser.parse_args()

    print(f"Extracting contours from {args.image}...")
    contours = extract_contours(args.image, canny_sigma=2.0, resize=256)
    print(f"Found {len(contours)} contours, {sum(len(c) for c in contours)} total points")

    path = build_contour_tour(contours).path
    print(f"Ordered path: {len(path)} points")

    chain = EpicycleChain.from_signal(path, n_harmonics=args.harmonics)
    print(f"Built epicycle chain with {len(chain)} components")

    anim = FourierAnimation(chain, duration=args.duration)
    anim.render(args.output)


if __name__ == "__main__":
    main()
