"""
agents/math_tutor.py — Math Tutor Agent.

Specializes in solving equations, providing step-by-step hints,
and generating localized practice problems for Nigerian students.
Uses SymPy for verification.
"""

from .base import BaseAgent
from tools.math_verifier import MathVerifier
from tools.problem_generator import ProblemGenerator


class MathTutorAgent(BaseAgent):
    """AI Tutor specializing in Mathematics (Algebra, Calculus, etc.)."""

    def __init__(self, **kwargs):
        system_prompt = (
            "You are the Math Tutor (Udene Physics). You explain concepts clearly "
            "and encourage students to solve problems themselves. "
            "Use standard mathematical notation. If a student is stuck, provide a "
            "small hint rather than the full solution. Focus on foundational STEM "
            "math (Algebra, Geometry, Trigonometry, Calculus)."
        )
        super().__init__(name="MathTutor", system_prompt=system_prompt, **kwargs)
        self.verifier = MathVerifier()
        self.generator = ProblemGenerator()
        # Per-student state: {student_id: {"problems": [], "index": 0}}
        self.states = {}

    def _get_student_state(self, student_id: int) -> dict:
        if student_id not in self.states:
            self.states[student_id] = {"problems": [], "index": 0}
        return self.states[student_id]

    def chat(self, user_msg: str, context: str = "", student_id: int = 1) -> str:
        """Enhanced chat that detects verification requests and problem commands."""
        msg_lower = user_msg.lower().strip()

        # Handle problem generation requests
        if msg_lower.startswith("/problems") or msg_lower.startswith("/practice"):
            return self._handle_problem_request(student_id, msg_lower)

        # Handle answer verification
        if msg_lower.startswith("/verify") or msg_lower.startswith("/check"):
            return self._handle_verify(student_id, user_msg)

        # Handle "next problem" during a practice session
        if msg_lower in ("/next", "next", "next problem"):
            return self._next_problem(student_id)

        # Handle hint request
        if msg_lower in ("/hint", "hint", "give me a hint"):
            return self._give_hint(student_id)

        # Build mastery context for the tutor
        mastery_context = self._build_mastery_context(student_id)
        full_context = f"{context}\n\n{mastery_context}" if context else mastery_context

        return super().chat(user_msg, full_context, student_id=student_id)

    def _build_mastery_context(self, student_id: int) -> str:
        """Build a context string from the user's math mastery levels."""
        if not self.db:
            return ""
        mastery = self.db.get_all_mastery(student_id)
        math_topics = [m for m in mastery if m["category"] in ("math", "algebra", "calculus",
                                                                 "linear_algebra", "trigonometry",
                                                                 "differential_equations")]
        if not math_topics:
            return "Student mastery: No math topics tracked yet (likely a beginner)."
        
        summary = "Student's current math mastery:\n"
        for m in math_topics:
            summary += f"  • {m['topic']}: {m['score']}% ({m['problems_attempted']} attempts)\n"
        return summary

    def _handle_problem_request(self, student_id: int, msg: str) -> str:
        """Generate a new set of problems based on the requested topic."""
        topic_name = msg.replace("/problems", "").replace("/practice", "").strip() or "Basic Algebra"
        
        difficulty = 1
        if self.db:
            # Try to match the user's input to a real topic name
            all_topics = self.db.get_all_topics(category="math")
            for t in all_topics:
                if topic_name.lower() in t["name"].lower():
                    topic_name = t["name"]
                    difficulty = t["difficulty"]
                    break

        problems = self.generator.generate(topic_name, difficulty=difficulty, count=3)
        state = self._get_student_state(student_id)
        state["problems"] = problems
        state["index"] = 0
        
        if not problems or not problems[0]["statement"]:
            return f"Sorry, I couldn't generate problems for '{topic_name}'. Try 'algebra' or 'calculus'."
            
        first = problems[0]
        return (
            f"📝 Let's practice **{topic}**!\n\n"
            f"**Problem 1:** {first['statement']}\n\n"
            "Try solving it and type `/verify <your_answer>` to check!"
        )

    def _handle_verify(self, student_id: int, user_msg: str) -> str:
        """Verify the user's answer against the current problem."""
        state = self._get_student_state(student_id)
        if not state["problems"]:
            return "I don't have a problem active for you. Type `/problems` to start!"
            
        current = state["problems"][state["index"]]
        # Extract the user's answer part (strip /verify or /check)
        user_ans = user_msg.replace("/verify", "").replace("/check", "").strip()
        
        if not user_ans:
            return "Please provide an answer after /verify (e.g., `/verify 42`)"

        # 'solution' is the key in ProblemGenerator output, not 'answer'
        is_correct, explanation = self.verifier.verify_symbolic(current["solution"], user_ans)
        
        if self.db:
            # Record result in DB
            self.db.update_mastery(student_id, current["topic"], "math", is_correct)
            self.db.log_interaction(
                student_id=student_id,
                agent="MathTutor",
                topic=current["topic"],
                user_input=user_msg,
                agent_response=explanation,
                result="correct" if is_correct else "incorrect"
            )
            
        if is_correct:
            return (
                f"{explanation}\n\n"
                "Great job! Type `/next` for the next problem."
            )
        else:
            return (
                f"{explanation}\n\n"
                "🤔 Not quite! Think about it — or type `/hint` for more help."
            )

    def _next_problem(self, student_id: int) -> str:
        """Move to the next problem in the current set."""
        state = self._get_student_state(student_id)
        if not state["problems"]:
            return "No active problem set. Type `/problems` to get some!"
            
        state["index"] += 1
        if state["index"] >= len(state["problems"]):
            return (
                "🏁 You've finished this practice set! "
                "Type `/problems <topic>` to get more challenges."
            )
            
        current = state["problems"][state["index"]]
        return (
            f"**Problem {state['index'] + 1}:**\n\n"
            f"{current['question']}\n\n"
            "Take your time!"
        )

    def _give_hint(self, student_id: int) -> str:
        """Provide a hint for the current problem based on the LLM's logic."""
        state = self._get_student_state(student_id)
        if not state["problems"]:
            return "I can only give hints if we are solving a specific problem. Type `/problems` to start."
            
        current = state["problems"][state["index"]]
        
        # We can use the LLM to generate a hint based on the question and answer
        prompt = (
            f"The student is working on this math problem: '{current['question']}'.\n"
            f"The correct answer is '{current['answer']}'.\n"
            f"They need a small, helpful hint that doesn't reveal the whole answer."
        )
        return self.chat(prompt, context="Provide only the hint text.", student_id=student_id)

    def get_summary(self, student_id: int) -> str:
        """Return a string summary of math progress."""
        if not self.db:
            return "Math tracking is disabled (no database)."
        mastery = self.db.get_all_mastery(student_id)
        math = [m for m in mastery if m["category"] in ("math", "algebra", "calculus")]
        if not math:
            return "No math progress recorded yet."
        
        lines = ["📏 **Math Mastery Overview:**"]
        for m in math:
            lines.append(f"  • {m['topic']}: {m['score']}%")
        return "\n".join(lines)
