"""LaTeX output formatting for Fourier series.

Provides two rendering modes:
  - **expanded**: first few terms with computed numerical coefficients + cdots
  - **sigma**: compact Σ notation with symbolic a_n, b_n, c_n placeholders
"""

from __future__ import annotations

from fourier_analysis.symbolic.models import FourierTerm
from fourier_analysis.symbolic.latex_format import (
    format_number,
    format_coefficient,
    extract_trig_pairs,
)


# ─────────────────────────── Expanded renderers ───────────────────────────


def render_trig(
    terms: list[FourierTerm],
    variable: str = "t",
    compact: bool = True,
) -> str:
    """Expanded trig: first few computed a_n cos(nt) + b_n sin(nt) + cdots."""
    if not terms:
        return "0"

    a0_half, pairs = extract_trig_pairs(terms)
    parts: list[str] = []
    max_terms = 4

    if a0_half is not None:
        parts.append(rf"\frac{{{format_number(a0_half)}}}{{2}}")

    max_amp = max((abs(a) + abs(b) for _, a, b in pairs), default=0)
    threshold = max_amp * 0.005
    term_count = 0

    for k, a_n, b_n in pairs:
        first = len(parts) == 0
        n_str = str(k) if k > 1 else ""
        omega_t = rf"{n_str}{variable}"

        if abs(a_n) > threshold:
            parts.append(rf"{format_coefficient(a_n, first=first)}\cos({omega_t})")
            first = False
            term_count += 1
        if abs(b_n) > threshold:
            parts.append(rf"{format_coefficient(b_n, first=first)}\sin({omega_t})")
            term_count += 1
        if term_count >= max_terms:
            parts.append(r"\cdots")
            break

    return " ".join(parts) if parts else "0"


def render_exponential(
    terms: list[FourierTerm],
    variable: str = "t",
    compact: bool = True,
) -> str:
    """Expanded exponential: first few c_n e^{int} + cdots."""
    if not terms:
        return "0"

    parts: list[str] = []
    max_amp = max((t.amplitude for t in terms), default=0)
    threshold = max_amp * 0.005
    shown = 0

    for i, t in enumerate(terms):
        if t.amplitude < threshold and t.n != 0:
            continue
        first = len(parts) == 0
        re, im = t.coefficient.real, t.coefficient.imag

        if abs(im) < 1e-14:
            coeff_str = format_coefficient(re, first=first)
        elif abs(re) < 1e-14:
            val = im
            if abs(val - 1.0) < 1e-10:
                coeff_str = ("" if first else "+") + "i"
            elif abs(val + 1.0) < 1e-10:
                coeff_str = "-i"
            else:
                coeff_str = format_number(val) + "i"
                if not first and not coeff_str.startswith("-"):
                    coeff_str = "+" + coeff_str
        else:
            coeff_str = f"({format_number(re)}{'+' if im >= 0 else ''}{format_number(im)}i)"
            if not first:
                coeff_str = "+" + coeff_str

        if t.n == 0:
            parts.append(coeff_str if coeff_str else format_number(re))
        else:
            n_str = str(t.n) if abs(t.n) > 1 else ("-" if t.n == -1 else "")
            parts.append(rf"{coeff_str}e^{{i{n_str}{variable}}}")

        shown += 1
        if shown >= 4:
            parts.append(r"\cdots")
            break

    return " ".join(parts) if parts else "0"


def render_polar(
    terms: list[FourierTerm],
    variable: str = "t",
    compact: bool = True,
) -> str:
    """Expanded polar: first few A_n e^{i(nt + phi)} + cdots."""
    if not terms:
        return "0"

    parts: list[str] = []
    max_amp = max((t.amplitude for t in terms), default=0)
    threshold = max_amp * 0.005
    shown = 0

    for i, t in enumerate(terms):
        if t.amplitude < threshold and t.n != 0:
            continue
        first = len(parts) == 0
        A_str = format_coefficient(t.amplitude, first=first)

        if t.n == 0:
            parts.append(A_str if A_str else format_number(t.amplitude))
        else:
            n_str = str(t.n) if abs(t.n) > 1 else ("-" if t.n == -1 else "")
            if abs(t.phase) < 1e-10:
                parts.append(rf"{A_str}e^{{i{n_str}{variable}}}")
            else:
                phi_str = format_number(t.phase)
                if not phi_str.startswith("-"):
                    phi_str = "+" + phi_str
                parts.append(rf"{A_str}e^{{i({n_str}{variable}{phi_str})}}")

        shown += 1
        if shown >= 4:
            parts.append(r"\cdots")
            break

    return " ".join(parts) if parts else "0"


# ──────────────────────────── Sigma renderers ─────────────────────────────


