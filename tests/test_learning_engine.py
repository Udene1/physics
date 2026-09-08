import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tools.learning_engine import DIAGNOSTIC, LearningEngine
from tools.progress_db import ProgressDB


class TestLearningEngine(unittest.TestCase):
    def setUp(self):
        self.path = "test_learning_engine.db"
        if os.path.exists(self.path):
            os.remove(self.path)
        self.db = ProgressDB(self.path)
        self.student_id = self.db.add_student("Learner")
        self.engine = LearningEngine(self.db)

    def tearDown(self):
        self.db.close()
        if os.path.exists(self.path):
            os.remove(self.path)

    def test_diagnostic_persists_and_resumes(self):
        self.engine.start(self.student_id)
        first = self.engine.current_question(self.student_id)
        self.assertEqual(first["number"], 1)

        self.engine.answer(self.student_id, first["id"], first["correct_index"] if "correct_index" in first else 1)

        # A new engine instance must recover the exact next question from DB state.
        resumed = LearningEngine(self.db).current_question(self.student_id)
        self.assertEqual(resumed["number"], 2)
        self.assertEqual(resumed["id"], DIAGNOSTIC[1].id)

    def test_stale_question_is_rejected(self):
        self.engine.start(self.student_id)
        first = self.engine.current_question(self.student_id)
        with self.assertRaises(ValueError):
            self.engine.answer(self.student_id, "not-the-current-question", 0)
        self.assertEqual(self.engine.current_question(self.student_id)["id"], first["id"])

    def test_finish_selects_math_intervention_for_weak_math(self):
        self.engine.start(self.student_id)
        for q in DIAGNOSTIC:
            # Intentionally answer every question incorrectly using the first
            # available choice. This is real engine behavior, not a mocked LLM.
            wrong = 0 if q.correct_index != 0 else 1
            self.engine.answer(self.student_id, q.id, wrong)

        snapshot = self.engine.snapshot(self.student_id)
        self.assertEqual(snapshot["status"], "complete")
        self.assertEqual(snapshot["current_stage"], "math_foundation")
        self.assertEqual(snapshot["current_skill"], "arithmetic")
        self.assertEqual(self.db.get_mastery(self.student_id, "arithmetic")["score"], 0.0)

    def test_all_correct_reaches_physics_extension(self):
        self.engine.start(self.student_id)
        for q in DIAGNOSTIC:
            self.engine.answer(self.student_id, q.id, q.correct_index)

        snapshot = self.engine.snapshot(self.student_id)
        self.assertEqual(snapshot["status"], "complete")
        self.assertEqual(snapshot["current_stage"], "physics_extension")
        self.assertEqual(snapshot["current_skill"], "motion")
        self.assertEqual(self.db.get_mastery(self.student_id, "algebra")["score"], 100.0)


if __name__ == "__main__":
    unittest.main()
