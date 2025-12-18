import sys
import os
import threading
import time

# Ensure project root is in path
_repo_root = os.path.abspath(os.path.dirname(__file__))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

# Load environment
from tui.agents import load_env
load_env()

from tui.logger import setup_logging
logger = setup_logging(verbose=True, name="system_cli.trinity")

# Import Trinity
from tui.agents import run_graph_agent_task
from system_cli.state import state

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 debug_task.py <prompt>")
        sys.exit(1)
        
    prompt = sys.argv[1]
    print(f"🚀 Starting task: {prompt}")
    
    # Set unsafe mode and gui mode if needed
    state.ui_unsafe_mode = True
    state.ui_gui_mode = "auto"
    state.ui_execution_mode = "native"
    
    print("DEBUG: Calling run_graph_agent_task...")
    try:
        run_graph_agent_task(
            prompt,
            allow_file_write=True,
            allow_shell=True,
            allow_applescript=True,
            allow_gui=True,
            allow_shortcuts=True
        )
        print("DEBUG: run_graph_agent_task returned.")
    except Exception as e:
        print(f"❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
