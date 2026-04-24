
import os
import sys
import unittest
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Mock environment
os.environ["LLM_BACKEND"] = "offline"

from app import app, db
from tools.progress_db import ProgressDB

class TestHistorySidebar(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.db_path = "test_sidebar.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        # Point app to test DB
        import app as app_mod
        app_mod.db = ProgressDB(self.db_path)
        self.db = app_mod.db
        
        # Create student and log some interactions
        self.student_id = self.db.add_student("testuser", "1234")
        with self.app.session_transaction() as sess:
            sess['student_id'] = self.student_id
            sess['nickname'] = 'testuser'
            sess['logged_in'] = True

    def tearDown(self):
        self.db.close()
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except:
                pass

    def test_sidebar_sessions_and_filtering(self):
        print("\n--- Testing History Sidebar Backend ---")
        
        # 1. Log interactions for different topics
        self.db.log_interaction(self.student_id, "MathTutor", "Algebra", "What is x?", "x is 5", "ok")
        self.db.log_interaction(self.student_id, "PhysicsSupervisor", "Kinematics", "What is v?", "v is d/t", "ok")
        self.db.log_interaction(self.student_id, "MathTutor", "Algebra", "Solve 2x=10", "x=5", "ok")

        # 2. Test /sessions endpoint
        resp = self.app.get('/sessions')
        data = json.loads(resp.data)
        print(f"Sessions found: {[s['topic'] for s in data['sessions']]}")
        self.assertEqual(len(data['sessions']), 2)
        topics = {s['topic'] for s in data['sessions']}
        self.assertIn("Algebra", topics)
        self.assertIn("Kinematics", topics)
        print("✅ /sessions correctly grouped unique topics.")

        # 3. Test /history filtering by topic
        resp = self.app.get('/history?topic=Kinematics')
        data = json.loads(resp.data)
        # Should only contain Kinematics messages
        for msg in data['history']:
            # Note: /history returns role/content/label
            # We don't return topic in the history payload itself, but we verify the count
            pass
        
        # We should have 2 messages (1 user, 1 assistant) for Kinematics
        self.assertEqual(len(data['history']), 2)
        print("✅ /history?topic=Kinematics correctly filtered messages.")

        # 4. Test /history filtering for Algebra (should have 4 messages)
        resp = self.app.get('/history?topic=Algebra')
        data = json.loads(resp.data)
        self.assertEqual(len(data['history']), 4)
        print("✅ /history?topic=Algebra correctly filtered messages.")

if __name__ == "__main__":
    unittest.main()
