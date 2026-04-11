"""
main.py — Entry point for the AI Learning Companion.

Orchestrates multi-agent system with CLI chat loop, intent routing,
auto-detected LLM backend (Gemini cloud or Ollama local), and session artifacts.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from agents.base import detect_backend, detect_model, OLLAMA_AVAILABLE
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
    "feynman", "maxwell", "kirchhoff", "kinematics", "statics", "dynamics",
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

    if msg_lower.startswith("/"):
        if msg_lower.startswith(("/problems", "/practice", "/verify", "/check", "/hint", "/next")):
            return "math", True
        if msg_lower.startswith(("/lesson", "/teach")):
            # Check keywords for lesson routing
            if any(kw in msg_lower for kw in PHYSICS_KEYWORDS):
                return "physics", True
            return "math", True
        if msg_lower.startswith(("/builds", "/projects", "/build ")):
            return "hardware", True
        if msg_lower.startswith(("/report", "/progress", "/weekly")):
            return "progress", True
        if msg_lower.startswith(("/curriculum", "/prereq", "/study")):
            return "physics", True
        if msg_lower.startswith(("/goals", "/greet")):
            return "companion", True

    scores = {
        "math": sum(1 for kw in MATH_KEYWORDS if kw in msg_lower),
        "physics": sum(1 for kw in PHYSICS_KEYWORDS if kw in msg_lower),
        "hardware": sum(1 for kw in HARDWARE_KEYWORDS if kw in msg_lower),
        "companion": sum(1 for kw in COMPANION_KEYWORDS if kw in msg_lower),
    }

    best = max(scores, key=scores.get)
    if scores[best] > 0:
        return best, True
    return "companion", False


def init_agents(db=None):
    """Initialize all agents with auto-detected LLM backend."""
    if db is None:
        db = ProgressDB()

    backend, model = detect_backend()
    kwargs = {"db": db, "backend": backend, "backend_model": model}

    agents = {
        "companion": CompanionAgent(**kwargs),
        "math": MathTutorAgent(**kwargs),
        "physics": PhysicsSupervisorAgent(**kwargs),
        "hardware": HardwareBridgeAgent(**kwargs),
        "progress": ProgressTrackerAgent(**kwargs),
    }
    return agents, backend, model, db


AGENT_LABELS = {
    "companion": "🌟 Companion",
    "math": "📐 MathTutor",
    "physics": "⚛️ PhysicsSupervisor",
    "hardware": "🔧 HardwareBridge",
    "progress": "📊 ProgressTracker",
}


def handle_message(msg: str, agents: dict, db, student_id: int) -> tuple[str, str]:
    """
    Process a user message and return (agent_label, response).
    Used by both CLI and Flask web app.
    """
    msg_lower = msg.lower().strip()

    if msg_lower in ("/help", "help"):
        return "📚 Help", HELP_TEXT

    if msg_lower == "/curriculum":
        return "⚛️ PhysicsSupervisor", agents["physics"].get_curriculum_overview(student_id)

    if msg_lower.startswith("/study "):
        topic = msg_lower.replace("/study ", "").strip()
        return "⚛️ PhysicsSupervisor", agents["physics"].get_study_tasks(student_id, topic)

    if msg_lower.startswith("/prereq "):
        topic = msg_lower.replace("/prereq ", "").strip()
        result = agents["physics"].check_prerequisites(student_id, topic)
        return "⚛️ PhysicsSupervisor", result["message"]

    if msg_lower == "/goals":
        goals = db.get_pending_goals(student_id)
        if goals:
            lines = ["📋 **Pending Goals:**"]
            for g in goals:
                lines.append(f"  • [{g['id']}] {g['description']}")
            return "📋 Goals", "\n".join(lines)
        return "📋 Goals", "No pending goals — ask the Companion to set some!"

    # Route to agent
    intent, was_matched = classify_intent(msg)
    
    # Check for session stickiness
    if intent == "companion" and not msg.startswith("/"):
        last_agent = db.get_meta("last_active_agent")
        
        # If Math Tutor has an active problem, it takes precedence
        math_agent = agents.get("math")
        if math_agent:
            state = math_agent.get_student_state(student_id)
            if state.get("problems"):
                # If it looks like a number/formula OR a specific session command
                is_math_like = len(msg) < 20 and (any(c.isdigit() for c in msg) or any(c in "+-*/^()=" for c in msg))
                is_session_cmd = msg_lower in ("hint", "next", "next problem", "give me a hint")
                if is_math_like or is_session_cmd:
                    intent = "math"
                    last_agent = None # Math state won

        # Otherwise, if we had a last active agent that isn't companion, 
        # and this message didn't explicitly trigger companion keywords, stick to it.
        if intent == "companion" and not was_matched and last_agent and last_agent != "companion":
            intent = last_agent

    # If intent is companion, inject roadmap context
    context = ""
    if intent == "companion":
        try:
            roadmap = agents["physics"].get_roadmap_status(student_id)
            context = (
                f"Current Roadmap Status:\n"
                f"- Focus: {roadmap['current_focus']}\n"
                f"- Next Step: {roadmap['next_step']}\n"
                f"- Hardware Milestone: {roadmap['hardware_suggestion'] or 'None yet'}\n"
                f"- Overall Progress: {roadmap['overall_progress']}%\n"
            )
        except Exception: pass

    agent = agents[intent]
    label = AGENT_LABELS.get(intent, "🤖 Agent")
    
    # Update student activity/streak
    db.update_streak(student_id)
    
    # Save last active agent for next turn
    db.set_meta("last_active_agent", intent)
    
    response = agent.chat(msg, context=context, student_id=student_id)

    db.log_interaction(
        student_id=student_id,
        agent=agent.name, topic=intent,
        user_input=msg[:500], agent_response=response[:500], result="ok",
    )
    return label, response


HELP_TEXT = """
📚 **Available Commands:**

