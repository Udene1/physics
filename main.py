"""main.py — Entry point for the AI Learning Companion."""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, os.path.dirname(__file__))

from agents.base import detect_backend
from agents.companion import CompanionAgent
from agents.math_tutor import MathTutorAgent
from agents.physics_supervisor import PhysicsSupervisorAgent
from agents.hardware_bridge import HardwareBridgeAgent
from agents.progress_tracker import ProgressTrackerAgent
from tools.progress_db import ProgressDB
from tools.learning_engine import LearningEngine
from tools.skill_graph import choose_next_skill, get_skill

MATH_KEYWORDS = ["algebra", "calculus", "integral", "derivative", "equation", "solve", "factor", "simplify", "matrix", "vector", "trigonometry", "sin", "cos", "tan", "limit", "proof", "function", "polynomial", "math", "calculate", "formula"]
PHYSICS_KEYWORDS = ["physics", "mechanics", "force", "energy", "momentum", "velocity", "acceleration", "newton", "gravity", "electromagnetism", "circuit", "voltage", "current", "resistance", "magnetic", "wave", "optics", "thermodynamics", "heat", "entropy", "quantum", "photon", "electron", "field", "potential", "frequency", "oscillation", "kinematics", "statics", "dynamics"]
HARDWARE_KEYWORDS = ["build", "hardware", "arduino", "sensor", "circuit", "solder", "component", "project", "device", "prototype", "breadboard", "led", "resistor", "capacitor", "microcontroller", "schematic", "pcb"]
COMPANION_KEYWORDS = ["hello", "hi", "hey", "good morning", "good evening", "motivation", "tired", "frustrated", "bored", "encourage", "goal", "plan", "feeling", "break", "stressed"]


def classify_intent(msg: str):
    text = msg.lower()
    if text.startswith("/"):
        if text.startswith(("/problems", "/practice", "/verify", "/check", "/hint", "/next")): return "math", True
        if text.startswith(("/lesson", "/teach")): return ("physics", True) if any(k in text for k in PHYSICS_KEYWORDS) else ("math", True)
        if text.startswith(("/builds", "/projects", "/build ")): return "hardware", True
        if text.startswith(("/report", "/progress", "/weekly")): return "progress", True
        if text.startswith(("/curriculum", "/prereq", "/study")): return "physics", True
        if text.startswith(("/goals", "/greet")): return "companion", True
    scores = {"math": sum(k in text for k in MATH_KEYWORDS), "physics": sum(k in text for k in PHYSICS_KEYWORDS), "hardware": sum(k in text for k in HARDWARE_KEYWORDS), "companion": sum(k in text for k in COMPANION_KEYWORDS)}
    best = max(scores, key=scores.get)
    return (best, True) if scores[best] else ("companion", False)


def init_agents(db=None):
    db = db or ProgressDB()
    backend, model = detect_backend()
    kwargs = {"db": db, "backend": backend, "backend_model": model}
    agents = {"companion": CompanionAgent(**kwargs), "math": MathTutorAgent(**kwargs), "physics": PhysicsSupervisorAgent(**kwargs), "hardware": HardwareBridgeAgent(**kwargs), "progress": ProgressTrackerAgent(**kwargs)}
    return agents, backend, model, db

AGENT_LABELS = {"companion": "🌟 Companion", "math": "📐 MathTutor", "physics": "⚛️ PhysicsSupervisor", "hardware": "🔧 HardwareBridge", "progress": "📊 ProgressTracker"}


def _question_text(question):
    if not question: return "The learner discovery assessment is complete."
    choices = "\n".join(f"  {i}. {c}" for i, c in enumerate(question["choices"], 1))
    return f"🧭 **Learner Discovery — {question['number']}/{question['total']}**\n\n{question['prompt']}\n\n{choices}\n\nAnswer with `/answer <number>`. There is no penalty for not knowing."


def _snapshot_text(snapshot):
    if snapshot["status"] != "complete":
        p = snapshot["diagnostic_progress"]
        return f"🧭 Diagnostic in progress: {p['answered']}/{p['total']} answered."
    return ("🎯 **Your learning position**\n\n"
            f"Stage: **{snapshot['current_stage'].replace('_', ' ').title()}**\n"
            f"Current focus: **{snapshot['current_skill'].replace('_', ' ').title()}**\n"
            f"Next action: **{snapshot['next_action']}**\n\n"
            "Uden keeps this state in the learner record, so returning later does not reset the journey.")


