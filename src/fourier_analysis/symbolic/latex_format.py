"""Shared number/coefficient formatting for LaTeX output."""

from __future__ import annotations

import math


def format_number(val: float, sig_digits: int = 2) -> str:
    """Format a number for LaTeX display."""
    if abs(val) < 1e-14:
        return "0"
    if abs(val - round(val)) < 1e-10 and abs(val) < 1e6:
        return str(int(round(val)))
    if abs(val - math.pi) < 1e-10:
        return r"\pi"
    if abs(val + math.pi) < 1e-10:
        return r"-\pi"
    if abs(val - 2 * math.pi) < 1e-10:
        return r"2\pi"

    for denom in [2, 3, 4, 6]:
        ratio = val / math.pi
        if abs(ratio - round(ratio * denom) / denom) < 1e-10:
            num = round(ratio * denom)
            if num == 1:
                return rf"\frac{{\pi}}{{{denom}}}"
            if num == -1:
                return rf"-\frac{{\pi}}{{{denom}}}"
            return rf"\frac{{{num}\pi}}{{{denom}}}"

    return f"{val:.{sig_digits}g}"


def format_coefficient(val: float, first: bool = False) -> str:
    """Format a real coefficient with sign handling."""
    if abs(val - 1.0) < 1e-10:
        return "" if first else "+"
    if abs(val + 1.0) < 1e-10:
        return "-"
    s = format_number(val)
    if not first and not s.startswith("-"):
        s = "+" + s
    return s


def extract_trig_pairs(
    terms: list,
) -> tuple[float | None, list[tuple[int, float, float]]]:
    """Extract DC half-value and (k, a_k, b_k) pairs from FourierTerms."""
    dc = [t for t in terms if t.n == 0]
    harmonics = [t for t in terms if t.n != 0]

    a0_half: float | None = None
    if dc:
        a0 = 2 * dc[0].coefficient.real
        if abs(a0) > 1e-14:
            a0_half = a0

    seen: set[int] = set()
    pairs: list[tuple[int, float, float]] = []
    for t in harmonics:
        k = abs(t.n)
        if k in seen:
            continue
        seen.add(k)
        pos = next((h for h in harmonics if h.n == k), None)
        neg = next((h for h in harmonics if h.n == -k), None)
        c_pos = pos.coefficient if pos else 0j
        c_neg = neg.coefficient if neg else 0j
        a_n = (c_pos + c_neg).real
        b_n = (1j * (c_pos - c_neg)).real
        if abs(a_n) > 1e-14 or abs(b_n) > 1e-14:
            pairs.append((k, a_n, b_n))

    return a0_half, sorted(pairs, key=lambda p: p[0])
