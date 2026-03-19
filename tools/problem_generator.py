"""
tools/problem_generator.py — Generates math & physics practice problems.

Creates problems with known solutions for verification, organized by topic and difficulty.
"""

import random
import sympy as sp

x, y, z, t = sp.symbols("x y z t")


# ── Problem Templates ───────────────────────────────────────────────

PROBLEM_BANK = {
    "algebra": {
        1: [
            {"statement": "Solve for x: {a}x + {b} = {c}",
             "params": lambda: {"a": random.randint(2, 9), "b": random.randint(1, 20), "c": random.randint(10, 50)},
             "solution": lambda p: f"x = {(p['c'] - p['b']) / p['a']}",
             "hint": "Isolate x by moving constants to the other side."},
            {"statement": "Simplify: ({a}x + {b})({c}x - {d})",
             "params": lambda: {"a": random.randint(1, 5), "b": random.randint(1, 5),
                                "c": random.randint(1, 5), "d": random.randint(1, 5)},
             "solution": lambda p: str(sp.expand((p["a"]*x + p["b"]) * (p["c"]*x - p["d"]))),
             "hint": "Use FOIL method: First, Outer, Inner, Last."},
        ],
        2: [
            {"statement": "Factor completely: x² + {b}x + {c}",
             "params": lambda: (lambda r1, r2: {"b": r1 + r2, "c": r1 * r2})(
                 random.randint(1, 6), random.randint(1, 6)),
             "solution": lambda p: str(sp.factor(x**2 + p["b"]*x + p["c"])),
             "hint": "Find two numbers that multiply to give the constant and add to the coefficient of x."},
            {"statement": "Solve the quadratic: x² - {b}x + {c} = 0",
             "params": lambda: (lambda r1, r2: {"b": r1 + r2, "c": r1 * r2})(
                 random.randint(1, 8), random.randint(1, 8)),
             "solution": lambda p: str(sp.solve(x**2 - p["b"]*x + p["c"], x)),
             "hint": "Try factoring, or use the quadratic formula: x = (-b ± √(b²-4ac)) / 2a."},
        ],
        3: [
            {"statement": "Solve: |{a}x - {b}| = {c}",
             "params": lambda: {"a": random.randint(2, 6), "b": random.randint(1, 10),
                                "c": random.randint(5, 20)},
             "solution": lambda p: f"x = {(p['c'] + p['b'])/p['a']} or x = {(-p['c'] + p['b'])/p['a']}",
             "hint": "Split into two cases: the expression equals +c and -c."},
        ],
    },
    "trigonometry": {
        1: [
            {"statement": "Convert {deg}° to radians.",
             "params": lambda: {"deg": random.choice([30, 45, 60, 90, 120, 135, 150, 180, 270, 360])},
             "solution": lambda p: str(sp.Rational(p["deg"], 180) * sp.pi),
             "hint": "Multiply by π/180."},
        ],
        2: [
            {"statement": "Find all solutions in [0, 2π): sin(x) = {val}",
             "params": lambda: {"val": random.choice(["1/2", "√2/2", "√3/2", "-1/2"])},
             "solution": lambda p: f"Use the unit circle to find angles where sin = {p['val']}",
             "hint": "Think about the unit circle. In which quadrants is sine positive/negative?"},
        ],
    },
    "calculus": {
        1: [
            {"statement": "Find dy/dx if y = {a}x^{n} + {b}x^{m}",
             "params": lambda: {"a": random.randint(2, 8), "n": random.randint(2, 5),
                                "b": random.randint(1, 6), "m": random.randint(1, 3)},
             "solution": lambda p: str(sp.diff(p["a"]*x**p["n"] + p["b"]*x**p["m"], x)),
             "hint": "Power rule: d/dx[xⁿ] = nxⁿ⁻¹."},
        ],
        2: [
            {"statement": "Evaluate ∫({a}x^{n} + {b}) dx",
             "params": lambda: {"a": random.randint(1, 6), "n": random.randint(1, 4),
                                "b": random.randint(1, 10)},
             "solution": lambda p: str(sp.integrate(p["a"]*x**p["n"] + p["b"], x)) + " + C",
             "hint": "Reverse the power rule: ∫xⁿ dx = xⁿ⁺¹/(n+1) + C."},
            {"statement": "Find dy/dx using the chain rule: y = ({a}x + {b})^{n}",
             "params": lambda: {"a": random.randint(2, 5), "b": random.randint(1, 5),
                                "n": random.randint(2, 5)},
             "solution": lambda p: str(sp.diff((p["a"]*x + p["b"])**p["n"], x)),
             "hint": "Chain rule: d/dx[f(g(x))] = f'(g(x)) · g'(x)."},
        ],
        3: [
            {"statement": "Find the critical points of f(x) = x³ - {a}x² + {b}x",
             "params": lambda: {"a": random.randint(3, 9), "b": random.randint(1, 12)},
             "solution": lambda p: str(sp.solve(sp.diff(x**3 - p["a"]*x**2 + p["b"]*x, x), x)),
             "hint": "Set f'(x) = 0 and solve."},
        ],
    },
    "linear_algebra": {
        1: [
            {"statement": "Compute the dot product: [{a}, {b}] · [{c}, {d}]",
             "params": lambda: {"a": random.randint(-5, 5), "b": random.randint(-5, 5),
                                "c": random.randint(-5, 5), "d": random.randint(-5, 5)},
             "solution": lambda p: str(p["a"]*p["c"] + p["b"]*p["d"]),
             "hint": "Dot product = a₁b₁ + a₂b₂."},
        ],
        2: [
            {"statement": "Find the determinant of [[{a}, {b}], [{c}, {d}]]",
             "params": lambda: {"a": random.randint(1, 7), "b": random.randint(1, 7),
                                "c": random.randint(1, 7), "d": random.randint(1, 7)},
             "solution": lambda p: str(p["a"]*p["d"] - p["b"]*p["c"]),
             "hint": "det([[a,b],[c,d]]) = ad - bc."},
        ],
    },
    "differential_equations": {
        2: [
            {"statement": "Solve the ODE: dy/dx = {a}y",
             "params": lambda: {"a": random.randint(1, 5)},
             "solution": lambda p: f"y = Ce^({p['a']}x)",
             "hint": "This is a separable equation. Separate variables and integrate."},
        ],
        3: [
            {"statement": "Solve: y'' + {a}y' + {b}y = 0",
             "params": lambda: (lambda r1, r2: {"a": r1 + r2, "b": r1 * r2})(
                 random.randint(1, 4), random.randint(1, 4)),
             "solution": lambda p: f"Characteristic equation: r² + {p['a']}r + {p['b']} = 0",
             "hint": "Write the characteristic equation r² + ar + b = 0, find its roots."},
        ],
    },
    "physics_mechanics": {
        1: [
            {"statement": "A ball is dropped from {h}m. How long to hit the ground? (g=9.8 m/s²)",
             "params": lambda: {"h": random.choice([5, 10, 20, 45, 80])},
             "solution": lambda p: f"t = √(2h/g) = {round((2*p['h']/9.8)**0.5, 2)}s",
             "hint": "Use h = ½gt². Solve for t."},
        ],
        2: [
            {"statement": "A {m}kg object accelerates at {a}m/s². What force is applied?",
             "params": lambda: {"m": random.randint(2, 50), "a": random.randint(1, 10)},
             "solution": lambda p: f"F = ma = {p['m'] * p['a']}N",
             "hint": "Newton's second law: F = ma."},
        ],
    },
}


