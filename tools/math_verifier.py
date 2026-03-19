"""
tools/math_verifier.py — SymPy-based symbolic math verification.

Checks user answers against expected solutions using symbolic simplification.
"""

import sympy as sp
from sympy.parsing.sympy_parser import (
    parse_expr,
    standard_transformations,
    implicit_multiplication_application,
    convert_xor,
)

TRANSFORMS = standard_transformations + (
    implicit_multiplication_application,
    convert_xor,
)

# Common symbols pre-declared for user convenience
x, y, z, t, n, k = sp.symbols("x y z t n k")
SYMBOL_MAP = {"x": x, "y": y, "z": z, "t": t, "n": n, "k": k}


class MathVerifier:
    """Symbolic and numeric math answer verification."""

    @staticmethod
    def _clean_input(expr_str: str) -> str:
        """Replace unicode superscripts and common notation with Python equivalents."""
        replacements = {
            "⁰": "**0", "¹": "**1", "²": "**2", "³": "**3", "⁴": "**4",
            "⁵": "**5", "⁶": "**6", "⁷": "**7", "⁸": "**8", "⁹": "**9",
            "^": "**",
        }
        for old, new in replacements.items():
            expr_str = expr_str.replace(old, new)
        return expr_str

    @staticmethod
    def parse(expr_str: str) -> sp.Expr:
        """Parse a string expression into a SymPy expression."""
        try:
            cleaned = MathVerifier._clean_input(expr_str)
            return parse_expr(cleaned, local_dict=SYMBOL_MAP, transformations=TRANSFORMS)
        except Exception as e:
            raise ValueError(f"Could not parse '{expr_str}': {e}")

    @staticmethod
    def verify_symbolic(expected: str, user_answer: str) -> tuple[bool, str]:
        """
        Check if two symbolic expressions are mathematically equivalent.

        Returns (is_correct, explanation).
        """
        try:
            expected_expr = MathVerifier.parse(expected)
            user_expr = MathVerifier.parse(user_answer)

            diff = sp.simplify(expected_expr - user_expr)
            is_correct = diff == 0

            if is_correct:
                return True, f"✅ Correct! {user_expr} equals {expected_expr}."
            else:
                # Try expanding both sides as a further check
                diff_expanded = sp.expand(expected_expr - user_expr)
                if diff_expanded == 0:
                    return True, f"✅ Correct! {user_expr} simplifies to {expected_expr}."

                return False, (
                    f"❌ Not quite. Your answer: {user_expr}\n"
                    f"   Expected: {expected_expr}\n"
                    f"   Difference: {diff}"
                )
        except ValueError as e:
            return False, f"⚠️ Could not verify: {e}"
        except Exception as e:
            return False, f"⚠️ Verification error: {e}"

    @staticmethod
    def verify_numeric(expected: str, user_answer: str,
                       test_points: dict = None) -> tuple[bool, str]:
        """
        Numerically verify by substituting test points.

        Useful for expressions that are hard to simplify symbolically.
        """
        try:
            expected_expr = MathVerifier.parse(expected)
            user_expr = MathVerifier.parse(user_answer)

            if test_points is None:
                # Auto-generate test points for symbols found
                free_syms = expected_expr.free_symbols | user_expr.free_symbols
                import random
                test_points_list = [
                    {s: random.uniform(0.5, 5.0) for s in free_syms}
                    for _ in range(5)
                ]
            else:
                test_points_list = [test_points]

            for pts in test_points_list:
                val_expected = complex(expected_expr.subs(pts))
                val_user = complex(user_expr.subs(pts))
                if abs(val_expected - val_user) > 1e-6:
                    return False, (
                        f"❌ Mismatch at {pts}:\n"
                        f"   Expected value: {val_expected}\n"
                        f"   Your value: {val_user}"
                    )

            return True, f"✅ Correct! Numeric verification passed across {len(test_points_list)} test points."
        except Exception as e:
            return False, f"⚠️ Numeric verification error: {e}"

    @staticmethod
    def solve_equation(equation_str: str, var: str = "x") -> str:
        """Solve an equation and return the solution (for hint generation, not for user)."""
        try:
            sym = SYMBOL_MAP.get(var, sp.Symbol(var))
            expr = MathVerifier.parse(equation_str)
            solutions = sp.solve(expr, sym)
            return f"Solutions for {var}: {solutions}"
        except Exception as e:
            return f"Could not solve: {e}"

    @staticmethod
    def compute_derivative(expr_str: str, var: str = "x") -> str:
        """Compute a derivative (for generating hints)."""
        try:
            sym = SYMBOL_MAP.get(var, sp.Symbol(var))
            expr = MathVerifier.parse(expr_str)
            result = sp.diff(expr, sym)
            return str(result)
        except Exception as e:
            return f"Could not differentiate: {e}"

    @staticmethod
    def compute_integral(expr_str: str, var: str = "x") -> str:
        """Compute an integral (for generating hints)."""
        try:
            sym = SYMBOL_MAP.get(var, sp.Symbol(var))
            expr = MathVerifier.parse(expr_str)
            result = sp.integrate(expr, sym)
            return str(result)
        except Exception as e:
            return f"Could not integrate: {e}"
