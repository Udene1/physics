
import os
import sys
import unittest
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Mock environment
os.environ["LLM_BACKEND"] = "offline"

from main import handle_message, init_agents
from tools.progress_db import ProgressDB

class TestRoutingAndMastery(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_resilience.db"
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

    def test_routing_stickiness(self):
        print("\n--- Testing Agent Routing Stickiness ---")
        # 1. Engage with Physics Supervisor
        handle_message("/lesson kinematics", self.agents, self.db, self.student_id)
        self.assertEqual(self.db.get_meta("last_active_agent"), "physics")
        
        # 2. Respond with a numeric-looking answer "10.5"
        # In current main.py (pre-fix), this would be routed to Math Tutor.
        # With the fix, it should stay with Physics because last_agent was physics and it's a short response.
        label, _ = handle_message("10.5", self.agents, self.db, self.student_id)
        print(f"Routed '10.5' to: {label}")
        self.assertIn("Physics", label)

    def test_physics_mastery_update(self):
        print("\n--- Testing Physics Mastery Update ---")
        # 1. Start a lesson to set active_topic
        topic = "Kinematics"
        self.agents["physics"].teach_topic(self.student_id, topic)
        
        # 2. Force an evaluation response
        # We'll mock the super().chat response implicitly if we were in real LLM,
        # but in offline mode it returns something generic.
        # We want to see if Mastery changes after evaluate_physics_response.
        
        # Initial score
        initial = self.db.get_mastery(self.student_id, topic)
        initial_score = initial["score"] if initial else 0.0
        
        # Call evaluate (Offline returns generic stuff, we check for presence of progress bump)
        # Note: evaluate_physics_response calls super().chat which returns "Offline" normally.
        # I'll manually call set_mastery_score to simulate success or adjust the agent code to be testable.
        
        # Let's mock the response part that contains [CORRECT]
        import unittest.mock as mock
        with mock.patch('agents.base.BaseAgent.chat', return_value='[CORRECT] Good understanding!'):
            self.agents["physics"].evaluate_physics_response(self.student_id, "Acceleration is change in velocity")
        
        updated = self.db.get_mastery(self.student_id, topic)
        new_score = updated["score"] if updated else 0.0
        print(f"Physics Mastery for {topic}: {initial_score} -> {new_score}")
        self.assertGreater(new_score, initial_score)

    def test_history_endpoint_logic(self):
        print("\n--- Testing History Payload Logic ---")
        # 1. Log some interactions
        self.db.log_interaction(self.student_id, "PhysicsSupervisor", "kinematics", "What is G?", "Gravity constant", "ok")
        
        # 2. Simulate the /history endpoint logic
        history = self.db.get_recent_interactions(self.student_id, limit=5)
        self.assertGreater(len(history), 0)
        self.assertEqual(history[0]["agent"], "PhysicsSupervisor")

if __name__ == "__main__":
    unittest.main()
