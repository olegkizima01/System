import sys
import os

# Add repo root to path
sys.path.append(os.getcwd())

try:
    from core.trinity.runtime import TrinityRuntime
    from core.trinity.state import TrinityState
    print("✅ Successfully imported TrinityRuntime")
except ImportError as e:
    print(f"❌ Failed to import TrinityRuntime: {e}")
    sys.exit(1)

try:
    rt = TrinityRuntime(verbose=False, enable_self_healing=False)
    print("✅ Successfully instantiated TrinityRuntime")
except Exception as e:
    print(f"❌ Failed to instantiate TrinityRuntime: {e}")
    sys.exit(1)

# Check for mixin methods
methods = [
    "_meta_planner_node", "_atlas_node", "_tetyana_node", "_grisha_node", 
    "_knowledge_node", "_build_graph", "_register_tools", 
    "_initialize_self_healing", "_auto_commit_on_success"
]

missing = []
for m in methods:
    if not hasattr(rt, m):
        missing.append(m)

if missing:
    print(f"❌ Missing methods (Mixin integration failed): {missing}")
    sys.exit(1)
else:
    print("✅ All mixin methods present on TrinityRuntime instance")

print("🎉 Verification Successful")
sys.exit(0)
