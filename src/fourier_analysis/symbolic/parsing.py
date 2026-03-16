"""Safe expression parsing using sympy.sympify with a restricted namespace."""

from __future__ import annotations

import re
from tokenize import TokenError

import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication,
    convert_xor,
)

# Restricted namespace: only safe mathematical functions and constants.
SAFE_NAMESPACE: dict[str, object] = {
    # Variables
    "x": sp.Symbol("x"),
    "t": sp.Symbol("t"),
    "n": sp.Symbol("n", integer=True),
    # Functions
    "sin": sp.sin,
    "cos": sp.cos,
    "tan": sp.tan,
    "exp": sp.exp,
    "log": sp.log,
    "ln": sp.log,
    "sqrt": sp.sqrt,
    "abs": sp.Abs,
    "Abs": sp.Abs,
    "sign": sp.sign,
    "floor": sp.floor,
    "ceil": sp.ceiling,
    "Piecewise": sp.Piecewise,
    "Heaviside": sp.Heaviside,
    # Constants
    "pi": sp.pi,
    "e": sp.E,
    "E": sp.E,
    "I": sp.I,
    "oo": sp.oo,
    # Trig inverses
    "asin": sp.asin,
    "acos": sp.acos,
    "atan": sp.atan,
    "atan2": sp.atan2,
    # Hyperbolic
    "sinh": sp.sinh,
    "cosh": sp.cosh,
    "tanh": sp.tanh,
}


def parse_expression(expr_str: str) -> sp.Expr:
    """Parse a user-supplied string into a sympy expression.

    Uses sympify with a restricted local namespace to prevent arbitrary
    code execution. Only mathematical functions and constants are available.

    Parameters
    ----------
    expr_str : str
        Mathematical expression, e.g. "x*(pi - x)" or "sin(2*x) + cos(3*x)".

    Returns
    -------
    sp.Expr
        Parsed sympy expression.

    Raises
    ------
    ValueError
        If the expression cannot be parsed or contains forbidden constructs.
    """
    expr_str = expr_str.strip()
    if not expr_str:
        raise ValueError("Empty expression")

    # Block obvious code injection patterns
    for forbidden in ("import", "__", "eval", "exec", "compile", "open", "system"):
        if forbidden in expr_str.lower():
            raise ValueError(f"Forbidden construct: {forbidden}")

    # Normalize common shorthand: ^ → ** for exponentiation
    # Insert implicit multiplication: 2x → 2*x, 3pi → 3*pi, xsin → x*sin
    transformations = standard_transformations + (implicit_multiplication, convert_xor)

    try:
        expr = parse_expr(expr_str, local_dict=SAFE_NAMESPACE, transformations=transformations)
    except (sp.SympifyError, SyntaxError, TypeError, TokenError) as e:
        raise ValueError(f"Cannot parse expression: {e}") from e

    return expr
