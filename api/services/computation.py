"""Wraps fourier_analysis library for async compute endpoints."""

from __future__ import annotations

import asyncio
import hashlib
import io
import json
from pathlib import Path
from typing import Any

import numpy as np
from cachetools import TTLCache

from fourier_analysis.bases import approximate_curve, build_animation_data
from fourier_analysis.contours import ContourStrategy, extract_contours, resample_arc_length
from fourier_analysis.epicycles import EpicycleChain
from fourier_analysis.shortest_tour import order_contours

_cache: TTLCache = TTLCache(maxsize=100, ttl=3600)


def _cache_key(image_bytes: bytes, params: dict) -> str:
    h = hashlib.sha256(image_bytes)
    h.update(json.dumps(params, sort_keys=True).encode())
    return h.hexdigest()


async def compute_contours(
    image_path: Path,
    strategy: str = "auto",
    resize: int = 512,
    blur_sigma: float = 1.0,
    n_classes: int = 3,
    min_contour_length: int = 40,
) -> dict[str, Any]:
    def _run():
        contours = extract_contours(
            image_path,
            strategy=strategy,
            resize=resize,
            blur_sigma=blur_sigma,
            n_classes=n_classes,
            min_contour_length=min_contour_length,
        )
        return [
            {"x": c.real.tolist(), "y": c.imag.tolist(), "n_points": len(c)}
            for c in contours
        ]

    contour_data = await asyncio.to_thread(_run)
    return {"n_contours": len(contour_data), "contours": contour_data}


async def compute_epicycles(
    image_path: Path,
    n_harmonics: int = 200,
    n_points: int = 1024,
    strategy: str = "auto",
    resize: int = 512,
    blur_sigma: float = 1.0,
    min_contour_length: int = 40,
) -> dict[str, Any]:
    def _run():
        contours = extract_contours(
            image_path,
            strategy=strategy,
            resize=resize,
            blur_sigma=blur_sigma,
            min_contour_length=min_contour_length,
        )
        if not contours:
            return {"error": "No contours extracted"}

        path = order_contours(contours)
        path = resample_arc_length(path, n_points)
        chain = EpicycleChain.from_signal(path, n_harmonics=n_harmonics)

        components = [
            {
                "frequency": c.frequency,
                "coefficient": [c.coefficient.real, c.coefficient.imag],
                "amplitude": c.amplitude,
                "phase": c.phase,
            }
            for c in chain.components
        ]

        ts = np.linspace(0, 1, 3000, endpoint=False)
        trace = chain.evaluate(ts)

        return {
            "n_components": len(components),
            "components": components,
            "trace": {"x": trace.real.tolist(), "y": trace.imag.tolist()},
            "path": {"x": path.real.tolist(), "y": path.imag.tolist()},
        }

    return await asyncio.to_thread(_run)


async def compute_bases(
    image_path: Path,
    max_degree: int = 200,
    n_points: int = 1024,
    strategy: str = "auto",
    resize: int = 512,
    blur_sigma: float = 1.0,
    min_contour_length: int = 40,
    levels: list[int] | None = None,
    n_eval: int = 1000,
) -> dict[str, Any]:
    def _run():
        contours = extract_contours(
            image_path,
            strategy=strategy,
            resize=resize,
            blur_sigma=blur_sigma,
            min_contour_length=min_contour_length,
        )
        if not contours:
            return {"error": "No contours extracted"}

        path = order_contours(contours)
        path = resample_arc_length(path, n_points)
        return build_animation_data(path, max_degree, levels=levels, n_eval=n_eval)

    return await asyncio.to_thread(_run)
