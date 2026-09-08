import unittest

from tools.skill_graph import (
    SKILLS,
    choose_next_skill,
    is_ready,
    learning_frontier,
    missing_prerequisites,
    prerequisite_chain,
    validate_graph,
)


class TestSkillGraph(unittest.TestCase):
    def test_graph_has_no_missing_nodes_or_cycles(self):
        validate_graph()
        self.assertGreater(len(SKILLS), 15)

    def test_math_is_required_before_motion(self):
        mastery = {
            "arithmetic": {"score": 100},
            "fractions": {"score": 100},
            "ratios": {"score": 100},
            "algebra": {"score": 100},
            "graphs": {"score": 100},
        }
        self.assertFalse(is_ready("motion", mastery))
        self.assertIn("measurement", missing_prerequisites("motion", mastery))

        mastery.update({"measurement": {"score": 100}})
        self.assertTrue(is_ready("motion", mastery))

    def test_frontier_does_not_skip_weak_prerequisites(self):
        mastery = {"arithmetic": {"score": 100}}
        frontier = learning_frontier(mastery)
        ids = [skill.id for skill in frontier]
        self.assertIn("fractions", ids)
        self.assertIn("geometry", ids)
        self.assertNotIn("motion", ids)
        self.assertNotIn("engineering_design", ids)

    def test_frontier_can_place_an_advanced_learner(self):
        mastery = {skill.id: {"score": 100} for skill in SKILLS}
        mastery["quantum_intro"]["score"] = 40
        mastery["engineering_design"]["score"] = 0
        next_skill = choose_next_skill(mastery, preferred_domain="engineering")
        self.assertEqual(next_skill.id, "engineering_design")

    def test_prerequisite_chain_is_stable(self):
        chain = prerequisite_chain("dc_circuits")
        self.assertLess(chain.index("electricity"), chain.index("dc_circuits") if "dc_circuits" in chain else len(chain))
        self.assertIn("algebra", chain)


if __name__ == "__main__":
    unittest.main()
