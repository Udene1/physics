"""
test_simulation.py — End-to-end test for the AI Learning Companion.

Tests all core modules without requiring Ollama to be running.
"""

import sys
import os

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(__file__))


def test_progress_db():
    """Test SQLite progress database."""
    print("=" * 50)
    print("TEST 1: Progress Database")
    print("=" * 50)

    from tools.progress_db import ProgressDB
    db = ProgressDB(":memory:")

    # Test mastery tracking
    db.update_mastery("algebra", "math", True)
    db.update_mastery("algebra", "math", True)
    db.update_mastery("algebra", "math", False)
    m = db.get_mastery("algebra")
    assert m is not None, "Mastery record should exist"
    assert m["score"] == 66.7, f"Score should be 66.7, got {m['score']}"
    assert m["problems_attempted"] == 3
    assert m["problems_correct"] == 2
    print(f"  Mastery tracking: PASS (score={m['score']}%)")

    # Test interaction logging
    db.log_interaction("MathTutor", "algebra", "What is 2+2?", "4", "correct")
    interactions = db.get_recent_interactions(limit=5)
    assert len(interactions) == 1
    print(f"  Interaction logging: PASS ({len(interactions)} logged)")

    # Test goals
    gid = db.add_goal("Complete 5 algebra problems", agent="MathTutor")
    goals = db.get_pending_goals()
    assert len(goals) == 1
    db.complete_goal(gid)
    goals = db.get_pending_goals()
    assert len(goals) == 0
    print("  Goal management: PASS")

    # Test projects
    pid = db.add_project("LED Circuit", "Simple LED build", ["circuits"])
    projects = db.get_projects()
    assert len(projects) == 1
    db.update_project_status(pid, "completed")
    completed = db.get_projects(status="completed")
    assert len(completed) == 1
    print("  Project tracking: PASS")

    # Test summary
    summary = db.generate_summary()
    assert summary["total_interactions"] == 1
    assert summary["projects_completed"] == 1
    print(f"  Summary generation: PASS")

    db.close()
    print("  >> All DB tests PASSED\n")
    return True


def test_math_verifier():
    """Test SymPy math verification."""
    print("=" * 50)
    print("TEST 2: Math Verifier")
    print("=" * 50)

    from tools.math_verifier import MathVerifier
    v = MathVerifier()

    # Test equivalent expressions
    ok, msg = v.verify_symbolic("x**2 + 2*x + 1", "(x+1)**2")
    assert ok, f"Should be equivalent: {msg}"
    print(f"  Symbolic equiv: PASS")

    # Test non-equivalent expressions
    ok, msg = v.verify_symbolic("x**2", "x**3")
    assert not ok, "Should NOT be equivalent"
    print(f"  Symbolic non-equiv: PASS")

    # Test numeric verification
    ok, msg = v.verify_numeric("sin(x)**2 + cos(x)**2", "1")
    assert ok, f"Trig identity should verify: {msg}"
    print(f"  Numeric verify: PASS")

    # Test derivative
    result = v.compute_derivative("x**3 + 2*x", "x")
    assert "3*x**2" in result
    print(f"  Derivative: PASS (d/dx[x^3+2x] = {result})")

    # Test integral
    result = v.compute_integral("2*x", "x")
    assert "x**2" in result
    print(f"  Integral: PASS (int 2x dx = {result})")

    print("  >> All Verifier tests PASSED\n")
    return True


def test_problem_generator():
    """Test problem generation."""
    print("=" * 50)
    print("TEST 3: Problem Generator")
    print("=" * 50)

    from tools.problem_generator import ProblemGenerator
    pg = ProblemGenerator()

    # Test topic listing
    topics = pg.get_available_topics()
    assert len(topics) > 0
    print(f"  Available topics: {list(topics.keys())}")

    # Test algebra problems
    probs = pg.generate("algebra", 1, 3)
    assert len(probs) == 3
    for p in probs:
        assert "statement" in p
        assert "solution" in p
        assert "hint" in p
    print(f"  Algebra (d=1): {len(probs)} problems generated")
    for p in probs:
        print(f"    Q: {p['statement']}")

    # Test calculus problems
    probs = pg.generate("calculus", 2, 2)
    assert len(probs) == 2
    print(f"  Calculus (d=2): {len(probs)} problems generated")

    # Test nonexistent topic fallback
    probs = pg.generate("topology", 1, 1)
    assert len(probs) == 1
    print(f"  Unknown topic fallback: PASS")

    print("  >> All Generator tests PASSED\n")
    return True


