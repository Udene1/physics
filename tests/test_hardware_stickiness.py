
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

def test_hardware_stickiness():
    print("Starting Hardware Stickiness Test...")
    
    # Use in-memory DB for isolation
    db = ProgressDB(":memory:")
    agents, backend, model, _ = init_agents(db=db)
    student_id = 1
    
    # Step 1: Start a hardware session
    print("\nStep 1: Requesting hardware builds...")
    label1, resp1 = handle_message("/builds", agents, db, student_id)
    print(f"Agent: {label1}")
    # print(f"Response: {resp1}")
    
    assert "HardwareBridge" in label1
    
    # Step 2: Send a follow-up without keywords
    print("\nStep 2: Sending follow-up 'Tell me more about the first one' (no keywords)...")
    label2, resp2 = handle_message("Tell me more about the first one", agents, db, student_id)
    print(f"Agent: {label2}")
    
    # Before the fix, this would have been "🌟 Companion"
    # After the fix, it should stick to "🔧 HardwareBridge"
    assert "HardwareBridge" in label2
    assert "offline" in resp2.lower() # Since backend is offline
    
    # Step 3: Switch to companion
    print("\nStep 3: Sending greeting 'Hello'...")
    label3, resp3 = handle_message("Hello", agents, db, student_id)
    print(f"Agent: {label3}")
    assert "Companion" in label3

    print("\n✅ Hardware Stickiness Test PASSED!")
    db.close()

if __name__ == "__main__":
    try:
        test_hardware_stickiness()
    except Exception as e:
        print(f"\n❌ Test FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
