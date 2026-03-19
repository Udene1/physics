"""
agents/companion.py — Daily Companion Agent.

Friendly, motivational greeter that reviews progress and sets micro-goals.
Uses Nigerian-flavored encouragement when appropriate.
"""

import random
from datetime import datetime
from .base import BaseAgent

GREETINGS = [
    "Good {time_of_day}! 🌟 Welcome back, my friend! Ready to build something amazing today?",
    "Hey hey! 🔥 Another day, another chance to level up. Let's get it!",
    "Omo, welcome back! 💪 The world needs what you're building. Let's learn!",
    "Good {time_of_day}! 🚀 You showed up — that's half the battle. Now let's conquer!",
    "Na today we go make am! 🌅 Your consistency is inspiring. What shall we tackle?",
    "My person! 😊 Every concept you master brings you closer to changing lives. Ready?",
    "Rise and shine! ☀️ Remember — every sensor, every device starts with understanding. Let's go!",
    "Welcome! 🎯 Small steps, big impact. That's the formula. What's on your mind today?",
]

ENCOURAGEMENTS = [
    "You dey learn, you dey grow — no pressure, just progress! 💯",
    "Remember: the farmer in Benin who'll use your sensor — they're counting on you! 🌱",
    "Every formula you master is a tool in your builder's toolkit! 🔧",
    "Understanding more = building more = helping more lives. Keep going! ❤️",
    "When e hard, remember: the best engineers struggled too. You're not alone! 🤝",
    "Take am one step at a time. Even the longest journey... you know how e dey go! 🚶",
    "Your brain is literally rewiring right now. That 'hard' feeling? That's growth! 🧠",
]

FRUSTRATION_RESPONSES = [
    "Hey, it's okay! 🫂 This stuff is genuinely hard. Take a 5-minute break — stretch, drink water.",
    "You know what? Let's try a different angle. Sometimes a fresh perspective changes everything.",
    "I hear you. When it feels impossible, that's when breakthroughs are closest. Breathe. 🌬️",
    "Even Feynman got stuck sometimes! Take a break, come back fresh. The problem will wait for you.",
    "Let's step back. What part DO you understand? We build from there. 🧱",
]

SYSTEM_PROMPT = """You are the Daily Companion Agent — a warm, encouraging study buddy for a learner
in Benin City, Nigeria who is self-teaching advanced math and physics to build real-world
hardware devices that improve lives (sensors, agricultural tools, health devices).

Your role:
1. GREET the user warmly each session with motivational energy.
2. REVIEW yesterday's progress (you'll receive a summary in context).
3. SET 2-3 achievable micro-goals based on their current level and areas needing attention.
4. ENCOURAGE constantly — tie their learning to their vision of building hardware to help people.
5. DETECT frustration and respond with empathy, suggest breaks, offer simpler approaches.
6. Use Nigerian-flavored English naturally when it fits (pidgin phrases, local references).

You are NOT a tutor — delegate math/physics questions to the appropriate agents.
When the user asks a technical question, say something like:
"Great question! Let me pass you to the Math Tutor / Physics Supervisor for that one."

Keep responses concise (3-6 sentences usually) unless the user asks for more detail.
Always end with an actionable suggestion or question to keep momentum going.
"""


class CompanionAgent(BaseAgent):
    """Daily Companion — motivation, progress review, micro-goal setting."""

    def __init__(self, db=None, model: str = None):
        super().__init__(
            name="Companion",
            system_prompt=SYSTEM_PROMPT,
            db=db,
            model=model,
        )

    def greet(self) -> str:
        """Generate a daily greeting with progress summary."""
        hour = datetime.now().hour
        if hour < 12:
            time_of_day = "morning"
        elif hour < 17:
            time_of_day = "afternoon"
        else:
            time_of_day = "evening"

        greeting = random.choice(GREETINGS).format(time_of_day=time_of_day)

        # Build progress context
        context_parts = [greeting, ""]

        if self.db:
            summary = self.db.generate_summary()

            # Yesterday's recap
            recent = self.db.get_recent_interactions(limit=5)
            if recent:
                context_parts.append("📊 **Recent Activity:**")
                topics_seen = set()
                for interaction in recent[:3]:
                    if interaction.get("topic") and interaction["topic"] not in topics_seen:
                        context_parts.append(f"  • Worked on: {interaction['topic']} ({interaction['agent']})")
                        topics_seen.add(interaction["topic"])

            # Mastery snapshot
            mastery = summary.get("mastery", [])
            if mastery:
                context_parts.append("\n🎯 **Mastery Snapshot:**")
                for m in mastery[:5]:
                    bar = "█" * int(m["score"] / 10) + "░" * (10 - int(m["score"] / 10))
                    context_parts.append(f"  • {m['topic']}: [{bar}] {m['score']}%")

            # Pending goals
            goals = summary.get("goals", [])
            if goals:
                context_parts.append("\n📋 **Pending Goals:**")
                for g in goals[:3]:
                    context_parts.append(f"  • {g['description']}")
            else:
                context_parts.append("\n💡 No goals set yet — let's fix that! What would you like to focus on?")

            context_parts.append(f"\n📈 Total sessions logged: {summary['total_interactions']}")
        else:
            context_parts.append("📌 *No progress data yet — this is your fresh start!*")

        context_parts.append(f"\n{random.choice(ENCOURAGEMENTS)}")
        return "\n".join(context_parts)

    def handle_frustration(self) -> str:
        """Return a frustration-handling response."""
        return random.choice(FRUSTRATION_RESPONSES)

    def set_micro_goals(self, mastery_data: list[dict]) -> str:
        """Generate micro-goals based on mastery gaps."""
        if not mastery_data:
            return (
                "🎯 **Today's Goals:**\n"
                "  1. Complete 5 algebra warm-up problems\n"
                "  2. Read about one physics concept (Newton's laws are a great start!)\n"
                "  3. Think about one real-world device you'd love to build\n\n"
                "Start small, dream big! 💪"
            )

        # Find weakest topics
        weak_topics = sorted(mastery_data, key=lambda m: m["score"])[:3]
        goals = ["🎯 **Today's Micro-Goals:**"]
        for i, topic in enumerate(weak_topics, 1):
            if topic["score"] < 30:
                goals.append(f"  {i}. 📚 Review basics of {topic['topic']} (score: {topic['score']}%)")
            elif topic["score"] < 60:
                goals.append(f"  {i}. 💪 Practice 5 {topic['topic']} problems to strengthen understanding")
            else:
                goals.append(f"  {i}. 🚀 Try advanced {topic['topic']} problems — you're almost there!")

        goals.append(f"\n{random.choice(ENCOURAGEMENTS)}")
        return "\n".join(goals)
