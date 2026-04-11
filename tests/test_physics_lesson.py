
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

def test_physics_lesson():
    print("Starting Physics Lesson Test...")
    
    # Use in-memory DB for isolation
    db = ProgressDB(":memory:")
    agents, backend, model, _ = init_agents(db=db)
    student_id = 1
    
    # Set mastery so prerequisites are met for kinematics
    # Kinematics requires Fractions & Decimals in old curriculum, but let's check new DB
    # Actually, in offline mode, check_prerequisites returns False for many things unless DB is set.
    db.set_mastery_score(student_id, "Basic Algebra", "math", 80.0)
    db.set_mastery_score(student_id, "Fractions & Decimals", "math", 80.0)
    db.set_mastery_score(student_id, "Linear Equations", "math", 80.0)
    db.set_mastery_score(student_id, "Calculus (Differentiation)", "math", 80.0)
    
    # Step 1: Request a physics lesson
    print("\nStep 1: Requesting Kinematics lesson...")
    label1, resp1 = handle_message("/lesson kinematics", agents, db, student_id)
    print(f"Agent: {label1}")
    
    assert "PhysicsSupervisor" in label1
    assert "offline" in resp1.lower() # Offline mode returns placeholder
    
    # Step 2: Try a math lesson with the same command (should route to MathTutor)
    print("\nStep 2: Requesting Algebra lesson...")
    label2, resp2 = handle_message("/lesson algebra", agents, db, student_id)
    print(f"Agent: {label2}")
    assert "MathTutor" in label2

    print("\n✅ Physics Lesson Test PASSED!")
    db.close()

if __name__ == "__main__":
    try:
        test_physics_lesson()
    except Exception as e:
        print(f"\n❌ Test FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