class ProblemGenerator:
    """Generates practice problems from the problem bank."""

    @staticmethod
    def generate(topic: str, difficulty: int = 1, count: int = 5) -> list[dict]:
        """
        Generate `count` problems for a given topic and difficulty.

        Returns list of dicts with keys: statement, solution, hint, difficulty, topic.
        """
        topic_bank = PROBLEM_BANK.get(topic, {})
        # Gather problems at requested difficulty and adjacent levels
        templates = topic_bank.get(difficulty, [])
        if not templates:
            # Fall back to any difficulty available for this topic
            for d in sorted(topic_bank.keys()):
                templates = topic_bank[d]
                if templates:
                    difficulty = d
                    break

        if not templates:
            return [{
                "statement": f"[No problems available for topic '{topic}' at difficulty {difficulty}]",
                "solution": "N/A",
                "hint": "Try asking the tutor to explain this topic first.",
                "difficulty": difficulty,
                "topic": topic,
            }]

        problems = []
        for _ in range(count):
            template = random.choice(templates)
            params = template["params"]()
            statement = template["statement"].format(**params)
            solution = template["solution"](params)

            problems.append({
                "statement": statement,
                "solution": solution,
                "hint": template.get("hint", "Think carefully!"),
                "difficulty": difficulty,
                "topic": topic,
            })

        return problems

    @staticmethod
    def get_available_topics() -> dict:
        """Return available topics and their difficulty levels."""
        return {
            topic: sorted(diffs.keys())
            for topic, diffs in PROBLEM_BANK.items()
        }


def generate_problems(topic: str, difficulty: int = 1, count: int = 5) -> list[dict]:
    """Module-level convenience function."""
    return ProblemGenerator.generate(topic, difficulty, count)
