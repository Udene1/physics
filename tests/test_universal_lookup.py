
import os
import sys
import unittest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Mock environment
os.environ["LLM_BACKEND"] = "offline"

from agents.companion import CompanionAgent
from tools.progress_db import ProgressDB

class TestUniversalKnowledge(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_universal.db"
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

    def test_proactive_lookup(self):
        print("\n--- Testing Universal Knowledge Retrieval ---")
        # 1. Manually insert some distilled knowledge
        topic = "Solar Power"
        content = "Solar power is energy from the sun converted into electricity."
        self.db.save_distilled_lesson(topic, "physics", content, "test-model")
        
        # 2. Ask the CompanionAgent about Solar Power
        companion = CompanionAgent(db=self.db)
        messages = companion._build_messages("Tell me about Solar Power", student_id=self.student_id)
        
        # 3. Verify that the distilled content is in the messages
        found = False
        for msg in messages:
            if "RELEVANT LOCAL KNOWLEDGE" in msg["content"] and topic in msg["content"]:
                found = True
                print(f"[OK] CompanionAgent received distilled knowledge about '{topic}'")
                break
        
        self.assertTrue(found, "Knowledge should be proactively retrieved based on keywords")

if __name__ == "__main__":
    unittest.main()
