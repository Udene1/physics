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
You help students stay consistent, recap their progress, and set small, achievable goals.
If a student is frustrated, be empathetic and suggest a break or a simpler task.
"""


class CompanionAgent(BaseAgent):
    """Daily Companion — motivation, progress review, micro-goal setting."""

    def __init__(self, **kwargs):
        super().__init__(
            name="Companion",
            system_prompt=SYSTEM_PROMPT,
            **kwargs
        )

    def chat(self, user_msg: str, context: str = "", student_id: int = 1) -> str:
        """Enhanced chat for the Companion with student-specific context."""
        student_info = ""
        if self.db:
            student = self.db.get_student(student_id)
            if student:
                student_info = f"You are talking to {student['nickname']}."
        
        full_context = f"{context}\n\n{student_info}" if context else student_info
        return super().chat(user_msg, full_context, student_id=student_id)

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
