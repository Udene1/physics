"""
agents/physics_supervisor.py — Physics Supervisor Agent.

Strict overseer for physics learning with prerequisite enforcement,
mastery tracking, and curriculum management.
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
   • No electromagnetism without solid mechanics + calculus
   • No quantum without linear algebra + differential equations + EM
3. ASSIGN study tasks from quality resources (Khan Academy, MIT OCW, Feynman Lectures).
4. ASSESS understanding through targeted questions — not just memorization.
5. FLAG weak areas and FORCE review loops until mastery improves.
6. APPROVE or BLOCK hardware project suggestions based on physics readiness.

STRICTNESS RULES:
- If mastery < 60% in prerequisites, BLOCK advancement. Be direct: "You're not ready yet."
- If user wants to skip, explain WHY prerequisites matter with a concrete example.
- Track mistakes — if user repeats the same error, assign targeted review.
- Quality over speed. Deep understanding > surface coverage.

TEACHING APPROACH:
- Use chain-of-thought to show physics reasoning.
- Connect theory to experiments and real-world applications.
- Ask probing questions: "What would happen if we doubled the mass?"
- Use order-of-magnitude reasoning and dimensional analysis.
- Recommend specific lectures/chapters, not just "go study."

APPROVAL FORMAT (for hardware requests):
✅ APPROVED: "[Project name]" — You have demonstrated sufficient mastery in [topics].
❌ BLOCKED: "[Project name]" — You need to improve [topics] first. Here's what to study: [specific tasks].
"""


