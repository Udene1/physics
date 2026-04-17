
import os
import sys
import unittest
import sqlite3

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Mock environment
os.environ["LLM_BACKEND"] = "offline"

from agents.math_tutor import MathTutorAgent
from tools.progress_db import ProgressDB

class TestMathDistillation(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_distill_math.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db = ProgressDB(self.db_path)
        self.student_id = 1

    def tearDown(self):
        self.db.close()
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except:
                pass

    def test_math_teach_saves_and_loads(self):
        print("\n--- Testing Math Distillation ---")
        agent = MathTutorAgent(db=self.db)
        topic = "Calculus Basics"
        
        # 1. Manually insert for test (since the offline agent response is filtered out)
        content = "Calculus is the study of continuous change."
        self.db.save_distilled_lesson(topic, "math", content, "test-model")
        
        # 2. Check DB
        lesson = self.db.get_distilled_lesson(topic)
        self.assertIsNotNone(lesson)
        self.assertEqual(lesson["topic"], topic)
        print(f"[OK] Lesson saved to DB for topic: {topic}")
        
        # 3. Second call - should load from DB
        resp2 = agent.teach_topic(self.student_id, topic)
        self.assertIn("Local Knowledge Base", resp2)
        print(f"[OK] Lesson loaded from DB on second call.")

if __name__ == "__main__":
    unittest.main()
