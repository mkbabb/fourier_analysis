"""FastAPI application entry point."""

from __future__ import annotations

import asyncio
import logging
import traceback
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

from api.config import settings
from api.routers import contours, equations, images, snapshots
from api.services.database import close_db, connect_db
from api.services.janitor import run_janitor


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    janitor_task = asyncio.create_task(run_janitor())
    yield
    janitor_task.cancel()
    await close_db()


app = FastAPI(
    title="Fourier Analysis API",
    version="0.2.0",
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(images.router)
app.include_router(contours.router)
app.include_router(snapshots.router)
app.include_router(equations.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception on %s %s:\n%s", request.method, request.url.path, traceback.format_exc())
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.get("/api/health")
async def health():
    return {"status": "ok"}
