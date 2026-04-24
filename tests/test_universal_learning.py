
import os
import sys
import unittest
import json
import sqlite3

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Mock environment
os.environ["LLM_BACKEND"] = "offline"

from main import init_agents
from tools.progress_db import ProgressDB

class TestUniversalDistillation(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_universal.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db = ProgressDB(self.db_path)
        self.agents, _, _, _ = init_agents(self.db)
        self.student_id = 1

    def tearDown(self):
        self.db.close()
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except:
                pass

    def test_auto_distillation_and_cross_learning(self):
        print("\n--- Testing Auto-Distillation & Cross-Agent Learning ---")
        
        # 1. Simulate a high-quality lesson from Math Tutor
        # We need to mock the LLM response to be long enough and contain keywords
        import unittest.mock as mock
        long_explanation = (
            "The concept of Integration in calculus is like finding the total area "
            "under a curve. Imagine you are building a road in Benin City and need "
            "to calculate the total amount of sand needed for a non-linear patch. "
            "The fundamental principles of integration allow us to sum up infinitely "
            "small slices to get the exact total. This step-by-step approach is "
            "crucial for engineering. Here is a clear analogy: it is like counting "
            "every single grain of rice in a bag by weighing small handfuls."
        )
        # Ensure it's over 500 chars for our heuristic
        long_explanation = long_explanation.ljust(505, '.') 
        
        print("1. Mocking Math Tutor to provide a high-quality explanation...")
        with mock.patch('agents.base.BaseAgent._call_llm', return_value=long_explanation):
            # We pass Topic in context manually for the test
            self.agents["math"].chat("Tell me about integration", context="Topic: Integration", student_id=self.student_id)
        
        # 2. Verify it was distilled
        row = self.db.conn.execute("SELECT * FROM distilled_knowledge WHERE topic = 'Integration'").fetchone()
        self.assertIsNotNone(row, "Knowledge should have been auto-distilled!")
        print(f"✅ Knowledge 'Integration' distilled from MathTutor: {row['topic']}")

        # 3. Ask Physics Supervisor about the same topic
        # It should now pull this knowledge into its prompt context
        print("2. Asking Physics Supervisor about integration...")
        # We'll intercept _build_messages to see if the knowledge was injected
        messages = self.agents["physics"]._build_messages("How do I use integration in kinematics?", student_id=self.student_id)
        
        found_injected = False
        for m in messages:
            if "RELEVANT LOCAL KNOWLEDGE" in m["content"] and "Integration" in m["content"]:
                found_injected = True
                break
        
        self.assertTrue(found_injected, "Physics Supervisor should have received distilled math knowledge!")
        print("✅ Physics Supervisor successfully 'learned' from MathTutor's distilled knowledge.")

        # 4. Ask Companion about the same topic
        print("3. Asking Companion for a recap on integration...")
        comp_messages = self.agents["companion"]._build_messages("Give me a motivational recap on what I just learned about integration", student_id=self.student_id)
        
        found_in_comp = False
        for m in comp_messages:
            if "RELEVANT LOCAL KNOWLEDGE" in m["content"] and "Integration" in m["content"]:
                found_in_comp = True
                break
        
        self.assertTrue(found_in_in_comp := found_in_comp, "Companion should have received distilled math knowledge!")
        print("✅ Companion successfully 'learned' from MathTutor's distilled knowledge.")

if __name__ == "__main__":
    unittest.main()
