import sys
import os

# Ensure project root is in path
_repo_root = os.path.abspath(os.path.dirname(__file__))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

# Load environment
from tui.agents import load_env
load_env()

from system_ai.tools.vision import analyze_with_copilot
import json

def test_analyze():
    print("Testing analyze_screen (direct call)...")
    res = analyze_with_copilot(prompt="What do you see on the screen? Is there a CAPTCHA or movie search results?")
    print(json.dumps(res, indent=2))

if __name__ == "__main__":
    test_analyze()