**Math:** /lesson <topic> · /problems <topic> [difficulty] [count] · /verify <answer> · /hint · /next
**Physics:** /curriculum · /study <topic> · /prereq <topic>
**Hardware:** /builds · /build <name>
**Progress:** /report · /weekly · /goals
**General:** /help · /quit

Or just type naturally — I'll route you to the right agent! 🤖
"""

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║                 🧠 AI Learning Companion 🧠                 ║
║     Math · Physics · Hardware — Build to Improve Lives      ║
╠══════════════════════════════════════════════════════════════╣
║  /problems · /builds · /curriculum · /report · /help · /quit ║
╚══════════════════════════════════════════════════════════════╝
"""


def main():
    """CLI entry point."""
    print(BANNER)

    print("📦 Initializing...")
    agents, backend, model, db = init_agents()
    print(f"   ✅ Backend: {backend} ({model or 'offline'})")
    print(f"   ✅ All agents ready\n")

    print("=" * 60)
    print(agents["companion"].greet(student_id=1))
    
    # Show Roadmap Summary in greeting
    try:
        roadmap = agents["physics"].get_roadmap_status(student_id=1)
        print(f"\n📍 **Current Focus:** {roadmap['current_focus']}")
        print(f"🎯 **Next Milestone:** {roadmap['next_step']}")
        if roadmap['hardware_suggestion']:
            print(f"🔧 **Hardware Gate:** {roadmap['hardware_suggestion']}")
        
        prog = roadmap['overall_progress']
        bar = "█" * (prog // 5) + "░" * (20 - (prog // 5))
        print(f"\n🌍 **Journey Progress:** [{bar}] {prog}%")
    except Exception: pass
    print("=" * 60)

    while True:
        try:
            user_input = input("\n🧑 You: ").strip()
        except (KeyboardInterrupt, EOFError):
            user_input = "/quit"

        if not user_input:
            continue

        if user_input.lower() in ("/quit", "/exit", "quit", "exit"):
            print("\n📝 Generating session artifact...")
            filepath = agents["progress"].generate_session_artifact()
            print(f"   ✅ Saved to: {filepath}")
            print("\n👋 Keep learning, keep building! See you next session! 💪🌍")
            db.close()
            break

        label, response = handle_message(user_input, agents, db, student_id=1)
        print(f"\n{label}:\n{response}")


if __name__ == "__main__":
    main()
