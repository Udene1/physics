
import os
import sys
import unittest
import struct
import math

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Mock environment for offline testing
os.environ["LLM_BACKEND"] = "offline"

from tools.progress_db import ProgressDB

class TestVectorSearch(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_vector.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db = ProgressDB(self.db_path)

    def tearDown(self):
        self.db.close()
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except:
                pass

    def test_embedding_storage_and_search(self):
        print("\n--- Testing Vector Search Engine ---")
        
        # 1. Create dummy embeddings (3-dim for simplicity)
        # Vector A: [1.0, 0.0, 0.0] - "Physics"
        # Vector B: [0.0, 1.0, 0.0] - "Math"
        # Vector C: [0.9, 0.1, 0.0] - "Kinematics" (similar to Physics)
        
        vec_physics = [1.0, 0.0, 0.0]
        vec_math = [0.0, 1.0, 0.0]
        vec_kinematics = [0.9, 0.1, 0.0]
        
        self.db.save_distilled_lesson("Physics Basics", "physics", "All about motion.", "gemini", vec_physics)
        self.db.save_distilled_lesson("Math Logic", "math", "All about numbers.", "gemini", vec_math)
        
        # 2. Search for something similar to Physics (vec_kinematics)
        matches = self.db.search_semantic_knowledge(vec_kinematics, limit=1)
        
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]['topic'], "Physics Basics")
        print(f"Top match for Kinematics-like vector: {matches[0]['topic']} (Score: {matches[0]['score']:.4f})")
        
        # 3. Verify similarity score
        self.assertGreater(matches[0]['score'], 0.9)
        print("SUCCESS: Semantic retrieval successfully matched conceptual target.")

if __name__ == "__main__":
    unittest.main()
