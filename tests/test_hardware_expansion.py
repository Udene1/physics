
import os
import sys
import unittest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Mock environment
os.environ["LLM_BACKEND"] = "offline"

from main import init_agents
from tools.progress_db import ProgressDB

class TestHardwareExpansion(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_hardware.db"
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

    def test_list_projects(self):
        print("\n--- Testing Hardware Project Listing ---")
        output = self.agents["hardware"].list_available_projects(self.student_id)
        # Check if new projects are in the list
        self.assertIn("DIY Solar Phone Charger", output)
        self.assertIn("Water Level Indicator", output)
        self.assertIn("Cardboard Portable Flashlight", output)
        self.assertIn("Hand-Crank Emergency Generator", output)
        self.assertIn("Magnetic Reed Burglar Alarm", output)
        print("✅ New projects successfully listed.")

    def test_build_guide_generation(self):
        print("\n--- Testing Build Guide Generation ---")
        # Test one of the new projects
        output = self.agents["hardware"].teach_build(self.student_id, "solar_charger")
        self.assertIn("Solar", output)
        # Note: In offline mode, it returns a generic message, but we check if it handled the request
        print("✅ Solar Charger build guide requested and returned response.")

if __name__ == "__main__":
    unittest.main()
