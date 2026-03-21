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
3. ASSIGN study tasks from quality resources.
4. assessment understanding through targeted questions.
5. FLAG weak areas and FORCE review loops.
6. APPROVE or BLOCK hardware project suggestions based on physics readiness.

STRICTNESS RULES:
- If mastery < 60% in prerequisites, BLOCK advancement.
- Quality over speed. Deep understanding > surface coverage.
"""


class PhysicsSupervisorAgent(BaseAgent):
    """Physics Supervisor — strict learning overseer with prerequisite enforcement."""

    def __init__(self, **kwargs):
        super().__init__(
            name="PhysicsSupervisor",
            system_prompt=SYSTEM_PROMPT,
            **kwargs
        )

    def chat(self, user_msg: str, context: str = "", student_id: int = 1) -> str:
        """Enhanced chat with curriculum and mastery context."""
        mastery_context = self._build_physics_context(student_id)
        full_context = f"{context}\n\n{mastery_context}" if context else mastery_context
        return super().chat(user_msg, full_context, student_id=student_id)

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
                guidance = f"🤔 To understand **{target_topic}**, you first need a solid grasp of **{math_missing[0]}**."
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
