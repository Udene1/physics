"""
integrations/web_ui.py — Optional Gradio web UI.

Provides a browser-based chat interface wrapping the same orchestrator.
Run with: python -m integrations.web_ui
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def launch_web_ui():
    """Launch Gradio chat UI wrapping the AI Learning Companion."""
    try:
        import gradio as gr
    except ImportError:
        print("⚠️ Gradio not installed. Install with: pip install gradio")
        print("   Then run: python -m integrations.web_ui")
        return

    from agents.base import detect_model
    from agents.companion import CompanionAgent
    from agents.math_tutor import MathTutorAgent
    from agents.physics_supervisor import PhysicsSupervisorAgent
    from agents.hardware_bridge import HardwareBridgeAgent
    from agents.progress_tracker import ProgressTrackerAgent
    from tools.progress_db import ProgressDB
    from main import classify_intent

    # Initialize
    db = ProgressDB()
    model = detect_model()

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

    def respond(message, history):
        """Process user message and return agent response."""
        if not message.strip():
            return ""

        msg_lower = message.lower().strip()

        if msg_lower in ("/help", "help"):
            return (
                "**Commands:** /problems, /verify, /hint, /builds, "
                "/curriculum, /study, /report, /weekly, /goals"
            )

        if msg_lower == "/curriculum":
            return physics_sup.get_curriculum_overview()

        if msg_lower.startswith("/study "):
            topic = msg_lower.replace("/study ", "").strip()
            return physics_sup.get_study_tasks(topic)

        intent = classify_intent(message)
        agent = agents[intent]
        response = agent.chat(message)

        db.log_interaction(
            agent=agent.name, topic=intent,
            user_input=message[:500], agent_response=response[:500], result="ok",
        )
        return response

    # Build UI
    greeting = companion.greet()
    status = f"Model: {model or 'OFFLINE'}"

    demo = gr.ChatInterface(
        fn=respond,
        title="🧠 AI Learning Companion",
        description=f"Math · Physics · Hardware — Build to Improve Lives\n\n{status}",
        examples=[
            "Hello! What should I study today?",
            "/problems algebra 1 5",
            "/curriculum",
            "/builds",
            "Explain Newton's second law",
            "What is a derivative?",
            "/report",
        ],
        theme=gr.themes.Soft(),
    )

    print(f"\n🌐 Launching web UI...")
    print(f"   Model: {model or 'OFFLINE'}")
    demo.launch(share=False, server_name="127.0.0.1", server_port=7860)


if __name__ == "__main__":
    launch_web_ui()