def _learner_command(engine, student_id, text):
    if text in ("/start", "/diagnostic", "/assess", "start assessment"):
        engine.start(student_id)
        return "🧭 Learner Discovery", _question_text(engine.current_question(student_id))
    if text.startswith("/answer"):
        parts = text.split()
        if len(parts) != 2 or not parts[1].isdigit(): return "🧭 Learner Discovery", "Use `/answer 1`, `/answer 2`, `/answer 3`, or `/answer 4`."
        question = engine.current_question(student_id)
        if not question: return "🧭 Learner Discovery", _snapshot_text(engine.snapshot(student_id))
        try: result = engine.answer(student_id, question["id"], int(parts[1]) - 1)
        except ValueError as exc: return "🧭 Learner Discovery", f"I couldn't record that answer: {exc}"
        if result.get("complete"): return "🧭 Learner Discovery", _snapshot_text(result)
        feedback = "✅ Good." if result["correct"] else "🧩 Useful evidence — Uden will use it to place you correctly."
        return "🧭 Learner Discovery", f"{feedback}\n\n{_question_text(result['next'])}"
    if text in ("/where", "/learning-state", "/state"):
        return "🧭 Learner Discovery", _snapshot_text(engine.snapshot(student_id))
    if text.startswith("/skill"):
        parts = text.split(maxsplit=1)
        if len(parts) != 2: return "🧭 Learner Map", "Use `/skill <skill-id>`, for example `/skill motion`."
        try: skill = get_skill(parts[1].strip())
        except ValueError as exc: return "🧭 Learner Map", str(exc)
        status = engine.skill_status(student_id, skill.id)
        if status["ready"]: return "🧭 Learner Map", f"**{skill.name}** is ready. Current mastery: {status['score']:.1f}%."
        missing = ", ".join(get_skill(s).name for s in status["missing_prerequisites"])
        return "🧭 Learner Map", f"**{skill.name}** needs: {missing}. Current mastery: {status['score']:.1f}%."
    if text == "/next-skill":
        snapshot = engine.snapshot(student_id)
        skill = choose_next_skill(snapshot["skills"])
        return "🧭 Learner Map", f"🎯 Next skill: **{skill.name}** ({skill.domain})." if skill else "No unmet actionable skill remains in the current graph."
    return None


def handle_message(msg: str, agents: dict, db, student_id: int = 1, image=None):
    text = msg.lower().strip()
    learner = _learner_command(LearningEngine(db), student_id, text)
    if learner: return learner
    if text in ("/help", "help"): return "📚 Help", HELP_TEXT
    if text == "/curriculum": return "⚛️ PhysicsSupervisor", agents["physics"].get_curriculum_overview(student_id)
    if text == "/goals":
        goals = db.get_pending_goals(student_id)
        return "📋 Goals", "\n".join(f"  • [{g['id']}] {g['description']}" for g in goals) if goals else "No pending goals — ask the Companion to set some!"

    intent, matched = classify_intent(msg)
    last_agent = db.get_meta("last_active_agent")
    if last_agent and last_agent != "companion" and not matched: intent = last_agent
    agent = agents[intent]
    db.update_streak(student_id)
    db.set_meta("last_active_agent", intent)
    response = agent.chat(msg, context="", student_id=student_id, image=image)
    db.log_interaction(student_id, agent.name, intent, msg[:500], response[:500], "ok")
    return AGENT_LABELS.get(intent, "🤖 Agent"), response

HELP_TEXT = """
📚 **Available Commands:**

**Start:** /start · /diagnostic · /answer <1-4> · /where
**Learner Map:** /skill <skill-id> · /next-skill
**Math:** /lesson <topic> · /problems <topic> [difficulty] [count] · /verify <answer> · /hint · /next
**Physics:** /curriculum · /study <topic> · /prereq <topic>
**Hardware:** /builds · /build <name>
**Progress:** /report · /weekly · /goals
**General:** /help · /quit
"""


def main():
    agents, backend, model, db = init_agents()
    print("🧠 AI Learning Companion — Math · Physics · Hardware")
    print(f"Backend: {backend} ({model or 'offline'})")
    print(agents["companion"].greet(student_id=1))
    while True:
        try: user_input = input("\n🧑 You: ").strip()
        except (KeyboardInterrupt, EOFError): user_input = "/quit"
        if not user_input: continue
        if user_input.lower() in ("/quit", "/exit", "quit", "exit"):
            db.close(); break
        label, response = handle_message(user_input, agents, db, student_id=1)
        print(f"\n{label}:\n{response}")


if __name__ == "__main__": main()