class PhysicsSupervisorAgent(BaseAgent):
    """Physics Supervisor — strict learning overseer with prerequisite enforcement."""

    def __init__(self, **kwargs):
        super().__init__(
            name="PhysicsSupervisor",
            system_prompt=SYSTEM_PROMPT,
            **kwargs
        )

    def chat(self, user_msg: str, context: str = "") -> str:
        """Enhanced chat with curriculum and mastery context."""
        mastery_context = self._build_physics_context()
        full_context = f"{context}\n\n{mastery_context}" if context else mastery_context
        return super().chat(user_msg, full_context)

    def check_prerequisites(self, target_topic: str) -> dict:
        """
        Check if the user meets prerequisites for a physics topic.

        Returns {"allowed": bool, "missing": [...], "message": str}
        """
        topic_info = CURRICULUM.get(target_topic)
        if not topic_info:
            return {"allowed": True, "missing": [], "message": f"Topic '{target_topic}' not in curriculum — proceeding."}

        missing = []

        # Check math prerequisites
        math_prereqs = topic_info.get("math_prereqs", [])
        for prereq in math_prereqs:
            mastery = self.db.get_mastery(prereq) if self.db else None
            if not mastery or mastery["score"] < MASTERY_THRESHOLD_ADVANCE:
                score = mastery["score"] if mastery else 0
                missing.append(f"Math: {prereq} (current: {score}%, need: {MASTERY_THRESHOLD_ADVANCE}%)")

        # Check physics prerequisites
        physics_prereqs = topic_info.get("physics_prereqs", [])
        for prereq in physics_prereqs:
            mastery = self.db.get_mastery(prereq) if self.db else None
            if not mastery or mastery["score"] < MASTERY_THRESHOLD_ADVANCE:
                score = mastery["score"] if mastery else 0
                missing.append(f"Physics: {prereq} (current: {score}%, need: {MASTERY_THRESHOLD_ADVANCE}%)")

        if missing:
            missing_str = "\n  ".join(missing)
            return {
                "allowed": False,
                "missing": missing,
                "message": (
                    f"❌ **Prerequisites Not Met for {target_topic.replace('_', ' ').title()}**\n\n"
                    f"You need to improve:\n  {missing_str}\n\n"
                    f"📚 Focus on these areas first. Use `/problems <topic>` to practice!"
                ),
            }

        return {
            "allowed": True,
            "missing": [],
            "message": f"✅ Prerequisites met for {target_topic.replace('_', ' ').title()}. Let's dive in!"
        }

    def approve_hardware(self, project_topics: list[str]) -> dict:
        """Check if the user is ready for a hardware project requiring certain topics."""
        missing = []

        for topic in project_topics:
            mastery = self.db.get_mastery(topic) if self.db else None
            if not mastery or mastery["score"] < MASTERY_THRESHOLD_HARDWARE:
                score = mastery["score"] if mastery else 0
                missing.append(f"{topic} (current: {score}%, need: {MASTERY_THRESHOLD_HARDWARE}%)")

        if missing:
            return {
                "approved": False,
                "missing": missing,
                "message": (
                    f"❌ **Hardware Project Blocked**\n\n"
                    f"Insufficient mastery in:\n  • " + "\n  • ".join(missing) + "\n\n"
                    f"Strengthen these topics before building. I want you to succeed, "
                    f"not get frustrated by gaps! 💪"
                ),
            }

        return {
            "approved": True,
            "missing": [],
            "message": "✅ **Hardware Project Approved!** You have the knowledge. Time to build! 🔧"
        }

    def get_study_tasks(self, topic: str) -> str:
        """Generate study tasks for a specific topic."""
        topic_info = CURRICULUM.get(topic)
        if not topic_info:
            return f"Topic '{topic}' not in the curriculum. Available: {', '.join(CURRICULUM.keys())}"

        mastery = self.db.get_mastery(topic) if self.db else None
        score = mastery["score"] if mastery else 0

        tasks = [f"📋 **Study Plan: {topic.replace('_', ' ').title()}** (Mastery: {score}%)\n"]

        # Recommend resources
        tasks.append("📖 **Recommended Resources:**")
        for r in topic_info.get("resources", []):
            tasks.append(f"  • {r}")

        # Recommend subtopics to focus on
        tasks.append("\n🎯 **Subtopics to Cover:**")
        for i, sub in enumerate(topic_info.get("subtopics", []), 1):
            sub_mastery = self.db.get_mastery(sub) if self.db else None
            sub_score = sub_mastery["score"] if sub_mastery else 0
            status = "✅" if sub_score >= MASTERY_THRESHOLD_ADVANCE else "📌"
            tasks.append(f"  {status} {i}. {sub.replace('_', ' ').title()} ({sub_score}%)")

        # Specific actions based on mastery level
        tasks.append("\n📝 **This Week's Tasks:**")
        if score < 30:
            tasks.append("  1. Watch introductory lecture on this topic")
            tasks.append("  2. Read the first relevant chapter carefully")
            tasks.append("  3. Complete 10 practice problems at difficulty 1")
        elif score < 60:
            tasks.append("  1. Review weak subtopics identified above")
            tasks.append("  2. Complete 10 practice problems at difficulty 2")
            tasks.append("  3. Try to explain one key concept in your own words")
        else:
            tasks.append("  1. Attempt advanced problems at difficulty 3")
            tasks.append("  2. Work through a real-world application example")
            tasks.append("  3. Consider a hardware project that uses this knowledge")

        return "\n".join(tasks)

    def get_curriculum_overview(self) -> str:
        """Return a formatted overview of the entire curriculum."""
        lines = ["📚 **Physics Curriculum Overview**\n"]

        for topic, info in sorted(CURRICULUM.items(), key=lambda x: x[1]["order"]):
            mastery = self.db.get_mastery(topic) if self.db else None
            score = mastery["score"] if mastery else 0
            bar = "█" * int(score / 10) + "░" * (10 - int(score / 10))

            prereqs = info.get("physics_prereqs", []) + info.get("math_prereqs", [])
            prereq_str = ", ".join(prereqs) if prereqs else "None"

            lines.append(f"**{info['order']}. {topic.replace('_', ' ').title()}** [{bar}] {score}%")
            lines.append(f"   {info['description']}")
            lines.append(f"   Prerequisites: {prereq_str}")
            lines.append("")

        return "\n".join(lines)

    def _build_physics_context(self) -> str:
        """Build context string about physics mastery for LLM."""
        if not self.db:
            return "No mastery data available."

        mastery = self.db.get_all_mastery()
        physics_topics = [m for m in mastery if m["category"] in
                          ("physics", "mechanics", "electromagnetism", "thermodynamics",
                           "waves_optics", "quantum_basics", "physics_mechanics")]

        if not physics_topics:
            return "Student mastery: No physics topics tracked yet. Likely a beginner — start with mechanics."

        lines = ["Student's current physics mastery:"]
        for m in physics_topics:
            lines.append(f"  - {m['topic']}: {m['score']}% ({m['problems_attempted']} problems attempted)")
        return "\n".join(lines)
