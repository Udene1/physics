
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

os.environ["LLM_BACKEND"] = "offline"

from agents.math_tutor import MathTutorAgent
from tools.progress_db import ProgressDB

def test_state_persistence():
    print("Starting State Persistence Test...")
    db_path = os.path.abspath("test_persistence.db")
    if os.path.exists(db_path): os.remove(db_path)
    
    try:
        db = ProgressDB(db_path)
        student_id = 1
        
        # Instance 1: Generate problems
        print("\nInstance 1: Starting algebra session...")
        agent1 = MathTutorAgent(db=db)
        resp1 = agent1.chat("/problems algebra", student_id=student_id)
        print(f"Response 1: {resp1[:100]}...")
        
        state1 = agent1.get_student_state(student_id)
        assert len(state1["problems"]) > 0
        print("✅ Session state saved to DB.")
        
        # Close DB to ensure write
        db.close()
        
        # Instance 2: Simulate restart
        print("\nInstance 2: Simulating server restart...")
        db2 = ProgressDB(db_path)
        agent2 = MathTutorAgent(db=db2)
        
        state2 = agent2.get_student_state(student_id)
        assert len(state2["problems"]) == len(state1["problems"])
        assert state2["problems"][0]["statement"] == state1["problems"][0]["statement"]
        print("✅ Session state recovered from DB.")
        
        # Verify an answer with the new instance
        problem = state2["problems"][0]
        correct_answer = problem["solution"]
        print(f"Verifying answer: {correct_answer}")
        
        resp2 = agent2.chat(correct_answer, student_id=student_id)
        print(f"Response 2: {resp2[:100]}...")
        assert "Correct" in resp2 or "Great job" in resp2
        print("✅ Implicit verification works on recovered state.")
        
        db2.close()
        print("\n✅ State Persistence Test PASSED!")
        
    finally:
        try:
            db.close()
        except: pass
        try:
            db2.close()
        except: pass
        
        # Give a small delay for OS to release file handles if needed
        import time
        time.sleep(0.5)
        
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except Exception as e:
                print(f"Warning: Could not remove test DB: {e}")

if __name__ == "__main__":
    try:
        test_state_persistence()
    except Exception as e:
        print(f"\n❌ Test FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
