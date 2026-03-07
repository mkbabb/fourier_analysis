"""Compute endpoints for contours, epicycles, and basis decompositions."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from bson import ObjectId
from fastapi import APIRouter, HTTPException

from api.dependencies import get_gridfs, get_session
from api.models.computation import (
    ComputeBasesRequest,
    ComputeContourRequest,
    ComputeEpicyclesRequest,
    ComputeResult,
)
from api.services import computation

router = APIRouter(prefix="/api/sessions/{slug}/compute", tags=["compute"])


async def _get_image_path(session: dict) -> Path:
    """Download image from GridFS to a temporary file and return its path."""
    if not session.get("image"):
        raise HTTPException(
            status_code=400, detail="No image uploaded for this session"
        )

    image_meta = session["image"]
    if "file_id" not in image_meta:
        raise HTTPException(
            status_code=400,
            detail="Image stored in legacy format — please re-upload",
        )

    bucket = get_gridfs()
    file_id = image_meta["file_id"]

    try:
        grid_out = await bucket.open_download_stream(ObjectId(file_id))
    except Exception:
        raise HTTPException(status_code=404, detail="Image file not found in storage")

    data = await grid_out.read()

    # Determine extension from original name or content type
    original = session["image"].get("original_name", "image.png")
    ext = Path(original).suffix.lower() or ".png"

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
    tmp.write(data)
    tmp.close()
    return Path(tmp.name)


@router.post("/contours", response_model=ComputeResult)
async def compute_contours(slug: str, req: ComputeContourRequest):
    session = await get_session(slug)
    image_path = await _get_image_path(session)
    try:
        data = await computation.compute_contours(
            image_path,
            strategy=req.strategy,
            resize=req.resize,
            blur_sigma=req.blur_sigma,
            n_classes=req.n_classes,
            min_contour_length=req.min_contour_length,
        )
    finally:
        os.unlink(image_path)
    return ComputeResult(data=data)


@router.post("/epicycles", response_model=ComputeResult)
async def compute_epicycles(slug: str, req: ComputeEpicyclesRequest):
    session = await get_session(slug)
    image_path = await _get_image_path(session)
    params = session.get("parameters", {})
    try:
        data = await computation.compute_epicycles(
            image_path,
            n_harmonics=req.n_harmonics,
            n_points=req.n_points,
            strategy=params.get("strategy", "auto"),
            resize=params.get("resize", 512),
            blur_sigma=params.get("blur_sigma", 1.0),
            min_contour_length=params.get("min_contour_length", 40),
        )
    finally:
        os.unlink(image_path)
    return ComputeResult(data=data)


@router.post("/bases", response_model=ComputeResult)
async def compute_bases(slug: str, req: ComputeBasesRequest):
    session = await get_session(slug)
    image_path = await _get_image_path(session)
    params = session.get("parameters", {})
    try:
        data = await computation.compute_bases(
            image_path,
            max_degree=req.max_degree,
            n_points=req.n_points,
            strategy=params.get("strategy", "auto"),
            resize=params.get("resize", 512),
            blur_sigma=params.get("blur_sigma", 1.0),
            min_contour_length=params.get("min_contour_length", 40),
            levels=req.levels,
            n_eval=req.n_eval,
        )
    finally:
        os.unlink(image_path)
    return ComputeResult(data=data)
