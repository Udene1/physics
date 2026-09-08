import os
import unittest

from tools.learning_engine import LearningEngine
from tools.progress_db import ProgressDB


class TestLearningEngineGraphIntegration(unittest.TestCase):
    def setUp(self):
        self.path = "test_learning_engine_graph.db"
        if os.path.exists(self.path):
            os.remove(self.path)
        self.db = ProgressDB(self.path)
        self.student_id = self.db.add_student("GraphLearner")
        self.engine = LearningEngine(self.db)

    def tearDown(self):
        self.db.close()
        if os.path.exists(self.path):
            os.remove(self.path)

    def test_weak_algebra_blocks_motion(self):
        for skill, score in {
            "arithmetic": 100,
            "fractions": 100,
            "ratios": 100,
            "algebra": 40,
            "geometry": 100,
            "graphs": 100,
            "trigonometry": 100,
            "measurement": 100,
        }.items():
            self.engine.record_mastery(self.student_id, skill, score)

        status = self.engine.skill_status(self.student_id, "motion")
        self.assertFalse(status["ready"])
        self.assertIn("algebra", status["missing_prerequisites"])

    def test_mastery_can_move_learner_to_engineering(self):
        for skill in (
            "arithmetic", "fractions", "ratios", "algebra", "geometry", "graphs",
            "trigonometry", "vectors", "measurement", "motion", "forces", "energy",
            "electricity", "dc_circuits",
        ):
            self.engine.record_mastery(self.student_id, skill, 100)

        snapshot = self.engine.record_mastery(self.student_id, "engineering_design", 100)
        self.assertEqual(snapshot["next_action"], "engineering")


if __name__ == "__main__":
    unittest.main()
