"""Compute endpoints for contours, epicycles, and basis decompositions."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from api.dependencies import get_session
from api.models.computation import (
    ComputeBasesRequest,
    ComputeContourRequest,
    ComputeEpicyclesRequest,
    ComputeResult,
)
from api.services import computation

router = APIRouter(prefix="/api/sessions/{slug}/compute", tags=["compute"])


def _get_image_path(session: dict) -> Path:
    if not session.get("image"):
        raise HTTPException(status_code=400, detail="No image uploaded for this session")
    path = Path(session["image"]["path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Image file not found on disk")
    return path


@router.post("/contours", response_model=ComputeResult)
async def compute_contours(slug: str, req: ComputeContourRequest):
    session = await get_session(slug)
    image_path = _get_image_path(session)
    data = await computation.compute_contours(
        image_path,
        strategy=req.strategy,
        resize=req.resize,
        blur_sigma=req.blur_sigma,
        n_classes=req.n_classes,
        min_contour_length=req.min_contour_length,
    )
    return ComputeResult(data=data)


@router.post("/epicycles", response_model=ComputeResult)
async def compute_epicycles(slug: str, req: ComputeEpicyclesRequest):
    session = await get_session(slug)
    image_path = _get_image_path(session)
    params = session.get("parameters", {})
    data = await computation.compute_epicycles(
        image_path,
        n_harmonics=req.n_harmonics,
        n_points=req.n_points,
        strategy=params.get("strategy", "auto"),
        resize=params.get("resize", 512),
        blur_sigma=params.get("blur_sigma", 1.0),
        min_contour_length=params.get("min_contour_length", 40),
    )
    return ComputeResult(data=data)


@router.post("/bases", response_model=ComputeResult)
async def compute_bases(slug: str, req: ComputeBasesRequest):
    session = await get_session(slug)
    image_path = _get_image_path(session)
    params = session.get("parameters", {})
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
    return ComputeResult(data=data)
