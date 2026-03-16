"""Equation computation and simplification endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from api.models.equations import (
    ComputeEquationRequest,
    ComputeEquationResponse,
    FourierTermDTO,
    SimplifyRequest,
    SimplifyResponse,
)
from api.services.computation import submit_compute_job

router = APIRouter(prefix="/api/equations", tags=["equations"])


def _term_to_dto(term) -> FourierTermDTO:
    return FourierTermDTO(
        n=term.n,
        coefficient_re=term.coefficient.real,
        coefficient_im=term.coefficient.imag,
        amplitude=term.amplitude,
        phase=term.phase,
    )


@router.post("/compute", response_model=ComputeEquationResponse)
async def compute_equation(req: ComputeEquationRequest) -> ComputeEquationResponse:
    """Compute closed-form Fourier series for a user-supplied f(x).

    Tries three tiers:
      1. Symbolic integration (exact)
      2. Sequence identification (conjectured)
      3. Spline approximation (approximate)
    """

    def _run():
        import numpy as np

        from fourier_analysis.symbolic.parsing import parse_expression
        from fourier_analysis.symbolic.integration import symbolic_fourier_coefficients
        from fourier_analysis.symbolic.identification import identify_sequence
        from fourier_analysis.symbolic.spline import spline_fourier_coefficients
        from fourier_analysis.symbolic.simplification import simplify_series
        from fourier_analysis.symbolic.models import FourierTerm

        import sympy as sp

        # Parse expression
        expr = parse_expression(req.expression)
        x = sp.Symbol("x")
        domain = (req.domain_start, req.domain_end)
        period = domain[1] - domain[0]

        # Evaluate original function on grid
        f_numpy = sp.lambdify(x, expr, modules=["numpy"])
        x_eval = np.linspace(domain[0], domain[1], req.n_eval_points, endpoint=False)
        try:
            raw = f_numpy(x_eval)
            y_eval = np.broadcast_to(
                np.asarray(raw, dtype=np.float64), x_eval.shape,
            ).copy()
        except Exception:
            y_eval = np.array([complex(expr.subs(x, xv)).real for xv in x_eval])

        # Tier 1: Symbolic integration
        tier = "symbolic"
        terms = symbolic_fourier_coefficients(expr, req.n_harmonics, domain, period)

        # Tier 2: Sequence identification
        if terms is None:
            tier = "identified"
            # Compute numerically via spline, then try to identify
            spline_terms = spline_fourier_coefficients(
                y_eval, x_eval, req.n_harmonics, period,
            )
            coeffs = [t.coefficient for t in spline_terms]
            indices = [t.n for t in spline_terms]
            terms = identify_sequence(coeffs, indices)

        # Tier 3: Spline fallback
        if terms is None:
            tier = "spline"
            terms = spline_fourier_coefficients(
                y_eval, x_eval, req.n_harmonics, period,
            )

        # Simplify and render
        latex, energy = simplify_series(terms, req.budget, req.notation)

        from fourier_analysis.symbolic.latex_rendering import render_latex_sigma
        from fourier_analysis.symbolic.simplification import compute_effective_n

        latex_sigma = render_latex_sigma(terms, req.notation)
        eff_n = compute_effective_n(terms)

        # Reconstruct from all terms
        y_recon = np.zeros_like(x_eval, dtype=complex)
        for t in terms:
            if t.n == 0:
                y_recon += t.coefficient
            else:
                y_recon += t.coefficient * np.exp(1j * t.n * 2 * np.pi / period * x_eval)

        return {
            "status": "ok",
            "tier": tier,
            "latex": latex,
            "latex_sigma": latex_sigma,
            "terms": terms,
            "original_points": {"x": x_eval.tolist(), "y": y_eval.tolist()},
            "reconstructed_points": {"x": x_eval.tolist(), "y": y_recon.real.tolist()},
            "energy_captured": energy,
            "effective_n": eff_n,
        }

    result = await submit_compute_job("equation", _run)

    return ComputeEquationResponse(
        status=result["status"],
        tier=result["tier"],
        latex=result["latex"],
        latex_sigma=result["latex_sigma"],
        coefficients=[_term_to_dto(t) for t in result["terms"]],
        original_points=result["original_points"],
        reconstructed_points=result["reconstructed_points"],
        energy_captured=result["energy_captured"],
        effective_n=result["effective_n"],
    )


@router.post("/simplify", response_model=SimplifyResponse)
async def simplify_coefficients(req: SimplifyRequest) -> SimplifyResponse:
    """Simplify existing DFT coefficients for display overlay."""

    def _run():
        from fourier_analysis.symbolic.simplification import simplify_numerical_coefficients

        coeffs = [
            {
                "n": c.n,
                "coefficient_re": c.coefficient_re,
                "coefficient_im": c.coefficient_im,
                "amplitude": c.amplitude,
                "phase": c.phase,
            }
            for c in req.coefficients
        ]

        latex, energy, term_count = simplify_numerical_coefficients(
            coeffs, req.budget, req.notation,
        )
        return {"latex": latex, "energy_captured": energy, "term_count": term_count}

    result = await submit_compute_job("simplify", _run)

    return SimplifyResponse(
        latex=result["latex"],
        energy_captured=result["energy_captured"],
        term_count=result["term_count"],
    )
