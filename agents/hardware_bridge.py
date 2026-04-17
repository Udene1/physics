"""
agents/hardware_bridge.py — Hardware Bridge Agent.

Suggests practical hardware builds tied to current physics/math mastery.
Provides component lists (Nigeria-available), starter code, and impact framing.
Supports multi-student project tracking.
"""

import json
from .base import BaseAgent

HARDWARE_PROJECTS = {
    "led_circuit": {
        "name": "LED Circuit with Resistor",
        "level": "beginner",
        "required_topics": ["electrostatics", "electric_circuits"],
        "min_mastery": 30,
        "description": "Build a simple LED circuit with a current-limiting resistor.",
        "impact": "Foundation for all electronic builds — indicator lights for any device!",
        "components": [
            "1x LED (any color) — N50", "1x 220 ohm resistor — N10",
            "1x 9V battery + connector — N300", "Breadboard — N500", "Jumper wires — N200",
        ],
        "total_cost": "~N1,100 (~$1.50)",
        "schematic": "9V(+) -> 220ohm -> LED(+) -> LED(-) -> Battery(-)",
    },
    "soil_moisture_sensor": {
        "name": "Soil Moisture Sensor for Agriculture",
        "level": "intermediate",
        "required_topics": ["electric_circuits", "electrostatics"],
        "min_mastery": 50,
        "description": "Two nails + Arduino to help farmers know when to water crops.",
        "impact": "Directly helps farmers in Benin/Nigeria optimize water usage!",
        "components": [
            "1x Arduino Uno/Nano — N3,000-5,000", "2x galvanized nails — N50",
            "1x 10k ohm resistor — N10", "Wire, breadboard — N700",
        ],
        "total_cost": "~N5,500 (~$7)",
        "schematic": "5V -> Nail1(soil) | Nail2(soil) -> 10k -> GND; Nail2+R junction -> A0",
    },
    "pendulum_sensor": {
        "name": "Simple Pendulum Timer (Measure g)",
        "level": "beginner",
        "required_topics": ["kinematics", "oscillations"],
        "min_mastery": 40,
        "description": "Build a pendulum and measure its period to calculate g ~ 9.8 m/s2.",
        "impact": "Classic physics experiment — understand oscillations used in sensors!",
        "components": [
            "String (~1m) — N50", "Small weight (bolt) — N0",
            "Ruler — N200", "Stopwatch (phone) — N0",
        ],
        "total_cost": "~N250 manual",
        "schematic": "Mount -> String(L) -> Weight; T = 2*pi*sqrt(L/g)",
    },
}

SYSTEM_PROMPT = """You are the Hardware Bridge Agent — connecting physics/math knowledge to
REAL-WORLD hardware builds that improve lives in resource-limited settings like Benin City, Nigeria.

YOUR ROLE:
1. SUGGEST hardware projects matched to the student's mastery.
2. PROVIDE build instructions with Nigerian prices (Naira).
3. FRAME every project in terms of REAL IMPACT.
4. Deliver high-quality, local build guides.
"""


class HardwareBridgeAgent(BaseAgent):
    """Hardware Bridge — connects learning to practical builds."""

    def __init__(self, **kwargs):
        super().__init__(
            name="HardwareBridge",
            system_prompt=SYSTEM_PROMPT,
            **kwargs
        )

    def chat(self, user_msg: str, context: str = "", student_id: int = 1, image=None) -> str:
        msg_lower = user_msg.lower().strip()
        if msg_lower in ("/builds", "/projects", "show builds"):
            return self.list_available_projects(student_id)
        if msg_lower.startswith("/build "):
            key = msg_lower.replace("/build ", "").strip().replace(" ", "_")
            return self.teach_build(student_id, key)
        
        if msg_lower.startswith("/analyze") and image:
            return self.analyze_circuit(image, student_id)
        
        projects_ctx = self._build_projects_context(student_id)
        full_ctx = f"{context}\n\n{projects_ctx}" if context else projects_ctx
        return super().chat(user_msg, full_ctx, student_id=student_id, image=image)

    def analyze_circuit(self, image_data, student_id: int = 1) -> str:
        """Analyze an image of a circuit for errors or verification."""
        prompt = (
            "Analyze this hardware circuit image. Identify the components "
            "(e.g., Arduino, Breadboard, LED, Resistor). Look for common errors "
            "like missing ground wires, floating pins, or incorrect resistor placement. "
            "Provide helpful, encouraging advice in a Nigerian context."
        )
        return super().chat(prompt, context="Vision analysis mode.", student_id=student_id, image=image_data)

    def list_available_projects(self, student_id: int) -> str:
        lines = ["🔧 **Hardware Build Suggestions**\n"]
        
        # 1. Vetted Core Projects
        lines.append("### 🏆 Vetted Core Projects")
        for key, p in HARDWARE_PROJECTS.items():
            ready = True
            if self.db:
                for topic in p["required_topics"]:
                    m = self.db.get_mastery(student_id, topic)
                    if not m or m["score"] < p["min_mastery"]:
                        ready = False
                        break
            status = "✅ Ready" if ready else "🔒 Locked"
            lines.append(f"  {status} **[ /build {key} ]** {p['name']}\n        🌍 {p['impact']}")

        # 2. Dynamic Topic-Based Suggestions
        if self.db:
            all_topics = self.db.get_all_topics()
            dynamic = []
            for t in all_topics:
                if t["build_hint"] and t["category"] == "physics":
                    m = self.db.get_mastery(student_id, t["name"])
                    score = m["score"] if m else 0
                    if score >= 50: # Standard Hardware Gate
                        dynamic.append(f"  ✨ **{t['build_hint']}** (Based on your {t['name']} mastery!)")
            
            if dynamic:
                lines.append("\n### 💡 Experimental Suggestions")
                lines.extend(dynamic)

        return "\n".join(lines)

    def teach_build(self, student_id: int, project_key: str) -> str:
        """Provide detailed build instructions, using distillation if available."""
        project = HARDWARE_PROJECTS.get(project_key)
        topic_name = project['name'] if project else project_key.replace("_", " ").title()
        
        # 1. Check distilled local knowledge first
        if self.db:
            distilled = self.db.get_distilled_lesson(topic_name)
            if distilled:
                return f"{distilled['content']}\n\n(✨ *Note: This guide was served from my Local Knowledge Base.*)"

        if not project: return "Project not found."
        
        # 2. Generate a fresh build guide using LLM for more depth
        prompt = (
            f"Provide a detailed build guide for the hardware project: '{project['name']}'.\n"
            f"Description: {project['description']}\n"
            f"Impact: {project['impact']}\n"
            "Include a step-by-step assembly guide, wiring tips, and a 'Troubleshooting' section "
            "relevant for a student in Lagos/Benin City using locally sourced parts."
        )
        guide = super().chat(prompt, context="Provide a practical hardware build guide.", student_id=student_id)
        
        # 3. Save to local DB for distillation
        if self.db and "Offline" not in guide:
            self.db.save_distilled_lesson(topic_name, "hardware", guide, self.model)

        if self.db:
            self.db.log_interaction(
                student_id=student_id,
                agent="HardwareBridge",
                topic=topic_name,
                user_input=f"/build {project_key}",
                agent_response=guide,
                result="lesson"
            )
        return guide

    def _build_projects_context(self, student_id: int) -> str:
        if not self.db: return ""
        completed = self.db.get_projects(student_id, status="completed")
        in_progress = self.db.get_projects(student_id, status="in_progress")
        return f"Projects: {len(completed)} completed, {len(in_progress)} in progress."
