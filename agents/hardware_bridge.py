"""
agents/hardware_bridge.py — Hardware Bridge Agent.

Suggests practical hardware builds tied to current physics/math mastery.
Provides component lists (Nigeria-available), starter code, and impact framing.
"""

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
    "arduino_voltmeter": {
        "name": "Arduino Digital Voltmeter",
        "level": "intermediate",
        "required_topics": ["electric_circuits", "electrostatics"],
        "min_mastery": 50,
        "description": "Use Arduino ADC to measure voltage (0-5V) and display on serial monitor.",
        "impact": "Cheap voltage monitoring for solar panels in rural areas!",
        "components": [
            "1x Arduino Uno/Nano — N3,000-5,000", "2x 10k ohm resistors — N20",
            "Breadboard + wires — N700", "USB cable — N300",
        ],
        "total_cost": "~N5,000 (~$6)",
        "schematic": "V_source -> R1(10k) -> Junction -> R2(10k) -> GND; Junction -> A0",
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
    "temperature_logger": {
        "name": "Temperature Data Logger",
        "level": "intermediate",
        "required_topics": ["temperature_heat", "electric_circuits"],
        "min_mastery": 45,
        "description": "Log temperature over time using LM35 sensor and Arduino.",
        "impact": "Monitor storage temps for medicine/vaccines in clinics!",
        "components": [
            "1x Arduino Uno/Nano — N3,000-5,000", "1x LM35 sensor — N300",
            "Breadboard + wires — N700",
        ],
        "total_cost": "~N5,000 (~$6)",
        "schematic": "LM35: Vs->5V, Vout->A0, GND->GND; Output 10mV per degree C",
    },
}

SYSTEM_PROMPT = """You are the Hardware Bridge Agent — connecting physics/math knowledge to
REAL-WORLD hardware builds that improve lives in resource-limited settings like Benin City, Nigeria.

YOUR ROLE:
1. SUGGEST hardware projects matched to the student's current mastery level.
2. PROVIDE build instructions: components (with Nigerian prices in Naira), schematics, code.
3. FRAME every project in terms of REAL IMPACT — who benefits and how.
4. Ensure components are AFFORDABLE and AVAILABLE in Nigeria.
5. Provide Python/Arduino starter code as learning scaffolds (leave gaps for learning).
6. Only suggest builds the Physics Supervisor has APPROVED.
7. Always explain the underlying physics of each component/circuit.
8. Connect to the vision: every device built is a step toward helping people.

Use clear sections: Components, Schematic, Code, Impact.
Include safety notes where relevant.
"""


class HardwareBridgeAgent(BaseAgent):
    """Hardware Bridge — connects learning to practical builds."""

    def __init__(self, **kwargs):
        super().__init__(
            name="HardwareBridge",
            system_prompt=SYSTEM_PROMPT,
            **kwargs
        )

    def chat(self, user_msg: str, context: str = "") -> str:
        msg_lower = user_msg.lower().strip()
        if msg_lower in ("/builds", "/projects", "show builds", "what can i build"):
            return self.list_available_projects()
        if msg_lower.startswith("/build "):
            key = msg_lower.replace("/build ", "").strip().replace(" ", "_")
            return self.get_project_details(key)
        projects_ctx = self._build_projects_context()
        full_ctx = f"{context}\n\n{projects_ctx}" if context else projects_ctx
        return super().chat(user_msg, full_ctx)

    def list_available_projects(self) -> str:
        lines = ["🔧 **Available Hardware Projects**\n"]
        for key, p in HARDWARE_PROJECTS.items():
            ready = True
            if self.db:
                for topic in p["required_topics"]:
                    m = self.db.get_mastery(topic)
                    if not m or m["score"] < p["min_mastery"]:
                        ready = False
                        break
            status = "✅ Ready" if ready else "🔒 Locked"
            lines.append(
                f"  {status} **{p['name']}** ({p['level']})\n"
                f"        Cost: {p['total_cost']} | Topics: {', '.join(p['required_topics'])}\n"
                f"        🌍 {p['impact']}\n"
            )
        lines.append("\nUse `/build <project_name>` for full details (e.g. `/build soil_moisture_sensor`).")
        return "\n".join(lines)

    def get_project_details(self, project_key: str) -> str:
        project = HARDWARE_PROJECTS.get(project_key)
        if not project:
            for key, proj in HARDWARE_PROJECTS.items():
                if project_key in key:
                    project = proj
                    break
        if not project:
            return f"Project '{project_key}' not found. Use `/builds` to see all."

        lines = [
            f"# 🔧 {project['name']}\n",
            f"**Level:** {project['level'].title()} | **Cost:** {project['total_cost']}\n",
            f"## 🌍 Impact\n{project['impact']}\n",
            "## 📋 Components",
        ]
        for c in project["components"]:
            lines.append(f"  • {c}")
        lines.append(f"\n## 📐 Schematic\n```\n{project['schematic']}\n```")
        lines.append(f"\n## 📝 Description\n{project['description']}")
        lines.append("\n*Ask me for starter code or simulation ideas for this project!*")
        return "\n".join(lines)

    def _build_projects_context(self) -> str:
        if not self.db:
            return ""
        completed = self.db.get_projects(status="completed")
        in_progress = self.db.get_projects(status="in_progress")
        parts = []
        if completed:
            parts.append(f"Completed projects: {len(completed)}")
        if in_progress:
            parts.append(f"In-progress projects: {len(in_progress)}")
        return "\n".join(parts) if parts else "No hardware projects started yet."
