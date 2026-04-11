
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Force offline backend for testing initial state
os.environ["LLM_BACKEND"] = "offline"

from main import init_agents, handle_message
from tools.progress_db import ProgressDB

def test_knowledge_distillation():
    print("Starting Knowledge Distillation Test...")
    
    # Use in-memory DB for isolation
    db = ProgressDB(":memory:")
    agents, backend, model, _ = init_agents(db=db)
    student_id = 1
    
    # Set mastery for prerequisites to pass
    db.set_mastery_score(student_id, "Basic Algebra", "math", 80.0)
    db.set_mastery_score(student_id, "Calculus (Differentiation)", "math", 80.0)
    
    topic = "Kinematics"
    
    # Step 1: Request lesson in offline mode (should return "Offline" placeholder)
    print("\nStep 1: Requesting Kinematics lesson (Offline)...")
    label1, resp1 = handle_message(f"/lesson {topic}", agents, db, student_id)
    print(f"Agent: {label1}")
    assert "Offline" in resp1
    
    # Step 2: Manually inject a "distilled" lesson into the DB
    print("\nStep 2: Injecting high-quality distilled lesson...")
    mock_content = "# Kinematics 101\nPhysics is like moving from Ikeja to Lekki..."
    db.save_distilled_lesson(topic, "physics", mock_content, "MockGemini")
    
    # Step 3: Request the lesson again
    print("\nStep 3: Requesting Kinematics lesson again (should be served from DB)...")
    label2, resp2 = handle_message(f"/lesson {topic}", agents, db, student_id)
    print(f"Agent: {label2}")
    # print(f"Response: {resp2}")
    
    assert "Local Knowledge Base" in resp2
    assert "Ikeja to Lekki" in resp2
    
    # Step 4: Verify learning signals
    print("\nStep 4: Logging a learning signal...")
    db.log_learning_signal(student_id, topic, "speed", 0.85)
    
    signals = db.conn.execute("SELECT * FROM learning_signals").fetchall()
    assert len(signals) > 0
    print(f"Signal logged: {dict(signals[0])}")

    print("\n✅ Knowledge Distillation Test PASSED!")
    db.close()

if __name__ == "__main__":
    try:
        test_knowledge_distillation()
    except Exception as e:
        print(f"\n❌ Test FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
