"""
main.py — Entry point for the AI Learning Companion.

Orchestrates multi-agent system with CLI chat loop, intent routing,
Ollama model auto-detection, and session artifact generation.
"""

import os
import sys
import re

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from agents.base import detect_model, OLLAMA_AVAILABLE
from agents.companion import CompanionAgent
from agents.math_tutor import MathTutorAgent
from agents.physics_supervisor import PhysicsSupervisorAgent
from agents.hardware_bridge import HardwareBridgeAgent
from agents.progress_tracker import ProgressTrackerAgent
from tools.progress_db import ProgressDB

# ── Intent Classification ────────────────────────────────────────

MATH_KEYWORDS = [
    "algebra", "calculus", "integral", "derivative", "equation", "solve",
    "factor", "simplify", "matrix", "vector", "eigenvalue", "linear algebra",
    "differential equation", "trigonometry", "sin", "cos", "tan", "limit",
    "series", "proof", "function", "polynomial", "logarithm", "exponent",
    "math", "calculate", "computation", "formula",
]

PHYSICS_KEYWORDS = [
    "physics", "mechanics", "force", "energy", "momentum", "velocity",
    "acceleration", "newton", "gravity", "electromagnetism", "circuit",
    "voltage", "current", "resistance", "magnetic", "wave", "optics",
    "thermodynamics", "heat", "entropy", "quantum", "photon", "electron",
    "field", "potential", "capacitor", "inductor", "frequency", "oscillation",
    "feynman", "maxwell", "kirchhoff",
]

HARDWARE_KEYWORDS = [
    "build", "hardware", "arduino", "sensor", "circuit", "solder",
    "component", "project", "device", "prototype", "breadboard", "led",
    "resistor", "capacitor", "microcontroller", "schematic", "pcb",
]

COMPANION_KEYWORDS = [
    "hello", "hi", "hey", "good morning", "good evening", "motivation",
    "tired", "frustrated", "bored", "encourage", "goal", "plan",
    "how are you", "feeling", "break", "stressed",
]


def classify_intent(msg: str) -> str:
    """Classify user message intent to route to appropriate agent."""
    msg_lower = msg.lower()

    # Command shortcuts always take priority
    if msg_lower.startswith("/"):
        if msg_lower.startswith(("/problems", "/practice", "/verify", "/check", "/hint", "/next")):
            return "math"
        if msg_lower.startswith(("/builds", "/projects", "/build ")):
            return "hardware"
        if msg_lower.startswith(("/report", "/progress", "/weekly")):
            return "progress"
        if msg_lower.startswith(("/curriculum", "/prereq", "/study")):
            return "physics"
        if msg_lower.startswith(("/goals", "/greet")):
            return "companion"

    # Keyword scoring
    scores = {
        "math": sum(1 for kw in MATH_KEYWORDS if kw in msg_lower),
        "physics": sum(1 for kw in PHYSICS_KEYWORDS if kw in msg_lower),
        "hardware": sum(1 for kw in HARDWARE_KEYWORDS if kw in msg_lower),
        "companion": sum(1 for kw in COMPANION_KEYWORDS if kw in msg_lower),
    }

    best = max(scores, key=scores.get)
    if scores[best] > 0:
        return best

    # Default to companion for general chat
    return "companion"


# ── Banner ────────────────────────────────────────────────────────

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║                 🧠 AI Learning Companion 🧠                 ║
║     Math · Physics · Hardware — Build to Improve Lives      ║
╠══════════════════════════════════════════════════════════════╣
║  Commands:                                                   ║
║    /problems <topic> [difficulty] [count] — Practice math    ║
║    /verify <answer>    — Check your answer                   ║
║    /hint               — Get a hint                          ║
║    /builds             — See hardware projects               ║
║    /build <name>       — Project details                     ║
║    /curriculum         — Physics curriculum overview          ║
║    /study <topic>      — Get study tasks                     ║
║    /report             — View progress report                ║
║    /weekly             — Weekly summary                      ║
║    /goals              — View pending goals                  ║
║    /help               — Show this help                      ║
║    /quit               — Save session & exit                 ║
╚══════════════════════════════════════════════════════════════╝
"""

HELP_TEXT = """
📚 **Available Commands:**

**Math & Practice:**
  /problems <topic> [difficulty] [count] — Generate practice problems
    Topics: algebra, trigonometry, calculus, linear_algebra,
            differential_equations, physics_mechanics
  /verify <answer>  — Check your answer against current problem
  /hint             — Get a hint for current problem
  /next             — Skip to next problem

