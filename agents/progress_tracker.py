"""
agents/progress_tracker.py — Progress Tracker & Memory Agent.

Maintains persistent state, logs interactions, generates reports,
and prevents topic repetition unless requested.
"""

from datetime import datetime, date
from .base import BaseAgent


SYSTEM_PROMPT = """You are the Progress Tracker & Memory Agent — the record-keeper and analyst
for a self-learner's journey through math, physics, and hardware engineering.

YOUR ROLE:
1. MAINTAIN accurate records of all learning activities.
2. GENERATE insightful weekly/session reports showing growth and gaps.
3. PREVENT unnecessary repetition — if a topic is mastered, suggest new challenges.
4. IDENTIFY patterns — repeated mistakes, strong areas, learning velocity.
5. PROVIDE data-driven recommendations to other agents.

When generating reports, use visual progress bars and clear metrics.
Always be encouraging about growth while honest about gaps.
"""


class ProgressTrackerAgent(BaseAgent):
    """Progress Tracker — logging, reporting, analysis."""

    def __init__(self, db=None, model: str = None):
        super().__init__(name="ProgressTracker", system_prompt=SYSTEM_PROMPT, db=db, model=model)

    def chat(self, user_msg: str, context: str = "") -> str:
        msg_lower = user_msg.lower().strip()
        if msg_lower in ("/report", "/progress", "show progress", "report"):
            return self.generate_report()
        if msg_lower in ("/weekly", "weekly report"):
            return self.weekly_report()
        report_ctx = self._build_report_context()
        full_ctx = f"{context}\n\n{report_ctx}" if context else report_ctx
        return super().chat(user_msg, full_ctx)

    def generate_report(self) -> str:
        """Generate a formatted progress report."""
        if not self.db:
            return "No database connected — cannot generate report."

        summary = self.db.generate_summary()
        lines = [
            "# 📊 Progress Report",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
            f"**Total Interactions:** {summary['total_interactions']}",
            f"**Today's Sessions:** {summary['today_interactions']}",
            f"**Projects Completed:** {summary['projects_completed']}",
            f"**Projects In Progress:** {summary['projects_in_progress']}",
            f"**Pending Goals:** {summary['pending_goals']}\n",
        ]

        # Mastery breakdown
        mastery = summary.get("mastery", [])
        if mastery:
            lines.append("## 🎯 Mastery Levels\n")
            for m in mastery:
                score = m["score"]
                bar = "█" * int(score / 10) + "░" * (10 - int(score / 10))
                attempted = m.get("problems_attempted", 0)
                correct = m.get("problems_correct", 0)
                lines.append(
                    f"  **{m['topic']}** [{bar}] {score}%  "
                    f"({correct}/{attempted} correct)"
                )
        else:
            lines.append("\n*No mastery data yet — start learning to see progress!*")

        # Pending goals
        goals = summary.get("goals", [])
        if goals:
            lines.append("\n## 📋 Pending Goals\n")
            for g in goals:
                lines.append(f"  • {g['description']}")

        lines.append("\n---\n*Keep going! Every problem solved is progress.* 💪")
        return "\n".join(lines)

    def weekly_report(self) -> str:
        """Generate a weekly summary report."""
        if not self.db:
            return "No database connected."

        # Get this week's interactions
        interactions = self.db.get_recent_interactions(limit=100)
        mastery = self.db.get_all_mastery()

        topics_covered = set()
        agents_used = {}
        for interaction in interactions:
            if interaction.get("topic"):
                topics_covered.add(interaction["topic"])
            agent = interaction.get("agent", "unknown")
            agents_used[agent] = agents_used.get(agent, 0) + 1

        lines = [
            "# 📅 Weekly Summary Report",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
            f"**Interactions this period:** {len(interactions)}",
            f"**Topics covered:** {len(topics_covered)}",
        ]

        if agents_used:
            lines.append("\n## Agent Usage")
            for agent, count in sorted(agents_used.items(), key=lambda x: -x[1]):
                lines.append(f"  • {agent}: {count} interactions")

        if topics_covered:
            lines.append(f"\n## Topics Studied\n  {', '.join(sorted(topics_covered))}")

        # Improvement areas
        weak = [m for m in mastery if m["score"] < 50] if mastery else []
        if weak:
            lines.append("\n## ⚠️ Areas Needing Attention")
            for m in weak[:5]:
                lines.append(f"  • {m['topic']}: {m['score']}%")

        strong = [m for m in mastery if m["score"] >= 70] if mastery else []
        if strong:
            lines.append("\n## 🌟 Strong Areas")
            for m in strong[:5]:
                lines.append(f"  • {m['topic']}: {m['score']}%")

        return "\n".join(lines)

    def generate_session_artifact(self, session_dir: str = "memory") -> str:
        """Generate a session summary markdown artifact file."""
        import os
        report = self.generate_report()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"session_{timestamp}.md"
        filepath = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), session_dir, filename
        )
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Session Artifact — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
            f.write(report)
            # Add next steps
            if self.db:
                goals = self.db.get_pending_goals()
                if goals:
                    f.write("\n\n## 🎯 Next Steps\n")
                    for g in goals[:5]:
                        f.write(f"  • {g['description']}\n")
        return filepath

    def _build_report_context(self) -> str:
        if not self.db:
            return ""
        summary = self.db.generate_summary()
        return (
            f"Total interactions: {summary['total_interactions']}, "
            f"Today: {summary['today_interactions']}, "
            f"Topics tracked: {len(summary['mastery'])}"
        )
