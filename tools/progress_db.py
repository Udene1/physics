"""
tools/progress_db.py — SQLite-backed progress and memory storage.

Tracks students, mastery levels, interaction history, hardware projects, and goals.
Supports multiple students on a single device.
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
        db_dir = os.path.dirname(db_path)
        if db_dir and db_path != ":memory:":
            os.makedirs(db_dir, exist_ok=True)
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()
        self._migrate_if_needed()
        self.preload_topics()

    # ── Schema ──────────────────────────────────────────────────────

    def _create_tables(self):
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS students (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                nickname    TEXT UNIQUE NOT NULL,
                pin         TEXT, -- Simple 4-digit PIN (stored as plain text for offline ease)
                created_at  TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS mastery (
                student_id  INTEGER NOT NULL,
                topic       TEXT NOT NULL,
                category    TEXT NOT NULL DEFAULT 'general',
                score       REAL NOT NULL DEFAULT 0.0,
                problems_attempted INTEGER NOT NULL DEFAULT 0,
                problems_correct   INTEGER NOT NULL DEFAULT 0,
                last_updated TEXT NOT NULL,
                PRIMARY KEY (student_id, topic),
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS interactions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id  INTEGER NOT NULL,
                timestamp   TEXT NOT NULL,
                agent       TEXT NOT NULL,
                topic       TEXT,
                user_input  TEXT,
                agent_response TEXT,
                result      TEXT,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS projects (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id      INTEGER NOT NULL,
                name            TEXT NOT NULL,
                description     TEXT,
                status          TEXT NOT NULL DEFAULT 'suggested',
                related_topics  TEXT,
                components      TEXT,
                created_at      TEXT NOT NULL,
                completed_at    TEXT,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS goals (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id  INTEGER NOT NULL,
                description TEXT NOT NULL,
                status      TEXT NOT NULL DEFAULT 'pending',
                agent       TEXT,
                created_at  TEXT NOT NULL,
                due_date    TEXT,
                completed_at TEXT,
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS gamification (
                student_id      INTEGER PRIMARY KEY,
                streak_days     INTEGER NOT NULL DEFAULT 0,
                last_active_date TEXT,
                badges_json     TEXT NOT NULL DEFAULT '[]',
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS topics (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                name            TEXT UNIQUE NOT NULL,
                category        TEXT NOT NULL,
                difficulty      INTEGER NOT NULL DEFAULT 1,
                prerequisites   TEXT NOT NULL DEFAULT '[]', -- JSON list of topic names
                build_hint      TEXT,
                description     TEXT
            );

            CREATE TABLE IF NOT EXISTS session_meta (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            INSERT OR IGNORE INTO session_meta (key, value) VALUES ('schema_version', '1.1');

            CREATE TABLE IF NOT EXISTS agent_states (
                student_id INTEGER NOT NULL,
                agent_name TEXT NOT NULL,
                state_json TEXT NOT NULL,
                PRIMARY KEY (student_id, agent_name),
                FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
            );

            -- Distilled Knowledge Table (for local retrieval without LLM)
            CREATE TABLE IF NOT EXISTS distilled_knowledge (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT UNIQUE,
                category TEXT,
                content TEXT,
                source_llm TEXT,
                verified INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- Learning Signals Table (for future training/analytics)
            CREATE TABLE IF NOT EXISTS learning_signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER,
                topic TEXT,
                signal_type TEXT, -- 'speed', 'mistake_count', 'hint_usage'
                value REAL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE
            );
        """)

        self.conn.commit()

    def _migrate_if_needed(self):
        """Handle migrations for old single-user databases."""
        # 1. Check if students table is empty or just created
        res = self.conn.execute("SELECT COUNT(*) as c FROM students").fetchone()
        if res["c"] == 0:
            # Create default student
            now = datetime.now().isoformat()
            self.conn.execute(
                "INSERT INTO students (nickname, created_at) VALUES (?, ?)",
                ("Guest", now)
            )
            student_id = 1
            
            # 2. Check if old tables have student_id column
            cursor = self.conn.execute("PRAGMA table_info(interactions)")
            cols = [row[1] for row in cursor.fetchall()]
            
            if "student_id" not in cols:
                print("[DB] Migrating database to multi-user schema...")
                
                # INTERACTIONS
                self.conn.execute("ALTER TABLE interactions ADD COLUMN student_id INTEGER")
                self.conn.execute("UPDATE interactions SET student_id = ?", (student_id,))
                
                # PROJECTS
                self.conn.execute("ALTER TABLE projects ADD COLUMN student_id INTEGER")
                self.conn.execute("UPDATE projects SET student_id = ?", (student_id,))
                
                # GOALS
                self.conn.execute("ALTER TABLE goals ADD COLUMN student_id INTEGER")
                self.conn.execute("UPDATE goals SET student_id = ?", (student_id,))
                
                # MASTERY (Needs careful PK change)
                self.conn.execute("ALTER TABLE mastery RENAME TO mastery_old")
                self.conn.execute("""
                    CREATE TABLE mastery (
                        student_id  INTEGER NOT NULL,
                        topic       TEXT NOT NULL,
                        category    TEXT NOT NULL DEFAULT 'general',
                        score       REAL NOT NULL DEFAULT 0.0,
                        problems_attempted INTEGER NOT NULL DEFAULT 0,
                        problems_correct   INTEGER NOT NULL DEFAULT 0,
                        last_updated TEXT NOT NULL,
                        PRIMARY KEY (student_id, topic),
                        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
                    )
                """)
                self.conn.execute("""
                    INSERT INTO mastery (student_id, topic, category, score, problems_attempted, problems_correct, last_updated)
                    SELECT ?, topic, category, score, problems_attempted, problems_correct, last_updated FROM mastery_old
                """, (student_id,))
                self.conn.execute("DROP TABLE mastery_old")

        # 3. Ensure topics table has new columns
        cursor = self.conn.execute("PRAGMA table_info(topics)")
        topic_cols = [row[1] for row in cursor.fetchall()]
        if "build_hint" not in topic_cols:
            self.conn.execute("ALTER TABLE topics ADD COLUMN build_hint TEXT")
        if "description" not in topic_cols:
            self.conn.execute("ALTER TABLE topics ADD COLUMN description TEXT")
        
        # 4. Add verified column to distilled_knowledge if missing
        cursor = self.conn.execute("PRAGMA table_info(distilled_knowledge)")
        distills_cols = [row[1] for row in cursor.fetchall()]
        if distills_cols and "verified" not in distills_cols:
            self.conn.execute("ALTER TABLE distilled_knowledge ADD COLUMN verified INTEGER DEFAULT 0")

        self.conn.commit()
        # print("[DB] Migration check complete.")

    # ── Students ────────────────────────────────────────────────────

    def add_student(self, nickname: str, pin: str = None) -> int:
        now = datetime.now().isoformat()
        try:
            cur = self.conn.execute(
                "INSERT INTO students (nickname, pin, created_at) VALUES (?, ?, ?)",
                (nickname, pin, now)
            )
            self.conn.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError:
            return -1 # Nickname taken

    def get_student(self, student_id: int) -> Optional[dict]:
        row = self.conn.execute("SELECT * FROM students WHERE id = ?", (student_id,)).fetchone()
        return dict(row) if row else None

    def get_all_students(self) -> list[dict]:
        rows = self.conn.execute("SELECT * FROM students ORDER BY nickname").fetchall()
        return [dict(r) for r in rows]

    def verify_student(self, nickname: str, pin: str = None) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM students WHERE LOWER(nickname) = LOWER(?)", (nickname.strip(),)
        ).fetchone()
        if row:
            if not row["pin"] or row["pin"] == pin:
                return dict(row)
        return None

    # ── Mastery ─────────────────────────────────────────────────────

    def get_mastery(self, student_id: int, topic: str) -> Optional[dict]:
        row = self.conn.execute(
            "SELECT * FROM mastery WHERE student_id = ? AND topic = ?", (student_id, topic)
        ).fetchone()
        return dict(row) if row else None

    def get_all_mastery(self, student_id: int) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM mastery WHERE student_id = ? ORDER BY category, topic", (student_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def update_mastery(self, student_id: int, topic: str, category: str, correct: bool):
        now = datetime.now().isoformat()
        existing = self.get_mastery(student_id, topic)
        if existing:
            attempted = existing["problems_attempted"] + 1
            correct_count = existing["problems_correct"] + (1 if correct else 0)
            score = round((correct_count / attempted) * 100, 1)
            self.conn.execute(
                """UPDATE mastery
                   SET score = ?, problems_attempted = ?, problems_correct = ?,
                       last_updated = ?
                   WHERE student_id = ? AND topic = ?""",
                (score, attempted, correct_count, now, student_id, topic),
            )
        else:
            self.conn.execute(
                """INSERT INTO mastery
                   (student_id, topic, category, score, problems_attempted, problems_correct, last_updated)
                   VALUES (?, ?, ?, ?, 1, ?, ?)""",
                (student_id, topic, category, 100.0 if correct else 0.0, 1 if correct else 0, now),
            )
        self.conn.commit()

    def set_mastery_score(self, student_id: int, topic: str, category: str, score: float):
        now = datetime.now().isoformat()
        self.conn.execute(
            """INSERT INTO mastery (student_id, topic, category, score, last_updated)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(student_id, topic) DO UPDATE SET score = ?, last_updated = ?""",
            (student_id, topic, category, score, now, score, now),
        )
        self.conn.commit()

    # ── Interactions ────────────────────────────────────────────────

    def log_interaction(self, student_id: int, agent: str, topic: str, user_input: str,
                        agent_response: str = "", result: str = ""):
        now = datetime.now().isoformat()
        self.conn.execute(
            """INSERT INTO interactions
               (student_id, timestamp, agent, topic, user_input, agent_response, result)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (student_id, now, agent, topic, user_input, agent_response, result),
        )
        self.conn.commit()

    def get_recent_interactions(self, student_id: int, limit: int = 20, agent: str = None, topic: str = None) -> list[dict]:
        if agent:
            if topic:
                rows = self.conn.execute(
                    "SELECT * FROM interactions WHERE student_id = ? AND agent = ? AND topic = ? ORDER BY id DESC LIMIT ?",
                    (student_id, agent, topic, limit),
                ).fetchall()
            else:
                rows = self.conn.execute(
                    "SELECT * FROM interactions WHERE student_id = ? AND agent = ? ORDER BY id DESC LIMIT ?",
                    (student_id, agent, limit),
                ).fetchall()
        elif topic:
            rows = self.conn.execute(
                "SELECT * FROM interactions WHERE student_id = ? AND topic = ? ORDER BY id DESC LIMIT ?",
                (student_id, topic, limit),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM interactions WHERE student_id = ? ORDER BY id DESC LIMIT ?", (student_id, limit)
            ).fetchall()
        return [dict(r) for r in rows]

    def get_today_interactions(self, student_id: int) -> list[dict]:
        today = date.today().isoformat()
        rows = self.conn.execute(
            "SELECT * FROM interactions WHERE student_id = ? AND timestamp LIKE ? ORDER BY id",
            (student_id, f"{today}%"),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_shared_context(self, student_id: int, limit: int = 5) -> str:
        """
        Fetch a summary of recent interactions across all agents for context.
        Used for inter-agent 'memory'.
        """
        rows = self.conn.execute(
            """SELECT agent, topic, user_input, agent_response, timestamp 
               FROM interactions 
               WHERE student_id = ? 
               ORDER BY id DESC LIMIT ?""",
            (student_id, limit)
        ).fetchall()
        
        if not rows:
            return ""

        context_lines = ["\n--- SHARED SESSION MEMORY (RECAP) ---"]
        # Reverse to show chronological order for the last few
        for row in reversed(rows):
            context_lines.append(
                f"[{row['timestamp']}] Agent {row['agent']} assisted with {row['topic']}."
            )
            context_lines.append(f"Student asked: {row['user_input']}")
            context_lines.append(f"Agent responded: {row['agent_response'][:200]}...")
            context_lines.append("")
        return "\n".join(context_lines)

    # ── Projects ────────────────────────────────────────────────────

    def add_project(self, student_id: int, name: str, description: str, related_topics: list[str],
                    components: list[str] = None) -> int:
        now = datetime.now().isoformat()
        cur = self.conn.execute(
            """INSERT INTO projects (student_id, name, description, status, related_topics,
               components, created_at)
               VALUES (?, ?, ?, 'suggested', ?, ?, ?)""",
            (student_id, name, description, json.dumps(related_topics),
             json.dumps(components or []), now),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_projects(self, student_id: int, status: str = None) -> list[dict]:
        if status:
            rows = self.conn.execute(
                "SELECT * FROM projects WHERE student_id = ? AND status = ? ORDER BY id DESC",
                (student_id, status),
            ).fetchall()
        else:
            rows = self.conn.execute(
                "SELECT * FROM projects WHERE student_id = ? ORDER BY id DESC", (student_id,)
            ).fetchall()
        return [dict(r) for r in rows]

    def update_project_status(self, student_id: int, project_id: int, status: str):
        now = datetime.now().isoformat()
        completed = now if status == "completed" else None
        self.conn.execute(
            "UPDATE projects SET status = ?, completed_at = ? WHERE student_id = ? AND id = ?",
            (status, completed, student_id, project_id),
        )
        self.conn.commit()

    # ── Goals ───────────────────────────────────────────────────────

    def add_goal(self, student_id: int, description: str, agent: str = "", due_date: str = "") -> int:
        now = datetime.now().isoformat()
        cur = self.conn.execute(
            """INSERT INTO goals (student_id, description, status, agent, created_at, due_date)
               VALUES (?, ?, 'pending', ?, ?, ?)""",
            (student_id, description, agent, now, due_date),
        )
        self.conn.commit()
        return cur.lastrowid

    def get_pending_goals(self, student_id: int) -> list[dict]:
        rows = self.conn.execute(
            "SELECT * FROM goals WHERE student_id = ? AND status = 'pending' ORDER BY id", (student_id,)
        ).fetchall()
        return [dict(r) for r in rows]

    def complete_goal(self, student_id: int, goal_id: int):
        now = datetime.now().isoformat()
        self.conn.execute(
            "UPDATE goals SET status = 'completed', completed_at = ? WHERE student_id = ? AND id = ?",
            (now, student_id, goal_id),
        )
        self.conn.commit()

    # ── Gamification ────────────────────────────────────────────────

    def update_streak(self, student_id: int):
        """Update student streak based on daily activity."""
        today = date.today().isoformat()
        row = self.conn.execute(
            "SELECT streak_days, last_active_date FROM gamification WHERE student_id = ?",
            (student_id,)
        ).fetchone()

        if not row:
            self.conn.execute(
                "INSERT INTO gamification (student_id, streak_days, last_active_date) VALUES (?, 1, ?)",
                (student_id, today)
            )
        else:
            last_date = row["last_active_date"]
            if last_date == today:
                return # Already active today
            
            # Check if yesterday
            from datetime import timedelta
            yesterday = (date.today() - timedelta(days=1)).isoformat()
            
            if last_date == yesterday:
                new_streak = row["streak_days"] + 1
            else:
                new_streak = 1 # Reset if miss a day
            
            self.conn.execute(
                "UPDATE gamification SET streak_days = ?, last_active_date = ? WHERE student_id = ?",
                (new_streak, today, student_id)
            )
        self.conn.commit()

    def get_stats(self, student_id: int) -> dict:
        row = self.conn.execute(
            "SELECT * FROM gamification WHERE student_id = ?", (student_id,)
        ).fetchone()
        if row:
            return dict(row)
        return {"student_id": student_id, "streak_days": 0, "last_active_date": None, "badges_json": "[]"}

    def add_badge(self, student_id: int, badge_name: str):
        stats = self.get_stats(student_id)
        badges = json.loads(stats["badges_json"])
        if badge_name not in badges:
            badges.append(badge_name)
            self.conn.execute(
                "UPDATE gamification SET badges_json = ? WHERE student_id = ?",
                (json.dumps(badges), student_id)
            )
            self.conn.commit()
            return True
        return False

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

    # ── Agent Persistent States ───────────────────────────────────

    def get_agent_state(self, student_id: int, agent_name: str) -> dict:
        row = self.conn.execute(
            "SELECT state_json FROM agent_states WHERE student_id = ? AND agent_name = ?",
            (student_id, agent_name)
        ).fetchone()
        if row:
            return json.loads(row["state_json"])
        return {}

    def set_agent_state(self, student_id: int, agent_name: str, state: dict):
        state_json = json.dumps(state)
        self.conn.execute(
            """INSERT INTO agent_states (student_id, agent_name, state_json)
               VALUES (?, ?, ?)
               ON CONFLICT(student_id, agent_name) DO UPDATE SET state_json = ?""",
            (student_id, agent_name, state_json, state_json)
        )
        self.conn.commit()

    # ── Reports ─────────────────────────────────────────────────────

    def generate_summary(self, student_id: int) -> dict:
        """Generate a snapshot summary of all progress for a student."""
        mastery = self.get_all_mastery(student_id)
        total_interactions = self.conn.execute(
            "SELECT COUNT(*) as c FROM interactions WHERE student_id = ?", (student_id,)
        ).fetchone()["c"]
        today_count = len(self.get_today_interactions(student_id))
        projects = self.get_projects(student_id)
        pending_goals = self.get_pending_goals(student_id)
        stats = self.get_stats(student_id)

        return {
            "mastery": mastery,
            "total_interactions": total_interactions,
            "today_interactions": today_count,
            "projects_completed": len([p for p in projects if p["status"] == "completed"]),
            "projects_in_progress": len([p for p in projects if p["status"] != "completed"]),
            "pending_goals": len(pending_goals),
            "goals": pending_goals,
            "streak": stats["streak_days"],
            "badges": json.loads(stats["badges_json"])
        }

    def preload_topics(self):
        """Populate the topics table with core STEM concepts if empty."""
        topics = [
            # MATH
            ("Basic Algebra", "math", 1, "[]", "Balance Scale", "Solving for x, basic operations."),
            ("Fractions & Decimals", "math", 1, "[]", None, "Working with parts of a whole."),
            ("Linear Equations", "math", 2, '["Basic Algebra"]', "Hanger Balance", "Graphing and solving y=mx+b."),
            ("Pythagorean Theorem", "math", 1, '["Basic Algebra"]', "Square Cutouts", "a² + b² = c²."),
            ("Trigonometry Basics", "math", 2, '["Pythagorean Theorem"]', "Sun Clinometer", "Sin, Cos, Tan and the Unit Circle."),
            ("Vectors & Matrices", "math", 3, '["Trigonometry Basics"]', "Force Table", "Direction, magnitude, and linear transforms."),
            ("Calculus (Differentiation)", "math", 3, '["Trigonometry Basics", "Linear Equations"]', "Slope Slider", "Rates of change and derivatives."),
            ("Calculus (Integration)", "math", 3, '["Calculus (Differentiation)"]', "Area cutouts", "Integration and areas under curves."),
            ("Differential Equations", "math", 4, '["Calculus (Integration)"]', "Growth model", "Modeling change over time."),
            
            # PHYSICS - MECHANICS
            ("Units & Measurements", "Mechanics", 1, '["Fractions & Decimals"]', "Handmade Ruler", "SI units and error analysis."),
            ("Scalars & Vectors", "Mechanics", 1, '["Trigonometry Basics"]', "Rubber Band Force", "Combining physical quantities."),
            ("Kinematics", "Mechanics", 2, '["Calculus (Differentiation)"]', "Bamboo Incline", "Position, velocity, acceleration."),
            ("Newton's Laws", "Mechanics", 2, '["Basic Algebra"]', "Balloon Powered Car", "Force, mass, and acceleration."),
            ("Friction", "Mechanics", 2, '["Newton\'s Laws"]', "Sandpaper Sled", "Static and kinetic friction."),
            ("Work & Power", "Mechanics", 2, '["Calculus (Integration)"]', "Water lifting pulley", "Force over distance."),
            ("Energy Conservation", "Mechanics", 2, '["Work & Power"]', "Marble Rollercoaster", "Potential and kinetic energy."),
            ("Momentum", "Mechanics", 2, '["Newton\'s Laws"]', "Newton's Cradle", "Impulse and collisions."),
            ("Circular Motion", "Mechanics", 3, '["Kinematics", "Trigonometry Basics"]', "Whirling stopper", "Centripetal force."),
            ("Gravitation", "Mechanics", 3, '["Newton\'s Laws"]', "Lead weight test", "Universal Law of Gravitation."),
            ("Oscillations (SHM)", "Mechanics", 3, '["Trigonometry Basics", "Calculus (Differentiation)"]', "Bottle Pendulum", "Periodic motion."),
            
            # PHYSICS - ELECTROMAGNETISM
            ("Electrostatics", "Electromagnetism", 2, '["Basic Algebra"]', "PVC Electroscope", "Static charges and Coulomb's law."),
            ("Electric Fields", "Electromagnetism", 3, '["Vectors & Matrices", "Electrostatics"]', None, "Mapping electrical force fields."),
            ("Ohm's Law", "Electromagnetism", 2, '["Basic Algebra"]', "Lemon Battery", "Voltage, current, and resistance."),
            ("DC Circuits", "Electromagnetism", 2, '["Ohm\'s Law"]', "Cardboard Flashlight", "Series and parallel circuits."),
            ("Magnetism", "Electromagnetism", 2, '["Electrostatics"]', "Nail Electromagnet", "Magnetic fields and poles."),
            ("Electromagnetic Induction", "Electromagnetism", 3, '["DC Circuits", "Magnetism"]', "Hand-crank generator", "Faraday's Law."),
            
            # PHYSICS - THERMODYNAMICS
            ("Temperature & Heat", "Thermodynamics", 2, '["Basic Algebra"]', "Homemade Thermometer", "Thermal energy and temperature scales."),
            ("Laws of Thermodynamics", "Thermodynamics", 3, '["Calculus (Differentiation)"]', "Steam Engine Model", "Entropy and energy conservation."),
            
            # PHYSICS - WAVES & OPTICS
            ("Wave Properties", "Waves & Optics", 2, '["Trigonometry Basics"]', "String Phone", "Frequency, wavelength, amplitude."),
            ("Optics (Reflection)", "Waves & Optics", 2, '["Geometry Basics"]', "Cardboard Mirror Periscope", "Law of reflection."),
            ("Optics (Refraction)", "Waves & Optics", 2, '["Trigonometry Basics"]', "Water Prism", "Snell's Law."),
            ("Lenses", "Waves & Optics", 2, '["Optics (Refraction)"]', "Magnifying Glass Camera", "Converging and diverging lenses."),

            # PHYSICS - QUANTUM BASICS
            ("Atomic Structure", "Quantum Basics", 3, '["Electrostatics"]', "Bohr Model Kit", "Understanding atoms and subatomic particles."),
            ("Quantum Intro", "Quantum Basics", 4, '["Calculus (Differentiation)"]', None, "Dual nature of light and matter."),
        ]

        for t in topics:
            self.conn.execute("""
                INSERT OR REPLACE INTO topics 
                (name, category, difficulty, prerequisites, build_hint, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, t)
        self.conn.commit()

    def get_topic(self, name: str) -> Optional[dict]:
        row = self.conn.execute("SELECT * FROM topics WHERE LOWER(name) = LOWER(?)", (name,)).fetchone()
        if row:
            data = dict(row)
            data["prerequisites"] = json.loads(data["prerequisites"])
            return data
        return None

    def get_all_topics(self, category: str = None) -> list[dict]:
        if category:
            rows = self.conn.execute("SELECT * FROM topics WHERE category = ? ORDER BY id", (category,)).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM topics ORDER BY category, id").fetchall()
        
        results = []
        for r in rows:
            data = dict(r)
            data["prerequisites"] = json.loads(data["prerequisites"])
            results.append(data)
        return results

    def close(self):
        self.conn.close()
    # --- Knowledge Distillation ---

    def save_distilled_lesson(self, topic: str, category: str, content: str, source_llm: str = None):
        """Save a high-quality lesson for future offline/fast retrieval."""
        self.conn.execute('''
            INSERT OR REPLACE INTO distilled_knowledge (topic, category, content, source_llm)
            VALUES (?, ?, ?, ?)
        ''', (topic, category, content, source_llm))
        self.conn.commit()

    def get_distilled_lesson(self, topic: str) -> Optional[dict]:
        """Retrieve a previously distilled lesson, prioritizing verified ones."""
        row = self.conn.execute("""
            SELECT * FROM distilled_knowledge WHERE LOWER(topic) = LOWER(?)
            ORDER BY verified DESC, created_at DESC LIMIT 1
        """, (topic,)).fetchone()
        return dict(row) if row else None

    def verify_distilled_lesson(self, lesson_id: int):
        """Mark a lesson as verified by an expert/sage."""
        self.conn.execute("UPDATE distilled_knowledge SET verified = 1 WHERE id = ?", (lesson_id,))
        self.conn.commit()

    def get_unverified_lessons(self, category: str = None) -> list[dict]:
        query = "SELECT * FROM distilled_knowledge WHERE verified = 0"
        params = []
        if category:
            query += " AND category = ?"
            params.append(category)
        rows = self.conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def log_learning_signal(self, student_id: int, topic: str, signal_type: str, value: float):
        """Log a granular learning signal for future model training."""
        self.conn.execute('''
            INSERT INTO learning_signals (student_id, topic, signal_type, value)
            VALUES (?, ?, ?, ?)
        ''', (student_id, topic, signal_type, value))
        self.conn.commit()
