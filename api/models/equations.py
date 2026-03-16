"""Request/response models for the equation endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class FourierTermDTO(BaseModel):
    n: int
    coefficient_re: float
    coefficient_im: float
    amplitude: float
    phase: float


class ComputeEquationRequest(BaseModel):
    expression: str
    domain_start: float = 0.0
    domain_end: float = Field(default=6.283185307179586)  # 2π
    n_harmonics: int = Field(default=20, ge=1, le=200)
    n_eval_points: int = Field(default=500, ge=50, le=5000)
    notation: str = Field(default="trig", pattern=r"^(trig|exponential|polar)$")
    budget: int = Field(default=10, ge=2, le=50)


class ComputeEquationResponse(BaseModel):
    status: str
    tier: str  # "symbolic" | "identified" | "spline"
    latex: str
    latex_sigma: str  # sigma-notation form with approximate c_n
    coefficients: list[FourierTermDTO]
    original_points: dict[str, list[float]]
    reconstructed_points: dict[str, list[float]]
    energy_captured: float
    effective_n: int  # harmonics needed for ~99.5% energy


class SimplifyRequest(BaseModel):
    coefficients: list[FourierTermDTO]
    budget: int = Field(default=6, ge=2, le=50)
    notation: str = Field(default="trig", pattern=r"^(trig|exponential|polar)$")


class SimplifyResponse(BaseModel):
    latex: str
    energy_captured: float
    term_count: int
