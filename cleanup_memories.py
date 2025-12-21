import sys
import os

# Add the project root to sys.path
sys.path.append(os.getcwd())

from core.memory import get_memory

def cleanup():
    print("🧹 Starting memory cleanup...")
    mem = get_memory()
    
    # We want to clear the 'strategies' collection which contains Tetyana's actions
    # In core/trinity.py, Tetyana saves with metadata {"type": "tetyana_action"}
    
    print("🗑️ Deleting all memories from 'strategies' with type 'tetyana_action'...")
    res = mem.delete_memory("strategies", where_filter={"type": "tetyana_action"})
    
    if res.get("status") == "success":
        print("✅ Cleanup successful!")
    else:
        print(f"❌ Cleanup failed: {res.get('error')}")
        
    # Optional: also clear episodic memory if needed
    # mem_h = get_hierarchical_memory()
    # mem_h.clear_episodic_memory()

if __name__ == "__main__":
    cleanup()
