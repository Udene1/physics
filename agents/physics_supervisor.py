"""
agents/physics_supervisor.py — Physics Supervisor Agent.

Strict overseer for physics learning with prerequisite enforcement,
mastery tracking, and curriculum management.
Supports multi-student state.
"""

from .base import BaseAgent


# ── Physics Curriculum Tree ──────────────────────────────────────────

CURRICULUM = {
    "mechanics": {
        "order": 1,
        "subtopics": [
            "kinematics", "newtons_laws", "work_energy", "momentum",
            "rotational_motion", "gravitation", "oscillations",
        ],
        "math_prereqs": ["algebra", "trigonometry", "calculus"],
        "description": "Classical mechanics — motion, forces, energy, momentum",
        "resources": [
            "Khan Academy: Physics - Forces and Newton's Laws",
            "MIT OCW 8.01: Classical Mechanics",
            "Feynman Lectures Vol 1, Ch 1-15",
        ],
    },
    "electromagnetism": {
        "order": 2,
        "subtopics": [
            "electrostatics", "electric_circuits", "magnetism",
            "electromagnetic_induction", "maxwells_equations",
        ],
        "math_prereqs": ["calculus", "linear_algebra"],
        "physics_prereqs": ["mechanics"],
        "description": "Electric and magnetic fields, circuits, EM waves",
        "resources": [
            "Khan Academy: Electrical Engineering",
            "MIT OCW 8.02: Electricity and Magnetism",
            "Feynman Lectures Vol 2",
        ],
    },
    "thermodynamics": {
        "order": 3,
        "subtopics": [
            "temperature_heat", "first_law", "second_law",
            "entropy", "heat_engines", "kinetic_theory",
        ],
        "math_prereqs": ["calculus"],
        "physics_prereqs": ["mechanics"],
        "description": "Heat, energy transfer, entropy, thermodynamic laws",
        "resources": [
            "MIT OCW 8.333: Statistical Mechanics",
            "Feynman Lectures Vol 1, Ch 39-46",
        ],
    },
    "waves_optics": {
        "order": 4,
        "subtopics": [
            "wave_properties", "sound", "light", "interference",
            "diffraction", "geometric_optics",
        ],
        "math_prereqs": ["calculus", "trigonometry"],
        "physics_prereqs": ["mechanics"],
        "description": "Wave mechanics, sound, light, optics",
        "resources": [
            "MIT OCW 8.03: Vibrations and Waves",
            "Feynman Lectures Vol 1, Ch 47-52",
        ],
    },
    "quantum_basics": {
        "order": 5,
        "subtopics": [
            "wave_particle_duality", "schrodinger_equation",
            "uncertainty_principle", "quantum_states", "hydrogen_atom",
        ],
        "math_prereqs": ["calculus", "linear_algebra", "differential_equations"],
        "physics_prereqs": ["mechanics", "electromagnetism", "waves_optics"],
        "description": "Introduction to quantum mechanics",
        "resources": [
            "MIT OCW 8.04: Quantum Physics I",
            "Feynman Lectures Vol 3",
        ],
    },
}

# Mastery thresholds
MASTERY_THRESHOLD_ADVANCE = 60.0  # Minimum to move to next topic
MASTERY_THRESHOLD_HARDWARE = 50.0  # Minimum to attempt related hardware


SYSTEM_PROMPT = """You are the Physics Supervisor Agent — a STRICT but fair physics education
overseer. You enforce rigorous learning standards for a self-learner building toward
hardware engineering in Benin City, Nigeria.

YOUR RESPONSIBILITIES:
1. TRACK mastery levels per physics topic (0-100% scale).
2. ENFORCE prerequisites — NEVER allow a student to skip ahead without demonstrating mastery.
3. TEACH physics concepts from first principles when requested, using interactive "lesson notes".
4. ASSIGN study tasks from quality resources.
5. ASSESSMENT understanding through targeted questions.
6. FLAG weak areas and FORCE review loops.
7. APPROVE or BLOCK hardware project suggestions based on physics readiness.

STRICTNESS RULES:
- If mastery < 60% in prerequisites, BLOCK advancement.
- Quality over speed. Deep understanding > surface coverage.

TEACHING STYLE:
- When giving a lesson, provide a concise but deep explanation of the "why" using local Nigerian analogies.
- Always end a lesson with a "Check for Understanding" question.
"""
MASTERY_THRESHOLD_ADVANCE = 80.0


