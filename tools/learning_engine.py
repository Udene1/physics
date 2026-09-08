"""Persistent adaptive learning engine.

The LLM is not the source of truth for progression. This module keeps a durable
learner model in the existing per-student agent-state store and uses real
assessment results to choose a starting point.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


STATE_AGENT = "LearningEngine"
STATE_VERSION = 1


@dataclass(frozen=True)
class DiagnosticQuestion:
    id: str
    skill: str
    prompt: str
    choices: tuple[str, ...]
    correct_index: int
    level: int


# The first diagnostic is intentionally cross-stage: a learner preparing for
# junior science, an existing physics student, and a WAEC candidate all enter
# through the same evidence-based discovery process.
DIAGNOSTIC: tuple[DiagnosticQuestion, ...] = (
    DiagnosticQuestion("arith_01", "arithmetic", "What is 7 + 5?", ("10", "12", "13", "15"), 1, 1),
    DiagnosticQuestion("frac_01", "fractions", "Which is larger?", ("1/4", "1/2", "They are equal", "Cannot tell"), 1, 1),
    DiagnosticQuestion("ratio_01", "ratios", "3 notebooks cost ₦600. What does one cost?", ("₦100", "₦150", "₦200", "₦300"), 2, 1),
    DiagnosticQuestion("alg_01", "algebra", "If x + 7 = 12, what is x?", ("3", "5", "7", "19"), 1, 2),
    DiagnosticQuestion("graph_01", "graphs", "A straight line rises as time increases. What does its slope describe?", ("A rate of change", "Only its colour", "Its starting unit", "Nothing physical"), 0, 2),
    DiagnosticQuestion("geo_01", "geometry", "A right triangle has sides 3 and 4. What is the hypotenuse?", ("5", "6", "7", "12"), 0, 2),
    DiagnosticQuestion("trig_01", "trigonometry", "In a right triangle, sin(θ) is best described as:", ("opposite/hypotenuse", "adjacent/hypotenuse", "opposite/adjacent", "hypotenuse/opposite"), 0, 3),
    DiagnosticQuestion("physics_01", "motion", "A car changes from 10 m/s to 20 m/s. Which quantity definitely changed?", ("Its velocity", "Its mass", "The laws of motion", "Its unit system"), 0, 2),
    DiagnosticQuestion("physics_02", "forces", "If the same force acts on a heavier object, its acceleration is generally:", ("Larger", "Smaller", "Always zero", "Unchanged"), 1, 3),
    DiagnosticQuestion("physics_03", "energy", "A raised object has stored energy mainly because of its:", ("Position", "Colour", "Temperature only", "Shape of its shadow"), 0, 3),
)

SKILL_ORDER = (
    "arithmetic", "fractions", "ratios", "algebra", "geometry", "graphs",
    "trigonometry", "motion", "forces", "energy",
)

MATH_SKILLS = {"arithmetic", "fractions", "ratios", "algebra", "geometry", "graphs", "trigonometry"}
PHYSICS_SKILLS = {"motion", "forces", "energy"}


def _default_state() -> dict:
    return {
        "version": STATE_VERSION,
        "status": "not_started",
        "diagnostic_index": 0,
        "diagnostic_answers": {},
        "skills": {},
        "current_skill": None,
        "current_stage": None,
        "next_action": "diagnostic",
        "updated_at": None,
    }


class LearningEngine:
    """Owns learner progression state; agents consume its decisions."""

    def __init__(self, db):
        self.db = db

    def _state(self, student_id: int) -> dict:
        state = self.db.get_agent_state(student_id, STATE_AGENT)
        if not state:
            state = _default_state()
        state.setdefault("version", STATE_VERSION)
        state.setdefault("diagnostic_answers", {})
        state.setdefault("skills", {})
        return state

    def _save(self, student_id: int, state: dict) -> dict:
        from datetime import datetime
        state["updated_at"] = datetime.now().isoformat()
        self.db.set_agent_state(student_id, STATE_AGENT, state)
        return state

    def start(self, student_id: int) -> dict:
        state = self._state(student_id)
        if state["status"] == "complete":
            return self.snapshot(student_id)
        state["status"] = "diagnostic"
        state["next_action"] = "diagnostic"
        return self._save(student_id, state)

    def current_question(self, student_id: int) -> Optional[dict]:
        state = self._state(student_id)
        if state["status"] == "not_started":
            self.start(student_id)
            state = self._state(student_id)
        if state["status"] != "diagnostic":
            return None
        index = state["diagnostic_index"]
        if index >= len(DIAGNOSTIC):
            self.finish_diagnostic(student_id)
            return None
        q = DIAGNOSTIC[index]
        return {
            "id": q.id,
            "skill": q.skill,
            "prompt": q.prompt,
            "choices": list(q.choices),
            "number": index + 1,
            "total": len(DIAGNOSTIC),
        }

    def answer(self, student_id: int, question_id: str, choice_index: int) -> dict:
        state = self._state(student_id)
        if state["status"] != "diagnostic":
            raise ValueError("Diagnostic is not active for this learner")
        index = state["diagnostic_index"]
        if index >= len(DIAGNOSTIC):
            raise ValueError("Diagnostic is already complete")
        question = DIAGNOSTIC[index]
        if question.id != question_id:
            raise ValueError("Question is stale; resume from the current diagnostic question")
        if not 0 <= choice_index < len(question.choices):
            raise ValueError("Invalid answer choice")

        correct = choice_index == question.correct_index
        skill = state["skills"].setdefault(question.skill, {"score": 0.0, "attempts": 0, "correct": 0})
        skill["attempts"] += 1
        if correct:
            skill["correct"] += 1
        skill["score"] = round(100.0 * skill["correct"] / skill["attempts"], 1)
        state["diagnostic_answers"][question.id] = {
            "skill": question.skill,
            "choice_index": choice_index,
            "correct": correct,
        }
        state["diagnostic_index"] += 1

        if state["diagnostic_index"] >= len(DIAGNOSTIC):
            self._save(student_id, state)
            return self.finish_diagnostic(student_id)
        self._save(student_id, state)
        return {"correct": correct, "complete": False, "next": self.current_question(student_id)}

    def finish_diagnostic(self, student_id: int) -> dict:
        state = self._state(student_id)
        skills = state["skills"]
        for skill in SKILL_ORDER:
            skills.setdefault(skill, {"score": 0.0, "attempts": 0, "correct": 0})

        # Find the earliest weak prerequisite. This is deliberately conservative:
        # a learner can enter at any age/stage, but we do not push them into a
        # physics track whose mathematical foundation is unsupported.
        weak_math = next((s for s in SKILL_ORDER if s in MATH_SKILLS and skills[s]["score"] < 60), None)
        if weak_math:
            current_skill = weak_math
            stage = "math_foundation"
        else:
            weak_physics = next((s for s in SKILL_ORDER if s in PHYSICS_SKILLS and skills[s]["score"] < 60), None)
            current_skill = weak_physics or "motion"
            stage = "physics_foundation" if weak_physics else "physics_extension"

        state["status"] = "complete"
        state["current_skill"] = current_skill
        state["current_stage"] = stage
        state["next_action"] = "learn"
        self._save(student_id, state)

        # Also expose the diagnostic evidence through the existing mastery table
        # so reports and existing agents can consume it without inventing a second
        # source of truth.
        for skill, data in skills.items():
            if data["attempts"]:
                category = "math" if skill in MATH_SKILLS else "physics"
                self.db.set_mastery_score(student_id, skill, category, data["score"])

        return self.snapshot(student_id)

    def snapshot(self, student_id: int) -> dict:
        state = self._state(student_id)
        return {
            "status": state["status"],
            "current_skill": state["current_skill"],
            "current_stage": state["current_stage"],
            "next_action": state["next_action"],
            "diagnostic_progress": {
                "answered": state["diagnostic_index"],
                "total": len(DIAGNOSTIC),
            },
            "skills": state["skills"],
        }
