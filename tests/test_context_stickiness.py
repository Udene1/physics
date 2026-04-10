
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Force offline backend for testing
os.environ["LLM_BACKEND"] = "offline"

from main import init_agents, handle_message
from tools.progress_db import ProgressDB

def test_context_stickiness():
    print("Starting Context Stickiness Test...")
    
    # Use in-memory DB for isolation
    db = ProgressDB(":memory:")
    agents, backend, model, _ = init_agents(db=db)
    student_id = 1
    
    # Step 1: Start a math session
    print("\nStep 1: Requesting algebra problems...")
    label1, resp1 = handle_message("/problems algebra", agents, db, student_id)
    print(f"Agent: {label1}")
    print(f"Response: {resp1}")
    
    assert "MathTutor" in label1
    assert "Problem 1:" in resp1
    
    # Extract the problem statement if possible, but we just need to send an answer
    # MathTutorAgent._handle_problem_request puts problems in self.states[student_id]["problems"]
    state = agents["math"].states[student_id]
    current_problem = state["problems"][state["index"]]
    correct_answer = current_problem["solution"]
    print(f"Debug: Correct answer is {correct_answer}")
    
    # Step 2: Send a bare numeric answer
    print(f"\nStep 2: Sending bare answer '{correct_answer}'...")
    label2, resp2 = handle_message(str(correct_answer), agents, db, student_id)
    print(f"Agent: {label2}")
    print(f"Response: {resp2}")
    
    # Before the fix, label2 would be "🌟 Companion"
    # After the fix, label2 should be "📐 MathTutor"
    assert "MathTutor" in label2
    assert "Great job!" in resp2 or "correct" in resp2.lower()
    
    # Step 3: Test a non-math message (should still go to Companion if not math-like)
    print("\nStep 3: Sending non-math message 'I am tired'...")
    label3, resp3 = handle_message("I am tired", agents, db, student_id)
    print(f"Agent: {label3}")
    
    # Note: "tired" is a companion keyword.
    assert "Companion" in label3 or "MathTutor" not in label3
    
    print("\n✅ Context Stickiness Test PASSED!")
    db.close()

if __name__ == "__main__":
    try:
        test_context_stickiness()
    except Exception as e:
        print(f"\n❌ Test FAILED: {str(e)}")
        sys.exit(1)
