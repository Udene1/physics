
import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from tools.progress_db import ProgressDB

def worker_task(db_path, worker_id):
    try:
        db = ProgressDB(db_path)
        for i in range(5):
            # Attempt a write operation that previously might have locked
            db.log_interaction(
                student_id=1,
                agent=f"Worker-{worker_id}",
                topic="Concurrency Test",
                user_input=f"Test {i}",
                agent_response="OK",
                result="test"
            )
            time.sleep(0.1)  # tiny sleep to overlap execution
        db.close()
        print(f"Worker {worker_id} finished successfully.")
    except Exception as e:
        print(f"Worker {worker_id} failed: {e}")

if __name__ == "__main__":
    test_db = "test_concurrent.db"
    
    # Pre-create the schema safely 
    db = ProgressDB(test_db)
    
    # We need a dummy student 
    try:
        db.conn.execute("INSERT INTO students (id, nickname, created_at) VALUES (1, 'Test', '2026')")
        db.conn.commit()
    except: pass
    db.close()

    print("Starting concurrent write test...")
    threads = []
    # Spin up 10 threads trying to write at the same time
    for i in range(10):
        t = threading.Thread(target=worker_task, args=(test_db, i))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    print("Test complete.")
    if os.path.exists(test_db):
        os.remove(test_db)
