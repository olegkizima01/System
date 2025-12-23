"""
Trinity Runtime - Core orchestration engine for Project Atlas.

This package provides the multi-agent system for autonomous macOS operation.
The Trinity Graph consists of:

- **Meta-Planner**: Orchestrator that sets strategy and manages replanning
- **Atlas**: Tactical planner/architect that generates execution plans
- **Tetyana**: Executor (Native/GUI/Playwright) that performs actions
- **Grisha**: Verifier with enhanced vision analysis
- **Knowledge**: Learning extractor for experience management

## Quick Start

```python
from core.trinity import TrinityRuntime, TrinityPermissions

# Create runtime with permissions
permissions = TrinityPermissions(allow_shell=True, allow_gui=True)
runtime = TrinityRuntime(permissions=permissions)

# Execute a task
for event in runtime.run("Create a new Python file"):
    print(event)
```

## Module Structure

- `runtime.py` - TrinityRuntime main class
- `state.py` - TrinityState and TrinityPermissions definitions
- `nodes/` - Agent node implementations (meta_planner, atlas, tetyana, grisha)
- `planning/` - Planning strategies and optimization
- `integration/` - Vibe Assistant and external integrations
"""

# Re-export main classes for backwards compatibility
# This allows: from core.trinity import TrinityRuntime
# Note: We keep trinity.py as the main implementation for now,
# and will migrate incrementally

from core.trinity.state import TrinityState, TrinityPermissions

# Import from legacy module for now - will be migrated
import sys
import importlib.util

# Check if we're being imported from the legacy trinity.py
# to avoid circular imports
_trinity_legacy_path = __file__.replace('/trinity/__init__.py', '/trinity.py')
if _trinity_legacy_path not in sys.modules:
    try:
        # Dynamic import to avoid circular dependency
        spec = importlib.util.spec_from_file_location("core.trinity_legacy", _trinity_legacy_path)
        if spec and spec.loader:
            _legacy = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(_legacy)
            TrinityRuntime = _legacy.TrinityRuntime
        else:
            # Fallback: define a stub
            TrinityRuntime = None
    except Exception:
        TrinityRuntime = None
else:
    TrinityRuntime = None

__all__ = [
    "TrinityRuntime",
    "TrinityState",
    "TrinityPermissions",
]

__version__ = "2.1.0"
__author__ = "Project Atlas Team"
