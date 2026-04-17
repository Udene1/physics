
import os
import sys
import unittest
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Mock environment
os.environ["LLM_BACKEND"] = "offline"

from agents.math_tutor import MathTutorAgent
from agents.physics_supervisor import PhysicsSupervisorAgent
from tools.progress_db import ProgressDB

class TestEnhancedMemory(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_memory.db"
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

    def test_shared_memory_context(self):
        print("\n--- Testing Shared Memory Injection ---")
        # 1. Math Tutor logs an interaction
        math_agent = MathTutorAgent(db=self.db)
        math_agent.chat("What is 5+5?", student_id=self.student_id)
        
        # 2. Physics Supervisor should see this in its _build_messages
        physics_agent = PhysicsSupervisorAgent(db=self.db)
        messages = physics_agent._build_messages("Hello", student_id=self.student_id)
        
        # Check if shared context is in messages
        shared_ctx_found = False
        for msg in messages:
            if "SHARED SESSION MEMORY" in msg["content"]:
                shared_ctx_found = True
                print(f"[OK] Found shared context in prompt: {msg['content'][:100]}...")
                self.assertIn("MathTutor", msg["content"])
                self.assertIn("What is 5+5?", msg["content"])
        
        self.assertTrue(shared_ctx_found, "Shared context should be injected into messages")

    def test_history_persistence(self):
        print("\n--- Testing Chat History Persistence ---")
        agent_name = "TestAgent"
        
        # 1. First session
        math_agent = MathTutorAgent(db=self.db)
        math_agent.chat("First message", student_id=self.student_id)
        math_agent.chat("Second message", student_id=self.student_id)
        
        # Verify in-memory history
        self.assertEqual(len(math_agent.histories[self.student_id]), 4) # 2 user, 2 assistant
        
        # 2. Simulate restart: Create new agent instance with same DB
        new_agent = MathTutorAgent(db=self.db)
        # Trigger _get_history
        history = new_agent._get_history(self.student_id)
        
        self.assertEqual(len(history), 4, "History should be recovered from DB")
        self.assertEqual(history[0]["content"], "First message")
        self.assertEqual(history[2]["content"], "Second message")
        print("[OK] Chat history successfully recovered from DB interactions.")

if __name__ == "__main__":
    unittest.main()
