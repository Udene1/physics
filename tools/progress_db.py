"""
tools/progress_db.py — SQLite-backed progress and memory storage.

Tracks mastery levels, interaction history, hardware projects, and goals.
"""

import sqlite3
import json
import os
from datetime import datetime, date
from typing import Optional


DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "memory")
DEFAULT_DB_PATH = os.path.join(DB_DIR, "progress.db")


class ProgressDB:
    """Lightweight SQLite wrapper for all persistent learning state."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        os.makedirs(os.path.dirname(db_path) if db_path != ":memory:" else ".", exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    # ── Schema ──────────────────────────────────────────────────────

    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS mastery (
                topic       TEXT PRIMARY KEY,
                category    TEXT NOT NULL DEFAULT 'general',
                score       REAL NOT NULL DEFAULT 0.0,
                problems_attempted INTEGER NOT NULL DEFAULT 0,
                problems_correct   INTEGER NOT NULL DEFAULT 0,
                last_updated TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS interactions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp   TEXT NOT NULL,
                agent       TEXT NOT NULL,
                topic       TEXT,
                user_input  TEXT,
                agent_response TEXT,
                result      TEXT
            );

            CREATE TABLE IF NOT EXISTS projects (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                name            TEXT NOT NULL,
                description     TEXT,
                status          TEXT NOT NULL DEFAULT 'suggested',
                related_topics  TEXT,
                components      TEXT,
                created_at      TEXT NOT NULL,
                completed_at    TEXT
            );

            CREATE TABLE IF NOT EXISTS goals (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT NOT NULL,
                status      TEXT NOT NULL DEFAULT 'pending',
                agent       TEXT,
                created_at  TEXT NOT NULL,
                due_date    TEXT,
                completed_at TEXT
            );

            CREATE TABLE IF NOT EXISTS session_meta (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)
        self.conn.commit()

    # ── Mastery ─────────────────────────────────────────────────────

    def get_mastery(self, topic: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM mastery WHERE topic = ?", (topic,)
        ).fetchone()
        return dict(row) if row else None

    def get_all_mastery(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM mastery ORDER BY category, topic"
        ).fetchall()
        return [dict(r) for r in rows]

    def update_mastery(self, topic: str, category: str, correct: bool):
        """Increment attempt count and adjust score based on correctness."""
        now = datetime.now().isoformat()
        existing = self.get_mastery(topic)
        if existing:
            attempted = existing["problems_attempted"] + 1
            correct_count = existing["problems_correct"] + (1 if correct else 0)
            score = round((correct_count / attempted) * 100, 1)
            self.conn.execute(
                """UPDATE mastery
                   SET score = ?, problems_attempted = ?, problems_correct = ?,
                       last_updated = ?
                   WHERE topic = ?""",
                (score, attempted, correct_count, now, topic),
            )
        else:
            self.conn.execute(
                """INSERT INTO mastery
                   (topic, category, score, problems_attempted, problems_correct, last_updated)
                   VALUES (?, ?, ?, 1, ?, ?)""",
                (topic, category, 100.0 if correct else 0.0, 1 if correct else 0, now),
            )
        self.conn.commit()

    def set_mastery_score(self, topic: str, category: str, score: float):
        """Directly set a mastery score (used for supervisor overrides)."""
        now = datetime.now().isoformat()
        self.conn.execute(
            """INSERT INTO mastery (topic, category, score, last_updated)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(topic) DO UPDATE SET score = ?, last_updated = ?""",
            (topic, category, score, now, score, now),
        )
        self.conn.commit()

    # ── Interactions ────────────────────────────────────────────────

    def log_interaction(self, agent: str, topic: str, user_input: str,
                        agent_response: str = "", result: str = ""):
        now = datetime.now().isoformat()
        self.conn.execute(
            """INSERT INTO interactions
               (timestamp, agent, topic, user_input, agent_response, result)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (now, agent, topic, user_input, agent_response, result),
        )
        self.conn.commit()

    def get_recent_interactions(self, limit: int = 20, agent: str = None) -> list[dict]:
        if agent:
            rows = self.conn.execute(
                "SELECT * FROM interactions WHERE agent = ? ORDER BY id DESC LIMIT ?",
                (agent, limit),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM interactions ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(r) for r in rows]

    def get_today_interactions(self) -> list[dict]:
        today = date.today().isoformat()
        rows = self.conn.execute(
            "SELECT * FROM interactions WHERE timestamp LIKE ? ORDER BY id",
            (f"{today}%",),
        ).fetchall()
        return [dict(r) for r in rows]

    # ── Projects ────────────────────────────────────────────────────

    def add_project(self, name: str, description: str, related_topics: list[str],
                    components: list[str] = None) -> int:
        now = datetime.now().isoformat()
        cur = self.conn.execute(
            """INSERT INTO projects (name, description, status, related_topics,
               components, created_at)
               VALUES (?, ?, 'suggested', ?, ?, ?)""",
            (name, description, json.dumps(related_topics),
             json.dumps(components or []), now),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_projects(self, status: str = None) -> list[dict]:
        if status:
            rows = self.conn.execute(
                "SELECT * FROM projects WHERE status = ? ORDER BY id DESC",
                (status,),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM projects ORDER BY id DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def update_project_status(self, project_id: int, status: str):
        now = datetime.now().isoformat()
        completed = now if status == "completed" else None
        self.conn.execute(
            "UPDATE projects SET status = ?, completed_at = ? WHERE id = ?",
            (status, completed, project_id),
        )
        self.conn.commit()

    # ── Goals ───────────────────────────────────────────────────────

    def add_goal(self, description: str, agent: str = "", due_date: str = "") -> int:
        now = datetime.now().isoformat()
        cur = self.conn.execute(
            """INSERT INTO goals (description, status, agent, created_at, due_date)
               VALUES (?, 'pending', ?, ?, ?)""",
            (description, agent, now, due_date),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_pending_goals(self) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM goals WHERE status = 'pending' ORDER BY id"
        ).fetchall()
        return [dict(r) for r in rows]

    def complete_goal(self, goal_id: int):
        now = datetime.now().isoformat()
        self.conn.execute(
            "UPDATE goals SET status = 'completed', completed_at = ? WHERE id = ?",
            (now, goal_id),
        )
        self.conn.commit()

    # ── Session Meta ────────────────────────────────────────────────

    def get_meta(self, key: str, default: str = "") -> str:
        row = self.conn.execute(
            "SELECT value FROM session_meta WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else default

    def set_meta(self, key: str, value: str):
        self.conn.execute(
            """INSERT INTO session_meta (key, value) VALUES (?, ?)
               ON CONFLICT(key) DO UPDATE SET value = ?""",
            (key, value, value),
        )
        self.conn.commit()

    # ── Reports ─────────────────────────────────────────────────────

    def generate_summary(self) -> dict:
        """Generate a snapshot summary of all progress."""
        mastery = self.get_all_mastery()
        total_interactions = self.conn.execute(
            "SELECT COUNT(*) as c FROM interactions"
        ).fetchone()["c"]
        today_count = len(self.get_today_interactions())
        projects = self.get_projects()
        pending_goals = self.get_pending_goals()

        return {
            "mastery": mastery,
            "total_interactions": total_interactions,
            "today_interactions": today_count,
            "projects_completed": len([p for p in projects if p["status"] == "completed"]),
            "projects_in_progress": len([p for p in projects if p["status"] != "completed"]),
            "pending_goals": len(pending_goals),
            "goals": pending_goals,
        }

    def close(self):
        self.conn.close()