**Physics:**
  /curriculum       — View full physics curriculum with progress
  /study <topic>    — Get study plan for a topic
  /prereq <topic>   — Check prerequisites for a topic

**Hardware:**
  /builds           — List all hardware projects
  /build <name>     — Get details for a specific project

**Progress:**
  /report           — View your progress report
  /weekly           — Weekly summary report
  /goals            — View pending goals

**General:**
  /help             — Show this help
  /quit             — Save session artifact and exit

Or just type naturally — I'll route you to the right agent! 🤖
"""


def main():
    """Main entry point — sets up agents and runs CLI chat loop."""
    print(BANNER)

    # ── Database Setup ────────────────────────────────────────
    print("📦 Initializing progress database...")
    db = ProgressDB()
    print("   ✅ Database ready\n")

    # ── Ollama Model Detection ────────────────────────────────
    print("🔍 Detecting Ollama models...")
    if not OLLAMA_AVAILABLE:
        print("   ⚠️  ollama package not installed. Install with: pip install ollama")
        print("   Running in OFFLINE mode (math verification & progress tracking only)\n")
        model = None
    else:
        model = detect_model()
        if model:
            print(f"   ✅ Using model: {model}\n")
        else:
            print("   ⚠️  No Ollama models found. Start Ollama and pull a model:")
            print("      ollama pull qwen2.5:7b")
            print("   Running in OFFLINE mode\n")

    # ── Agent Initialization ──────────────────────────────────
    print("🤖 Initializing agents...")
    companion = CompanionAgent(db=db, model=model)
    math_tutor = MathTutorAgent(db=db, model=model)
    physics_sup = PhysicsSupervisorAgent(db=db, model=model)
    hardware = HardwareBridgeAgent(db=db, model=model)
    progress = ProgressTrackerAgent(db=db, model=model)

    agents = {
        "companion": companion,
        "math": math_tutor,
        "physics": physics_sup,
        "hardware": hardware,
        "progress": progress,
    }
    print("   ✅ All agents ready\n")

    # ── Daily Greeting ────────────────────────────────────────
    print("=" * 60)
    print(companion.greet())
    print("=" * 60)
    print()

    # ── Main Chat Loop ────────────────────────────────────────
    while True:
        try:
            user_input = input("\n🧑 You: ").strip()
        except (KeyboardInterrupt, EOFError):
            user_input = "/quit"

        if not user_input:
            continue

        msg_lower = user_input.lower()

        # ── Special commands ──────────────────────────────────
        if msg_lower in ("/quit", "/exit", "quit", "exit"):
            print("\n📝 Generating session artifact...")
            filepath = progress.generate_session_artifact()
            print(f"   ✅ Saved to: {filepath}")
            print("\n👋 Keep learning, keep building! See you next session! 💪🌍")
            db.close()
            break

        if msg_lower in ("/help", "help"):
            print(HELP_TEXT)
            continue

        if msg_lower in ("/curriculum",):
            print(f"\n🤖 PhysicsSupervisor:\n{physics_sup.get_curriculum_overview()}")
            continue

        if msg_lower.startswith("/study "):
            topic = msg_lower.replace("/study ", "").strip()
            print(f"\n🤖 PhysicsSupervisor:\n{physics_sup.get_study_tasks(topic)}")
            continue

        if msg_lower.startswith("/prereq "):
            topic = msg_lower.replace("/prereq ", "").strip()
            result = physics_sup.check_prerequisites(topic)
            print(f"\n🤖 PhysicsSupervisor:\n{result['message']}")
            continue

        if msg_lower in ("/goals",):
            goals = db.get_pending_goals()
            if goals:
                print("\n📋 **Pending Goals:**")
                for g in goals:
                    print(f"  • [{g['id']}] {g['description']} (due: {g.get('due_date', 'N/A')})")
            else:
                print("\n📋 No pending goals — ask the Companion to set some!")
            continue

        # ── Route to agent ────────────────────────────────────
        intent = classify_intent(user_input)
        agent = agents[intent]
        agent_name = agent.name

        # Show which agent is responding
        label = {
            "companion": "🌟 Companion",
            "math": "📐 MathTutor",
            "physics": "⚛️ PhysicsSupervisor",
            "hardware": "🔧 HardwareBridge",
            "progress": "📊 ProgressTracker",
        }.get(intent, "🤖 Agent")

        print(f"\n{label}:")
        response = agent.chat(user_input)
        print(response)

        # Log the interaction
        db.log_interaction(
            agent=agent_name,
            topic=intent,
            user_input=user_input[:500],
            agent_response=response[:500],
            result="ok",
        )


if __name__ == "__main__":
    main()