def render_trig_sigma(
    terms: list[FourierTerm],
    variable: str = "t",
    compact: bool = True,
) -> str:
    r"""Sigma notation with hoverable a_n / b_n via \htmlClass."""
    if not terms:
        return "0"

    a0_half, pairs = extract_trig_pairs(terms)
    if not pairs:
        if a0_half is not None:
            return rf"\frac{{{format_number(a0_half)}}}{{2}}"
        return "0"

    N = max(k for k, _, _ in pairs)
    parts: list[str] = []
    if a0_half is not None:
        parts.append(rf"\frac{{{format_number(a0_half)}}}{{2}}")

    # Wrap a_n / b_n in \htmlClass for frontend hover interactivity
    an = r"\htmlClass{eq-coeff eq-an}{a_n}"
    bn = r"\htmlClass{eq-coeff eq-bn}{b_n}"

    # Use relative threshold (0.5% of max) to elide negligible terms (spline noise)
    max_amp = max(abs(a) + abs(b) for _, a, b in pairs)
    elide_thresh = max_amp * 0.005
    all_a_zero = all(abs(a) < elide_thresh for _, a, _ in pairs)
    all_b_zero = all(abs(b) < elide_thresh for _, _, b in pairs)

    if all_a_zero:
        sigma = rf"\sum_{{n=1}}^{{{N}}} {bn} \sin(n{variable})"
    elif all_b_zero:
        sigma = rf"\sum_{{n=1}}^{{{N}}} {an} \cos(n{variable})"
    else:
        sigma = (
            rf"\sum_{{n=1}}^{{{N}}} "
            rf"\!\left( {an} \cos(n{variable}) + {bn} \sin(n{variable}) \right)"
        )

    if parts:
        return parts[0] + " + " + sigma
    return sigma


def render_exponential_sigma(
    terms: list[FourierTerm],
    variable: str = "t",
    compact: bool = True,
) -> str:
    """Sigma notation: Σ c_n e^{int}."""
    if not terms:
        return "0"

    harmonics = [t for t in terms if t.n != 0]
    if len(harmonics) < 2:
        return render_exponential(terms, variable, compact)

    ns = sorted(t.n for t in harmonics)
    N_pos = max(ns) if any(n > 0 for n in ns) else 0
    N_neg = abs(min(ns)) if any(n < 0 for n in ns) else 0

    cn = r"\htmlClass{eq-coeff eq-cn}{c_n}"

    if N_neg > 0 and N_pos > 0 and N_neg == N_pos:
        return rf"\sum_{{n=-{N_pos}}}^{{{N_pos}}} {cn} \, e^{{in{variable}}}"
    elif N_pos > 0:
        dc = [t for t in terms if t.n == 0]
        parts: list[str] = []
        if dc and abs(dc[0].coefficient.real) > 1e-14:
            parts.append(format_number(dc[0].coefficient.real))
        parts.append(rf"\sum_{{n=1}}^{{{N_pos}}} {cn} \, e^{{in{variable}}}")
        return " + ".join(parts)

    return render_exponential(terms, variable, compact)


def render_polar_sigma(
    terms: list[FourierTerm],
    variable: str = "t",
    compact: bool = True,
) -> str:
    """Sigma notation: Σ A_n e^{i(nt + φ_n)}."""
    if not terms:
        return "0"

    harmonics = [t for t in terms if t.n != 0]
    if len(harmonics) < 2:
        return render_polar(terms, variable, compact)

    ns = sorted(t.n for t in harmonics)
    N_pos = max(ns) if any(n > 0 for n in ns) else 0
    N_neg = abs(min(ns)) if any(n < 0 for n in ns) else 0

    An = r"\htmlClass{eq-coeff eq-An}{A_n}"

    if N_neg > 0 and N_pos > 0 and N_neg == N_pos:
        return rf"\sum_{{n=-{N_pos}}}^{{{N_pos}}} {An} \, e^{{i(n{variable} + \varphi_n)}}"
    elif N_pos > 0:
        dc = [t for t in terms if t.n == 0]
        parts: list[str] = []
        if dc and dc[0].amplitude > 1e-14:
            parts.append(format_number(dc[0].amplitude))
        parts.append(
            rf"\sum_{{n=1}}^{{{N_pos}}} {An} \, e^{{i(n{variable} + \varphi_n)}}"
        )
        return " + ".join(parts)

    return render_polar(terms, variable, compact)


# ─────────────────────────── Public API ───────────────────────────────────


_EXPANDED = {"trig": render_trig, "exponential": render_exponential, "polar": render_polar}
_SIGMA = {"trig": render_trig_sigma, "exponential": render_exponential_sigma, "polar": render_polar_sigma}


def render_latex(
    terms: list[FourierTerm],
    notation: str = "trig",
    budget: int = 10,
    variable: str = "t",
    compact: bool = True,
) -> str:
    """Render Fourier terms as expanded LaTeX (individual terms + cdots)."""
    renderer = _EXPANDED.get(notation, render_trig)
    latex = renderer(terms, variable, compact=compact)
    return f"f({variable}) \\approx {latex}"


def render_latex_sigma(
    terms: list[FourierTerm],
    notation: str = "trig",
    variable: str = "t",
) -> str:
    """Render Fourier terms in sigma notation."""
    renderer = _SIGMA.get(notation, render_trig_sigma)
    latex = renderer(terms, variable)
    return f"f({variable}) \\approx {latex}"