def test_agents_import():
    """Test that all agents can be imported and instantiated."""
    print("=" * 50)
    print("TEST 4: Agent Import & Instantiation")
    print("=" * 50)

    from tools.progress_db import ProgressDB
    db = ProgressDB(":memory:")

    from agents.companion import CompanionAgent
    c = CompanionAgent(db=db)
    greeting = c.greet()
    assert len(greeting) > 0
    print(f"  CompanionAgent: PASS (greeting length={len(greeting)})")

    from agents.math_tutor import MathTutorAgent
    mt = MathTutorAgent(db=db)
    assert mt.name == "MathTutor"
    print(f"  MathTutorAgent: PASS")

    from agents.physics_supervisor import PhysicsSupervisorAgent
    ps = PhysicsSupervisorAgent(db=db)
    result = ps.check_prerequisites("quantum_basics")
    assert result["allowed"] == False  # No mastery yet
    print(f"  PhysicsSupervisorAgent: PASS (quantum blocked: {not result['allowed']})")

    overview = ps.get_curriculum_overview()
    assert "Mechanics" in overview
    print(f"  Curriculum overview: PASS")

    from agents.hardware_bridge import HardwareBridgeAgent
    hb = HardwareBridgeAgent(db=db)
    builds = hb.list_available_projects()
    assert "LED" in builds or "Soil" in builds
    print(f"  HardwareBridgeAgent: PASS")

    from agents.progress_tracker import ProgressTrackerAgent
    pt = ProgressTrackerAgent(db=db)
    report = pt.generate_report()
    assert "Progress Report" in report
    print(f"  ProgressTrackerAgent: PASS")

    db.close()
    print("  >> All Agent tests PASSED\n")
    return True


def test_intent_classifier():
    """Test intent classification."""
    print("=" * 50)
    print("TEST 5: Intent Classification")
    print("=" * 50)

    from main import classify_intent

    assert classify_intent("hello there") == "companion"
    assert classify_intent("what is a derivative") == "math"
    assert classify_intent("explain Newton's laws") == "physics"
    assert classify_intent("I want to build a sensor") == "hardware"
    assert classify_intent("/problems algebra") == "math"
    assert classify_intent("/builds") == "hardware"
    assert classify_intent("/report") == "progress"
    assert classify_intent("/curriculum") == "physics"
    print("  All intent classifications: PASS")
    print("  >> Intent classifier PASSED\n")
    return True


def test_session_artifact():
    """Test session artifact generation."""
    print("=" * 50)
    print("TEST 6: Session Artifact Generation")
    print("=" * 50)

    import tempfile
    from tools.progress_db import ProgressDB
    from agents.progress_tracker import ProgressTrackerAgent

    db = ProgressDB(":memory:")
    db.update_mastery("algebra", "math", True)
    db.log_interaction("test", "algebra", "test input", "test response")

    pt = ProgressTrackerAgent(db=db)

    # Use temp directory for artifact
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = pt.generate_session_artifact(session_dir=tmpdir)
        assert os.path.exists(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        assert "Session Artifact" in content
        assert "Progress Report" in content
        print(f"  Artifact generated: {os.path.basename(filepath)}")
        print(f"  Content length: {len(content)} chars")

    db.close()
    print("  >> Session artifact PASSED\n")
    return True


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("   AI Learning Companion — End-to-End Test Suite")
    print("=" * 60 + "\n")

    results = []
    results.append(("Progress Database", test_progress_db()))
    results.append(("Math Verifier", test_math_verifier()))
    results.append(("Problem Generator", test_problem_generator()))
    results.append(("Agent Import", test_agents_import()))
    results.append(("Intent Classifier", test_intent_classifier()))
    results.append(("Session Artifact", test_session_artifact()))

    print("=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    all_pass = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  {status}: {name}")
        if not passed:
            all_pass = False

    print()
    if all_pass:
        print("ALL TESTS PASSED! The system is ready to use.")
    else:
        print("SOME TESTS FAILED. Check output above.")
    print()
