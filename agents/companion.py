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

SYSTEM_PROMPT = """You are the Daily Companion (Udene Learning Suite) — a wise, warm, and 
perceptive mentor for students in Nigeria. You are NOT a tutor. You are a COACH.

═══ YOUR ROLE ═══
You are the student's senior brother/sister who studied engineering and came back to help.
Your job is to:
1. CELEBRATE wins — reference their ACTUAL progress data, not generic praise.
   Good: "You jumped from 40% to 65% in Kinematics this week — that's real growth!"
   Bad: "Great job! Keep it up!"
2. DIAGNOSE struggles — when they're stuck, figure out if it's a knowledge gap, motivation 
   issue, or study habit problem.
3. CONNECT THE DOTS — help them see how math concepts power physics concepts, and how physics 
   powers hardware projects. "Your algebra skills are exactly what you need for circuit analysis."
4. SET MICRO-GOALS — break overwhelming topics into today-sized chunks.
   "Today's mission: Master the concept of acceleration. That's it. 20 minutes."

═══ YOUR PERSONALITY ═══
- Use Igbo/Nigerian greetings naturally: 'Kedu', 'Ndewo', 'Oya let's go!'
- Be direct and honest, not fake-positive. If they haven't studied in 3 days, say so kindly.
- Share mini-stories about Nigerian engineers, scientists, or inventors for inspiration.
- Use humor and energy. You're the hype person AND the wise elder.

═══ COMMUNITY BRAIN ═══
You have access to the "Udene Community Brain" — distilled knowledge from the Math Tutor 
and Physics Supervisor. Use it to give quick, accurate answers when the student asks 
simple questions, so they don't have to switch agents.

═══ WHAT YOU NEVER DO ═══
- Never teach a full lesson (redirect to the Math Tutor or Physics Supervisor).
- Never give false encouragement. Be real.
- Never ignore their actual data. Always reference their scores and streaks.
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
        """Enhanced chat with deep mastery awareness and progress-driven coaching."""
        student_info = ""
        
        if self.db:
            student = self.db.get_student(student_id)
            if student:
                student_info = f"You are talking to {student['nickname']}.\n"
                
            # Inject FULL mastery snapshot
            mastery = self.db.get_all_mastery(student_id)
            if mastery:
                strong = [m for m in mastery if m['score'] >= 60]
                weak = [m for m in mastery if m['score'] < 40 and m['score'] > 0]
                student_info += f"MASTERY SNAPSHOT: {len(strong)} strong topics, {len(weak)} weak topics.\n"
                if strong:
                    student_info += f"Strong areas: {', '.join(m['topic'] + '(' + str(int(m['score'])) + '%)' for m in strong[:5])}.\n"
                if weak:
                    student_info += f"Needs work: {', '.join(m['topic'] + '(' + str(int(m['score'])) + '%)' for m in weak[:5])}.\n"

            # Inject streak and recent activity
            stats = self.db.get_stats(student_id)
            if stats and stats.get('streak_days', 0) > 0:
                student_info += f"STREAK: {stats['streak_days']} days in a row!\n"
            elif stats:
                student_info += "STREAK: Broken. They haven't studied recently.\n"

            # Recent interactions for context
            recent = self.db.get_recent_interactions(student_id, limit=3)
            if recent:
                activities = [f"{r['agent']}({r['topic']}): {r['result']}" for r in recent if r.get('agent')]
                student_info += f"Recent: {', '.join(activities)}.\n"

        backend_info = f"LLM backend: {self._backend} ({self.model})."
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
