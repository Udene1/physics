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
            "You are the Math Tutor (Udene Learning Suite) — a patient, brilliant mathematics "
            "teacher who makes even the most abstract concepts feel intuitive.\n\n"

            "═══ YOUR TEACHING PHILOSOPHY ═══\n"
            "Math is not about memorizing formulas. It is about understanding PATTERNS and STRUCTURE. "
            "Your job is to help the student SEE the pattern, not just compute the answer.\n\n"

            "═══ LESSON STRUCTURE ═══\n"
            "When teaching a concept, follow this flow:\n"
            "1. **WHY IT MATTERS** — Connect the topic to something real (building circuits, "
            "calculating profit at a market, measuring land).\n"
            "2. **THE CORE IDEA** — Explain the concept in plain language FIRST, then introduce notation.\n"
            "3. **WORKED EXAMPLE** — Solve one problem step-by-step, narrating your thinking aloud.\n"
            "4. **COMMON TRAPS** — Warn about the most frequent mistakes students make.\n"
            "5. **YOUR TURN** — Give a practice problem and ask the student to try.\n\n"

            "═══ WHEN STUDENTS GET IT WRONG ═══\n"
            "NEVER just say 'incorrect.' Diagnose the error:\n"
            "- **Sign Error**: 'You lost a negative sign in step 2. Watch: -(3-5) = -3+5 = 2, not -2.'\n"
            "- **Wrong Operation**: 'You multiplied when you should have divided. Remember: "
            "to isolate x, do the OPPOSITE operation.'\n"
            "- **Conceptual Gap**: 'You applied the product rule, but this needs the chain rule "
            "because f(g(x)) is a composition.'\n"
            "- **Arithmetic Slip**: 'Your method is perfect! Just recheck: 7x8 = 56, not 54.'\n\n"

            "═══ ADAPTIVE DEPTH ═══\n"
            "- **Beginner**: Use Nigerian market analogies. 'If 1 tuber of yam costs N500, "
            "how much for x tubers? That's a linear equation!'\n"
            "- **Intermediate**: Introduce formal notation with physical meaning attached.\n"
            "- **Advanced**: Challenge with proofs, edge cases, and connections to physics.\n\n"

            "═══ HINTS ═══\n"
            "When giving hints, use SCAFFOLDING — give the smallest possible nudge:\n"
            "Level 1: 'What operation undoes multiplication?'\n"
            "Level 2: 'Try dividing both sides by 3.'\n"
            "Level 3: 'If 3x = 12, then x = 12/3 = ?'"
        )
        super().__init__(name="MathTutor", system_prompt=system_prompt, **kwargs)
        self.verifier = MathVerifier()
        self.generator = ProblemGenerator()

    def get_student_state(self, student_id: int) -> dict:
        if self.db:
            state = self.db.get_agent_state(student_id, self.name)
            if not state:
                state = {"problems": [], "index": 0}
            return state
        return {"problems": [], "index": 0}

    def _save_student_state(self, student_id: int, state: dict):
        if self.db:
            self.db.set_agent_state(student_id, self.name, state)

    def chat(self, user_msg: str, context: str = "", student_id: int = 1, image=None) -> str:
        """Enhanced chat that detects verification requests and problem commands."""
        msg_lower = user_msg.lower().strip()

        # Handle problem generation requests
        if msg_lower.startswith("/problems") or msg_lower.startswith("/practice"):
            return self._handle_problem_request(student_id, msg_lower)

        # Handle answer verification
        if msg_lower.startswith("/verify") or msg_lower.startswith("/check"):
            return self._handle_verify(student_id, user_msg)
            
        if msg_lower.startswith("/analyze") and image:
            return self.analyze_math_photo(image, student_id)

        # Handle "next problem" during a practice session
        if msg_lower in ("/next", "next", "next problem"):
            return self._next_problem(student_id)

        # Handle lesson/teaching requests
        if msg_lower.startswith("/lesson") or msg_lower.startswith("/teach"):
            topic = msg_lower.replace("/lesson", "").replace("/teach", "").strip() or "Basic Algebra"
            return self.teach_topic(student_id, topic)

        # Handle hint request
        if msg_lower in ("/hint", "hint", "give me a hint"):
            return self._give_hint(student_id)

        # Check for numeric or symbolic "naked" answers if a problem is active
        state = self.get_student_state(student_id)
        if state["problems"] and not user_msg.startswith("/"):
            # If the user just sends something like "42" or "x+1", try to verify it
            # We assume it's an answer if it doesn't clearly match a command
            return self._handle_verify(student_id, user_msg)

        # Build mastery context for the tutor
        mastery_context = self._build_mastery_context(student_id)
        full_context = f"{context}\n\n{mastery_context}" if context else mastery_context

        return super().chat(user_msg, full_context, student_id=student_id, image=image)

    def analyze_math_photo(self, image_data, student_id: int = 1) -> str:
        """Analyze a photo of handwritten math for errors or steps."""
        prompt = (
            "Analyze this photo of handwritten mathematical work. Extract the problem "
            "being solved and check the steps for accuracy. If there is a mistake, "
            "explain why it happened using a first-principles approach. Do not just give "
            "the answer; guide the student to correct their own thinking."
        )
        return super().chat(prompt, context="Math vision analysis mode.", student_id=student_id, image=image_data)

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
        state = self.get_student_state(student_id)
        state["problems"] = problems
        state["index"] = 0
        self._save_student_state(student_id, state)
        
        if not problems or not problems[0]["statement"]:
            return f"Sorry, I couldn't generate problems for '{topic_name}'. Try 'algebra' or 'calculus'."
            
        first = problems[0]
        # Include a very brief conceptual anchor even when just starting problems
        intro = f"📝 Let's practice **{topic_name}**!\n\n"
        if difficulty == 1:
            intro += "Remember: Always look for the first principle or the core definition first.\n\n"
            
        return (
            f"{intro}"
            f"**Problem 1:** {first['statement']}\n\n"
            "Try solving it and type `/verify <your_answer>` to check!"
        )

    def teach_topic(self, student_id: int, topic_name: str) -> str:
        """
        Provides interactive lesson notes on a topic, first checking for distilled local knowledge.
        """
        topic_name = topic_name.title().strip()
        
        # 1. Check distilled local knowledge first
        if self.db:
            distilled = self.db.get_distilled_lesson(topic_name)
            if distilled:
                return f"{distilled['content']}\n\n(✨ *Note: This lesson was served from my Local Knowledge Base.*)"

        # 2. Generate new lesson via LLM
        prompt = (
            f"The student wants to learn about '{topic_name}'.\n"
            "Provide a clear, engaging, and concise lesson that explains the core concepts "
            "from first principles. Use relatable analogies where possible (e.g., Nigerian context "
            "like market trade or construction). Do NOT give practice problems yet. "
            "End by asking if they feel ready for a practice problem."
        )
        lesson = super().chat(prompt, context=f"Topic: {topic_name}\nProvide only the lesson content.", student_id=student_id)
        
        if self.db:
            self.db.log_interaction(
                student_id=student_id,
                agent="MathTutor",
                topic=topic_name,
                user_input=f"/lesson {topic_name}",
                agent_response=lesson,
                result="lesson"
            )
        return lesson

    def _handle_verify(self, student_id: int, user_msg: str) -> str:
        """Verify the user's answer against the current problem."""
        state = self.get_student_state(student_id)
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
            # LLM-powered Error Diagnosis
            diagnosis_prompt = (
                f"The student tried to solve: '{current['question']}'\n"
                f"Correct answer: {current['solution']}\n"
                f"Student's answer: {user_ans}\n\n"
                "Diagnose their specific error. Is it a:\n"
                "- Sign error (lost a negative)\n"
                "- Wrong operation (multiplied instead of divided)\n"
                "- Conceptual gap (used wrong formula/rule)\n"
                "- Arithmetic slip (right method, wrong computation)\n"
                "Give a SHORT, targeted explanation that helps them fix THIS specific mistake. "
                "Do NOT reveal the full answer. Guide them to correct it themselves."
            )
            diagnosis = super().chat(diagnosis_prompt, context=f"Error diagnosis for: {current['topic']}", student_id=student_id)
            
            return (
                f"{explanation}\n\n"
                f"**Error Analysis:**\n{diagnosis}\n\n"
                "Try again, or type `/hint` for more help."
            )

    def _next_problem(self, student_id: int) -> str:
        """Move to the next problem in the current set."""
        state = self.get_student_state(student_id)
        if not state["problems"]:
            return "No active problem set. Type `/problems` to get some!"
            
        state["index"] += 1
        self._save_student_state(student_id, state)
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
        state = self.get_student_state(student_id)
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
