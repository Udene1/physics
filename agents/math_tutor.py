"""
agents/math_tutor.py — Math Tutor Agent.

Explains concepts from algebra through differential equations with Socratic questioning.
Ties explanations to physical intuition and hardware applications.
Uses SymPy for answer verification.
"""

from .base import BaseAgent
from tools.math_verifier import MathVerifier
from tools.problem_generator import ProblemGenerator


SYSTEM_PROMPT = """You are the Math Tutor Agent — a patient, rigorous mathematics teacher helping a
self-learner in Benin City, Nigeria build deep mathematical understanding for physics and
hardware engineering applications.

TEACHING PHILOSOPHY:
1. NEVER solve problems completely for the user. Guide them with Socratic questions.
2. Use chain-of-thought reasoning VISIBLY — show your thinking step by step.
3. ALWAYS connect math to physical intuition:
   - Derivatives → rates of change in circuits, velocity, acceleration
   - Integrals → area under curves, total charge, total energy
   - Linear algebra → transformations, circuit analysis, signal processing
   - Differential equations → oscillations, heat flow, circuit dynamics
4. Start with concrete examples before abstract theory.
5. When the user is stuck, give ONE hint at a time, then ask a guiding question.
6. Celebrate correct answers and correct reasoning.
7. If the user makes an error, identify the specific misconception — don't just say "wrong."

COVERAGE (in order of prerequisites):
- Algebra & Trigonometry (refresh/foundation)
- Calculus (single & multivariable)
- Linear Algebra
- Differential Equations
- Probability & Statistics (basics for sensor data)

HARDWARE CONNECTIONS (use when teaching):
- "When you differentiate voltage across a capacitor, you get current flow — calculus in action!"
- "Matrix multiplication is how we solve systems of linear equations in circuit analysis."
- "This ODE describes how a spring-mass system oscillates — same math as an LC circuit!"

FORMAT:
- Use clear mathematical notation (x², √, ∫, Σ, etc.)
- Break complex steps into numbered sub-steps
- End explanations with a question to check understanding
- Suggest practice problems from the problem generator
"""