class PhysicsSupervisorAgent(BaseAgent):
    """Physics Supervisor — strict learning overseer with prerequisite enforcement."""

    def __init__(self, **kwargs):
        super().__init__(
            name="PhysicsSupervisor",
            system_prompt=SYSTEM_PROMPT,
            **kwargs
        )

    def get_student_state(self, student_id: int) -> dict:
        if self.db:
            state = self.db.get_agent_state(student_id, self.name)
            if not state:
                state = {"active_topic": None, "last_interaction": None}
            return state
        return {"active_topic": None, "last_interaction": None}

    def _save_student_state(self, student_id: int, state: dict):
        if self.db:
            self.db.set_agent_state(student_id, self.name, state)

    def chat(self, user_msg: str, context: str = "", student_id: int = 1, image=None) -> str:
        """Enhanced chat with curriculum, mastery context, and lesson support."""
        msg_lower = user_msg.lower().strip()

        # Handle lesson/teaching/prereq requests
        if msg_lower.startswith(("/lesson", "/teach", "/study")):
            topic = msg_lower.replace("/lesson", "").replace("/teach", "").replace("/study", "").strip() or "Mechanics"
            return self.teach_topic(student_id, topic)
            
        if msg_lower.startswith("/prereq"):
            topic = msg_lower.replace("/prereq", "").strip() or "Mechanics"
            return self.check_prerequisites(student_id, topic)["message"]

        # IMPROVEMENT: Check if responding to an assessment
        state = self.get_student_state(student_id)
        if state.get("active_topic") and not user_msg.startswith("/"):
            return self.evaluate_physics_response(student_id, user_msg)

        mastery_context = self._build_physics_context(student_id)
        full_context = f"{context}\n\n{mastery_context}" if context else mastery_context
        return super().chat(user_msg, full_context, student_id=student_id, image=image)

    def evaluate_physics_response(self, student_id: int, user_msg: str) -> str:
        """Evaluate a student's response to a 'Check for Understanding' question."""
        state = self.get_student_state(student_id)
        topic = state["active_topic"]
        
        prompt = (
            f"The student was learning about '{topic}' and just responded with: '{user_msg}'.\n"
            "Evaluate if their response shows a solid conceptual understanding. "
            "If yes, award 10% progress. If no, guide them back to the core concept. "
            "Output format: [CORRECT/INCORRECT] Followed by your feedback."
        )
        
        response = super().chat(prompt, context=f"Topic Assessment: {topic}", student_id=student_id)
        
        if self.db:
            is_correct = "[CORRECT]" in response.upper()
            # If correct, update mastery. We give a small bump for lesson participation.
            if is_correct:
                curr_mastery = self.db.get_mastery(student_id, topic)
                new_score = min(100.0, (curr_mastery["score"] + 10.0) if curr_mastery else 10.0)
                self.db.set_mastery_score(student_id, topic, "physics", new_score)
            
            self.db.log_interaction(
                student_id=student_id,
                agent="PhysicsSupervisor",
                topic=topic,
                user_input=user_msg,
                agent_response=response,
                result="correct" if is_correct else "incorrect"
            )
        
        # Clear active topic focus after assessment loop
        state["active_topic"] = None
        self._save_student_state(student_id, state)
        
        return response.replace("[CORRECT]", "✅").replace("[INCORRECT]", "🤔")

    def teach_topic(self, student_id: int, topic_name: str) -> str:
        """
        Provides interactive lesson notes on a topic, first checking for distilled local knowledge.
        """
        topic_name = topic_name.title().strip()
        
        # Set focus for assessment (apply to both distilled and generated)
        state = self.get_student_state(student_id)
        state["active_topic"] = topic_name
        self._save_student_state(student_id, state)

        # 1. Check distilled local knowledge first
        if self.db:
            distilled = self.db.get_distilled_lesson(topic_name)
            if distilled:
                return f"{distilled['content']}\n\n(✨ *Note: This lesson was served from my Local Knowledge Base.*)"

        # 2. Check prerequisites first
        prereqs = self.check_prerequisites(student_id, topic_name)
        if not prereqs["allowed"]:
            return prereqs["message"]

        # 3. Generate new lesson via LLM
        teaching_context = (
            f"The student wants an interactive lesson on '{topic_name}'.\n"
            "Provide 'Lesson Notes' that explain the first principles clearly. "
            "Use a Nigerian analogy (e.g., transportation in Lagos, construction in Benin). "
            "End with a specific 'Check for Understanding' question."
        )
        
        lesson = super().chat(user_msg=f"Give me a lesson on {topic_name}", context=f"Topic: {topic_name}\n{teaching_context}", student_id=student_id)
        
        if self.db:
            self.db.log_interaction(
                student_id=student_id,
                agent="PhysicsSupervisor",
                topic=topic_name,
                user_input=f"/lesson {topic_name}",
                agent_response=lesson,
                result="lesson"
            )
        return lesson

    def check_prerequisites(self, student_id: int, target_topic: str) -> dict:
        """Check if the student meets prerequisites for a topic using DB topics table."""
        if not self.db:
            return {"allowed": True, "missing": [], "message": "No database. Skipping checks."}

        topic_data = self.db.get_topic(target_topic)
        if not topic_data:
            # Fallback to hardcoded curriculum if not in topics table
            return self._check_legacy_prerequisites(student_id, target_topic)

        missing = []
        # Check prerequisites from DB
        for prereq_name in topic_data.get("prerequisites", []):
            mastery = self.db.get_mastery(student_id, prereq_name)
            if not mastery or mastery["score"] < MASTERY_THRESHOLD_ADVANCE:
                score = mastery["score"] if mastery else 0
                missing.append(f"{prereq_name} ({score}%)")

        if missing:
            # Check if any missing prereqs are 'math' to provide better guidance
            math_missing = []
            for m in missing:
                p_name = m.split(" (")[0]
                p_data = self.db.get_topic(p_name)
                if p_data and p_data["category"] == "math":
                    math_missing.append(p_name)

            if math_missing:
                guidance = (
                    f"🤔 To understand **{target_topic}**, you first need a solid grasp of **{math_missing[0]}**.\n\n"
                    f"Would you like a quick lesson? Try typing: `/lesson {math_missing[0]}`"
                )
            else:
                guidance = f"❌ **Prerequisites Not Met for {target_topic}**"

            return {
                "allowed": False,
                "missing": missing,
                "message": f"{guidance}\n\nImprove these first:\n" + "\n".join([f"• {m}" for m in missing])
            }
            
        return {"allowed": True, "missing": [], "message": f"✅ Ready for {target_topic}!"}

    def _check_legacy_prerequisites(self, student_id: int, target_topic: str) -> dict:
        """Fallback check using the hardcoded CURRICULUM dictionary."""
        topic_info = CURRICULUM.get(target_topic)
        if not topic_info:
            return {"allowed": True, "missing": [], "message": "Proceed."}
        
        missing = []
        for prereq in topic_info.get("math_prereqs", []) + topic_info.get("physics_prereqs", []):
            mastery = self.db.get_mastery(student_id, prereq)
            if not mastery or mastery["score"] < MASTERY_THRESHOLD_ADVANCE:
                score = mastery["score"] if mastery else 0
                missing.append(f"{prereq} ({score}%)")
        
        if missing:
            return {
                "allowed": False, 
                "missing": missing, 
                "message": f"❌ Missing prerequisites:\n" + "\n".join(missing)
            }
        return {"allowed": True, "missing": [], "message": "✅ Ready!"}

    def approve_hardware(self, student_id: int, project_topics: list[str]) -> dict:
        """Check if the student is ready for a hardware project."""
        missing = []
        for topic in project_topics:
            mastery = self.db.get_mastery(student_id, topic) if self.db else None
            if not mastery or mastery["score"] < MASTERY_THRESHOLD_HARDWARE:
                score = mastery["score"] if mastery else 0
                missing.append(f"{topic} ({score}%)")

        if missing:
            return {
                "approved": False,
                "missing": missing,
                "message": f"❌ **Hardware Blocked**\nNeed more mastery in:\n" + "\n".join(missing)
            }
        return {"approved": True, "missing": [], "message": "✅ **Hardware Approved!**"}

    def get_study_tasks(self, student_id: int, topic: str) -> str:
        """Generate study tasks for a specific topic."""
        topic_info = CURRICULUM.get(topic)
        if not topic_info:
            # Check DB
            if self.db:
                db_topic = self.db.get_topic(topic)
                if db_topic:
                    topic_info = {
                        "description": db_topic.get("description", ""),
                        "resources": ["Udene Professional Repository", "Local Distilled Knowledge"]
                    }
        
        if not topic_info:
            return f"Topic '{topic}' not found."

        mastery = self.db.get_mastery(student_id, topic) if self.db else None
        score = mastery["score"] if mastery else 0
        tasks = [f"📋 **Study Plan: {topic.title()}** (Mastery: {score}%)\n"]
        tasks.append("📖 **Resources:**")
        for r in topic_info.get("resources", []): tasks.append(f"  • {r}")
        
        return "\n".join(tasks)

    def get_curriculum_overview(self, student_id: int) -> str:
        """Return a formatted overview of the curriculum based on 5 standard buckets."""
        if not self.db: return "No database connection."
        
        buckets = ["Mechanics", "Electromagnetism", "Thermodynamics", "Waves & Optics", "Quantum Basics"]
        all_topics = self.db.get_all_topics()
        
        lines = ["📚 **Physics Curriculum Overview**\n"]
        
        for i, cat_name in enumerate(buckets, 1):
            items = [t for t in all_topics if t["category"] == cat_name]
            
            if not items:
                lines.append(f"**{i}. {cat_name}** [░░░░░░░░░░] 0% (Coming Soon)")
                continue

            total_mastery = 0
            for item in items:
                m = self.db.get_mastery(student_id, item["name"])
                total_mastery += m["score"] if m else 0
            
            avg_mastery = int(total_mastery / len(items)) if items else 0
            bar = "█" * (avg_mastery // 10) + "░" * (10 - (avg_mastery // 10))
            lines.append(f"**{i}. {cat_name}** [{bar}] {avg_mastery}%")
                
        return "\n".join(lines)

    def _build_physics_context(self, student_id: int) -> str:
        if not self.db: return "No mastery data."
        mastery = self.db.get_all_mastery(student_id)
        physics = [m for m in mastery if m["category"] in ("physics", "mechanics", "electromagnetism")]
        if not physics: return "Beginner — start with Mechanics."
        lines = ["Student's physics mastery:"]
        for m in physics:
            lines.append(f"  - {m['topic']}: {m['score']}%")
        return "\n".join(lines)

    def get_roadmap_status(self, student_id: int) -> dict:
        """
        Analyze the student's current position in the 5-topic curriculum.
        Returns a dict with current topic, progress, next milestones, and hardware hints.
        """
        if not self.db:
            return {"error": "No database connection"}

        all_topics = self.db.get_all_topics()
        mastery = {m["topic"]: m["score"] for m in self.db.get_all_mastery(student_id)}
        
        # 5 standard buckets
        buckets = ["Mechanics", "Electromagnetism", "Thermodynamics", "Waves & Optics", "Quantum Basics"]
        
        roadmap = []
        current_focus = None
        next_step = None
        hardware_milestone = None

        for bucket in buckets:
            bucket_topics = [t for t in all_topics if t["category"] == bucket]
            if not bucket_topics: continue
            
            completed_count = 0
            for t in bucket_topics:
                score = mastery.get(t["name"], 0)
                if score >= MASTERY_THRESHOLD_ADVANCE:
                    completed_count += 1
                elif not next_step:
                    # Found the first uncompleted topic
                    next_step = t
                    current_focus = bucket

            progress = (completed_count / len(bucket_topics)) * 100
            roadmap.append({"bucket": bucket, "progress": int(progress)})

        # Look for a hardware project "along the line"
        if next_step and next_step.get("build_hint"):
            hardware_milestone = next_step["build_hint"]
        
        return {
            "roadmap": roadmap,
            "current_focus": current_focus or "Completed",
            "next_step": next_step["name"] if next_step else "All core topics mastered!",
            "hardware_suggestion": hardware_milestone,
            "overall_progress": int(sum(r["progress"] for r in roadmap) / len(roadmap)) if roadmap else 0
        }
