"""Compute endpoints for contours, epicycles, and basis decompositions."""

from __future__ import annotations

import os

from fastapi import APIRouter

from api.dependencies import get_session
from api.models.computation import (
    ComputeBasesRequest,
    ComputeContourRequest,
    ComputeEpicyclesRequest,
    ComputeResult,
)
from api.services import computation
from api.services.image_storage import download_to_tempfile

router = APIRouter(prefix="/api/sessions/{slug}/compute", tags=["compute"])


@router.post("/contours", response_model=ComputeResult)
async def compute_contours(slug: str, req: ComputeContourRequest):
    session = await get_session(slug)
    image_path = await download_to_tempfile(session)
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
    image_path = await download_to_tempfile(session)
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
    image_path = await download_to_tempfile(session)
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
