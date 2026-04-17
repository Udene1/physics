"""
agents/progress_tracker.py — Progress Tracker & Memory Agent.

Maintains persistent state, logs interactions, generates reports,
and prevents topic repetition unless requested.
Supports multi-student state.
"""

from datetime import datetime
from .base import BaseAgent


SYSTEM_PROMPT = """You are the Progress Tracker & Memory Agent — the record-keeper and analyst
for a self-learner's journey through math, physics, and hardware engineering.

YOUR ROLE:
1. MAINTAIN accurate records of all learning activities.
2. GENERATE insightful weekly/session reports showing growth and gaps.
3. PREVENT unnecessary repetition.
4. IDENTIFY patterns — repeated mistakes, strong areas, learning velocity.
5. PROVIDE data-driven recommendations to other agents.
"""


class ProgressTrackerAgent(BaseAgent):
    """Progress Tracker — logging, reporting, analysis."""

    def __init__(self, **kwargs):
        super().__init__(
            name="ProgressTracker",
            system_prompt=SYSTEM_PROMPT,
            **kwargs
        )

    def chat(self, user_msg: str, context: str = "", student_id: int = 1, image=None) -> str:
        msg_lower = user_msg.lower().strip()
        if msg_lower in ("/report", "/progress", "show progress", "report"):
            return self.generate_report(student_id)
        if msg_lower in ("/weekly", "weekly report"):
            return self.weekly_report(student_id)
            
        report_ctx = self._build_report_context(student_id)
        full_ctx = f"{context}\n\n{report_ctx}" if context else report_ctx
        return super().chat(user_msg, full_ctx, student_id=student_id, image=image)

    def generate_report(self, student_id: int) -> str:
        """Generate a formatted progress report for a student."""
        if not self.db: return "No database."

        # Check for new badges before generating report
        self.auto_check_badges(student_id)

        summary = self.db.generate_summary(student_id)
        lines = [
            f"# 📊 Progress Report for {self.db.get_student(student_id)['nickname']}",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
            f"🔥 **Current Streak: {summary['streak']} days**",
            f"**Total Interactions:** {summary['total_interactions']}",
            f"**Projects Completed:** {summary['projects_completed']}\n",
        ]

        # Badges
        badges = summary.get("badges", [])
        if badges:
            lines.append("## 🏅 Badges Unlocked")
            lines.append("  " + " ".join([f"✨ **{b}**" for b in badges]) + "\n")

        # Mastery breakdown
        mastery = summary.get("mastery", [])
        if mastery:
            lines.append("## 🎯 Mastery Levels\n")
            for m in mastery:
                score = m["score"]
                bar = "█" * int(score / 10) + "░" * (10 - int(score / 10))
                lines.append(f"  **{m['topic']}** [{bar}] {score}%")
        else:
            lines.append("\n*No mastery data yet — start learning!*")

        return "\n".join(lines)

    def auto_check_badges(self, student_id: int) -> list[str]:
        """Check and award badges based on milestones. Returns list of newly awarded badges."""
        if not self.db: return []
        
        summary = self.db.generate_summary(student_id)
        mastery = summary.get("mastery", [])
        new_badges = []
        
        # 1. Beginner Builder: 1 completed build
        if summary["projects_completed"] >= 1:
            if self.db.add_badge(student_id, "Beginner Builder"):
                new_badges.append("Beginner Builder")
        
        # 2. Hardware Hero: 5 completed builds
        if summary["projects_completed"] >= 5:
            if self.db.add_badge(student_id, "Hardware Hero"):
                new_badges.append("Hardware Hero")
                
        # 3. SymPy Ninja: 3 math topics with 80%+ mastery
        math_score_80 = [m for m in mastery if m["category"] == "math" and m["score"] >= 80]
        if len(math_score_80) >= 3:
            if self.db.add_badge(student_id, "SymPy Ninja"):
                new_badges.append("SymPy Ninja")
                
        # 4. Circuit Master: Electricity/Circuits at 70%+
        circuits = [m for m in mastery if "circuit" in m["topic"].lower() and m["score"] >= 70]
        if circuits:
            if self.db.add_badge(student_id, "Circuit Master"):
                new_badges.append("Circuit Master")
                
        # 5. Consistency King: 7-day streak
        if summary["streak"] >= 7:
            if self.db.add_badge(student_id, "Consistency King"):
                new_badges.append("Consistency King")
                
        return new_badges

    def weekly_report(self, student_id: int) -> str:
        """Generate a weekly summary report for a student."""
        if not self.db: return "No database."

        interactions = self.db.get_recent_interactions(student_id, limit=100)
        lines = [
            f"# 📅 Weekly Summary for {self.db.get_student(student_id)['nickname']}",
            f"Interactions this period: {len(interactions)}",
        ]
        return "\n".join(lines)

    def _build_report_context(self, student_id: int) -> str:
        if not self.db: return ""
        summary = self.db.generate_summary(student_id)
        return f"Student Streak: {summary['streak']} days, Sessions: {summary['total_interactions']}"
