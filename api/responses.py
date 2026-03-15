"""Shared response builders for asset documents."""

from __future__ import annotations

from api.models.assets import ContourAssetResponse


def contour_points(asset: dict) -> tuple[list[float], list[float]]:
    points = asset.get("points", {})
    return points.get("x", []), points.get("y", [])


def contour_response(asset: dict) -> ContourAssetResponse:
    xs, ys = contour_points(asset)
    return ContourAssetResponse(
        contour_hash=asset["contour_hash"],
        image_slug=asset.get("image_slug"),
        source=asset["source"],
        point_count=asset["point_count"],
        bbox=asset["bbox"],
        image_bounds=asset.get("image_bounds"),
        preview_path=asset.get("preview_path", ""),
        created_at=asset["created_at"],
        last_accessed_at=asset["last_accessed_at"],
        points={"x": xs, "y": ys},
    )
