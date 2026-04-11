import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import init_agents, handle_message
from tools.progress_db import ProgressDB

def test_teaching_flow():
    print("\n--- Starting Teaching Flow Verification ---")
    
    # Use a fresh test database
    db_path = "memory/test_teaching.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    db = ProgressDB(db_path)
    agents, backend, model, _ = init_agents(db)
    student_id = 1
    
    # Ensure guest student exists
    db.add_student("Tester")
    student_id = 1

    print("\nScenario 1: Physics Prerequisite Suggestion")
    # Kinematics requires Calculus (Differentiation) which has 0% mastery
    msg = "/prereq Kinematics"
    label, response = handle_message(msg, agents, db, student_id)
    print(f"User: {msg}")
    print(f"{label}: {response}")
    
    assert "Would you like a quick lesson? Try typing: `/lesson Calculus (Differentiation)`" in response
    print("✅ Scenario 1 PASSED")

    print("\nScenario 2: Explicit Lesson Request")
    msg = "/lesson Basic Algebra"
    label, response = handle_message(msg, agents, db, student_id)
    print(f"User: {msg}")
    print(f"{label}: {response}")
    
    # The response should be a lesson, not a problem set
    assert "Problem 1:" not in response
    assert "ready for a practice problem" in response.lower()
    print("✅ Scenario 2 PASSED")

    print("\nScenario 3: Problems with Concept Refresher")
    msg = "/problems Basic Algebra"
    label, response = handle_message(msg, agents, db, student_id)
    print(f"User: {msg}")
    print(f"{label}: {response}")
    
    assert "Remember: Always look for the first principle" in response
    assert "Problem 1:" in response
    print("✅ Scenario 3 PASSED")

    print("\n--- All Teaching Flow Tests PASSED! ---")
    db.close()
    if os.path.exists(db_path):
        os.remove(db_path)

if __name__ == "__main__":
    try:
        test_teaching_flow()
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
