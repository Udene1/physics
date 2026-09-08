import os
import unittest

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
        self.engine.answer(self.student_id, first["id"], 1)
        resumed = LearningEngine(self.db).current_question(self.student_id)
        self.assertEqual(resumed["number"], 2)
        self.assertEqual(resumed["id"], DIAGNOSTIC[1].id)

    def test_stale_question_is_rejected(self):
        self.engine.start(self.student_id)
        first = self.engine.current_question(self.student_id)
        self.engine.answer(self.student_id, first["id"], 1)
        with self.assertRaises(ValueError):
            self.engine.answer(self.student_id, first["id"], 1)

    def test_math_intervention_is_selected(self):
        for question in DIAGNOSTIC:
            answer = question.correct_index
            if question.skill == "algebra":
                answer = (question.correct_index + 1) % len(question.choices)
            self.engine.answer(self.student_id, question.id, answer)
        snapshot = self.engine.snapshot(self.student_id)
        self.assertEqual(snapshot["current_skill"], "algebra")
        self.assertEqual(snapshot["current_stage"], "math_foundation")

    def test_strong_learner_can_reach_physics_extension(self):
        for question in DIAGNOSTIC:
            self.engine.answer(self.student_id, question.id, question.correct_index)
        snapshot = self.engine.snapshot(self.student_id)
        self.assertEqual(snapshot["current_skill"], "vectors")
        self.assertEqual(snapshot["current_stage"], "math_foundation")


if __name__ == "__main__":
    unittest.main()