class MathTutorAgent(BaseAgent):
    """Math Tutor — Socratic teaching, problem generation, answer verification."""

    def __init__(self, db=None, model: str = None):
        super().__init__(
            name="MathTutor",
            system_prompt=SYSTEM_PROMPT,
            db=db,
            model=model,
        )
        self.verifier = MathVerifier()
        self.generator = ProblemGenerator()
        self.current_problems: list[dict] = []
        self.current_problem_index: int = 0

    def chat(self, user_msg: str, context: str = "") -> str:
        """Enhanced chat that detects verification requests and problem commands."""
        msg_lower = user_msg.lower().strip()

        # Handle problem generation requests
        if msg_lower.startswith("/problems") or msg_lower.startswith("/practice"):
            return self._handle_problem_request(msg_lower)

        # Handle answer verification
        if msg_lower.startswith("/verify") or msg_lower.startswith("/check"):
            return self._handle_verify(user_msg)

        # Handle "next problem" during a practice session
        if msg_lower in ("/next", "next", "next problem"):
            return self._next_problem()

        # Handle hint request
        if msg_lower in ("/hint", "hint", "give me a hint"):
            return self._give_hint()

        # Build mastery context for the tutor
        mastery_context = self._build_mastery_context()
        full_context = f"{context}\n\n{mastery_context}" if context else mastery_context

        return super().chat(user_msg, full_context)

    def _build_mastery_context(self) -> str:
        """Build a context string from the user's math mastery levels."""
        if not self.db:
            return ""
        mastery = self.db.get_all_mastery()
        math_topics = [m for m in mastery if m["category"] in ("math", "algebra", "calculus",
                                                                 "linear_algebra", "trigonometry",
                                                                 "differential_equations")]
        if not math_topics:
            return "Student mastery: No math topics tracked yet (likely a beginner)."

        lines = ["Student's current math mastery:"]
        for m in math_topics:
            lines.append(f"  - {m['topic']}: {m['score']}% ({m['problems_attempted']} problems attempted)")
        return "\n".join(lines)

    def _handle_problem_request(self, msg: str) -> str:
        """Generate practice problems for a topic."""
        parts = msg.split()
        topic = parts[1] if len(parts) > 1 else "algebra"
        difficulty = int(parts[2]) if len(parts) > 2 else 1
        count = int(parts[3]) if len(parts) > 3 else 5

        available = self.generator.get_available_topics()
        if topic not in available:
            topics_list = ", ".join(available.keys())
            return (
                f"📚 Available topics: {topics_list}\n\n"
                f"Usage: /problems <topic> [difficulty] [count]\n"
                f"Example: /problems calculus 2 5"
            )

        self.current_problems = self.generator.generate(topic, difficulty, count)
        self.current_problem_index = 0
        return self._format_problem(0)

    def _format_problem(self, index: int) -> str:
        """Format a problem for display."""
        if index >= len(self.current_problems):
            return self._session_complete()

        p = self.current_problems[index]
        total = len(self.current_problems)
        return (
            f"📝 **Problem {index + 1}/{total}** [{p['topic']} — Difficulty {p['difficulty']}]\n\n"
            f"{p['statement']}\n\n"
            f"💡 Type your answer, or:\n"
            f"  • `/hint` for a hint\n"
            f"  • `/next` to skip\n"
            f"  • `/verify <your_answer>` to check"
        )

    def _next_problem(self) -> str:
        """Move to the next problem in the session."""
        if not self.current_problems:
            return "No active practice session. Use `/problems <topic>` to start one!"

        self.current_problem_index += 1
        return self._format_problem(self.current_problem_index)

    def _give_hint(self) -> str:
        """Give a hint for the current problem."""
        if not self.current_problems or self.current_problem_index >= len(self.current_problems):
            return "No active problem. Use `/problems <topic>` to start practicing!"

        p = self.current_problems[self.current_problem_index]
        return f"💡 **Hint:** {p['hint']}"

    def _handle_verify(self, msg: str) -> str:
        """Verify a user's answer against the current problem or a custom expression."""
        parts = msg.split(maxsplit=1)
        if len(parts) < 2:
            return "Usage: `/verify <your_answer>`\nExample: `/verify x**2 + 2*x + 1`"

        user_answer = parts[1].strip()

        # If we have an active problem, compare against its solution
        if self.current_problems and self.current_problem_index < len(self.current_problems):
            p = self.current_problems[self.current_problem_index]
            expected = p["solution"]

            # Try symbolic verification
            is_correct, explanation = self.verifier.verify_symbolic(expected, user_answer)

            if is_correct:
                # Update mastery
                if self.db:
                    self.db.update_mastery(p["topic"], p["topic"], True)

                result = (
                    f"{explanation}\n\n"
                    f"🎉 Excellent work! Moving to the next problem...\n"
                )
                self.current_problem_index += 1
                if self.current_problem_index < len(self.current_problems):
                    result += "\n" + self._format_problem(self.current_problem_index)
                else:
                    result += "\n" + self._session_complete()
                return result
            else:
                if self.db:
                    self.db.update_mastery(p["topic"], p["topic"], False)
                return (
                    f"{explanation}\n\n"
                    f"🤔 Not quite! Think about it — {p['hint']}\n"
                    f"Try again with `/verify <new_answer>`, or `/hint` for more help."
                )

        return "No active problem to verify against. Start a session with `/problems <topic>`"

    def _session_complete(self) -> str:
        """Summary when all problems in a session are done."""
        total = len(self.current_problems)
        self.current_problems = []
        self.current_problem_index = 0
        return (
            f"🏆 **Practice Session Complete!** ({total} problems)\n\n"
            f"Great effort! You can:\n"
            f"  • Start another session: `/problems <topic> [difficulty]`\n"
            f"  • Ask me to explain any concept\n"
            f"  • Check your progress: `/report`"
        )
