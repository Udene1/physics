"""
agents/companion.py — Daily Companion Agent.

Focuses on motivation, daily recaps, and goal setting for students.
Provides a friendly, encouraging personality.
"""

import random
from datetime import datetime
from .base import BaseAgent

GREETINGS = [
    "Kedu! Good {time_of_day}, let's build something today! 🚀",
    "Welcome back! Ready to master some physics this {time_of_day}? 🧠",
    "Ndewo! Great to see you're back at it. What's the goal for this {time_of_day}?",
    "Science never sleeps! Good {time_of_day}, ready to dive in?",
]

ENCOURAGEMENTS = [
    "You're doing great — consistency is the key to mastery! 💪",
    "Every problem you solve brings you closer to being an engineer. 🏗️",
    "Don't worry if it's tough; that's just your brain getting stronger! 🧠",
    "Remember: every great scientist started exactly where you are. 🌟",
]

FRUSTRATION_RESPONSES = [
    "I hear you. Physics can be tough, but you've got this! Let's take it one step at a time. 🧘",
    "It's okay to feel stuck. Why don't we try a simpler problem first? 💡",
    "Take a deep breath. Even Einstein had bad days! What part is confusing? 🤔",
]

SYSTEM_PROMPT = """You are the Daily Companion (Udene Physics). 
Your role is to be a friendly, encouraging mentor for students in Nigeria.
Use local context (e.g., Igbo greetings like 'Kedu', 'Ndewo') and keep motivation high.
You are NOT just a physics tutor; you are a friend. Feel free to engage in small talk.

YOUR PRIMARY MISSION:
Direct the student toward their "True Goal" of becoming a builder/engineer using physics.
You are aware of the 5-topic curriculum roadmap (Mechanics -> Electromagnetism -> Thermodynamics -> Waves -> Quantum).
Always keep the student aware of their current "milestone" and what hardware project is coming up next.

When the student's 'Brain' (LLM) is connected, be very talkative and creative. 
Reference their recent successes (from the data) to build confidence.
"""


class CompanionAgent(BaseAgent):
    """Daily Companion — roadmap guide, motivation, progress review."""

    def __init__(self, **kwargs):
        super().__init__(
            name="Companion",
            system_prompt=SYSTEM_PROMPT,
            **kwargs
        )

    def chat(self, user_msg: str, context: str = "", student_id: int = 1, image=None) -> str:
        """Enhanced chat with roadmap awareness and student-specific context."""
        student_info = ""
        roadmap_info = ""
        
        if self.db:
            student = self.db.get_student(student_id)
            if student:
                # Localize with nickname
                student_info = f"You are talking to {student['nickname']}."
                
            # Fetch recent mistakes or successes for deeper personalization
            recent = self.db.get_recent_interactions(student_id, limit=3)
            if recent:
                activities = [f"{r['agent']} ({r['topic']})" for r in recent if r.get('agent')]
                student_info += f" Recently, they: {', '.join(activities)}."

        # Backend info
        backend_info = f"Your current LLM backend is: {self._backend} ({self.model})."
        
        # Merge all into context
        full_context = f"{context}\n\n{student_info}\n{backend_info}" if context else f"{student_info}\n{backend_info}"
        
        return super().chat(user_msg, full_context, student_id=student_id, image=image)

    def greet(self, student_id: int) -> str:
        """Generate a daily greeting with progress summary for a specific student."""
        hour = datetime.now().hour
        time_of_day = "morning" if hour < 12 else "afternoon" if hour < 17 else "evening"
        greeting = random.choice(GREETINGS).format(time_of_day=time_of_day)

        context_parts = [greeting, ""]

        if self.db:
            summary = self.db.generate_summary(student_id)
            recent = self.db.get_recent_interactions(student_id, limit=5)
            
            if recent:
                context_parts.append("📊 **Recent Activity:**")
                topics = {i['topic'] for i in recent[:3] if i.get('topic')}
                for t in topics:
                    context_parts.append(f"  • Worked on: {t}")

            mastery = summary.get("mastery", [])
            if mastery:
                context_parts.append("\n🎯 **Top Mastery:**")
                for m in sorted(mastery, key=lambda x: x['score'], reverse=True)[:3]:
                    context_parts.append(f"  • {m['topic']}: {m['score']}%")

            streak = summary.get("streak", 0)
            if streak > 0:
                context_parts.append(f"\n🔥 You're on a **{streak}-day streak!** Keep it going!")

        context_parts.append(f"\n{random.choice(ENCOURAGEMENTS)}")
        return "\n".join(context_parts)
