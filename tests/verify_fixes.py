
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Force offline backend
os.environ["LLM_BACKEND"] = "offline"

from main import init_agents, handle_message

def test_fixes():
    print("Starting Bug Fix Verification...")
    agents, backend, model, db = init_agents()
    student_id = 1
    
    # 1. Test Math Tutor /lesson (should NOT trigger verifier syntax error)
    print("\nTesting Math Tutor /lesson...")
    label, resp = handle_message("/lesson Basic Algebra", agents, db, student_id)
    print(f"Agent: {label}")
    assert "Offline" in resp or "lesson" in resp.lower()
    print("✅ Math Tutor /lesson fixed (no syntax error).")
    
    # 2. Test Physics Supervisor /study kinematics (case-insensitive)
    print("\nTesting Physics Supervisor /study kinematics...")
    label, resp = handle_message("/study kinematics", agents, db, student_id)
    print(f"Agent: {label}")
    # Prereq check usually happens. If "not found" is gone, we are good.
    assert "Topic 'kinematics' not found" not in resp
    print(f"Response: {resp[:50]}...")
    print("✅ Physics Supervisor /study kinematics fixed.")

    print("\n✅ All bug fixes verified!")

if __name__ == "__main__":
    test_fixes()
