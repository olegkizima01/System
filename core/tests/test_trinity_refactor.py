import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Ensure core can be imported
sys.path.append(os.getcwd())

from core.trinity.runtime import TrinityRuntime
from core.trinity.state import TrinityState, TrinityPermissions

@pytest.fixture
def mock_dependencies():
    with patch("core.trinity.runtime.CopilotLLM") as mock_llm, \
         patch("core.trinity.runtime.Context7") as mock_ctx, \
         patch("core.trinity.runtime.AdaptiveVerifier") as mock_ver, \
         patch("core.trinity.runtime.MCPToolRegistry") as mock_reg, \
         patch("core.trinity.runtime.VisionContextManager") as mock_vis, \
         patch("core.trinity.runtime.VibeCLIAssistant") as mock_vibe, \
         patch("core.trinity.runtime.get_memory") as mock_mem, \
         patch("core.trinity.runtime.get_logger") as mock_log:
        
        yield {
            "llm": mock_llm,
            "ctx": mock_ctx
        }

def test_trinity_runtime_instantiation(mock_dependencies):
    """Test that TrinityRuntime can be instantiated with mocked dependencies."""
    rt = TrinityRuntime(verbose=False, enable_self_healing=False)
    assert rt is not None
    assert isinstance(rt, TrinityRuntime)

def test_mixin_methods_presence(mock_dependencies):
    """Test that runtime has methods from all mixins."""
    rt = TrinityRuntime(verbose=False, enable_self_healing=False)
    
    # MetaPlannerMixin
    assert hasattr(rt, "_meta_planner_node")
    assert hasattr(rt, "_prepare_meta_config")
    
    # AtlasMixin
    assert hasattr(rt, "_atlas_node")
    assert hasattr(rt, "_prepare_atlas_prompt")
    
    # TetyanaMixin
    assert hasattr(rt, "_tetyana_node")
    assert hasattr(rt, "_execute_tetyana_tools")
    
    # GrishaMixin
    assert hasattr(rt, "_grisha_node")
    assert hasattr(rt, "_run_grisha_tests")
    
    # KnowledgeMixin
    assert hasattr(rt, "_knowledge_node")
    
    # ExecutionMixin
    assert hasattr(rt, "_build_graph")
    assert hasattr(rt, "_router")
    
    # ToolsMixin
    assert hasattr(rt, "_register_tools")
    
    # GitMixin
    assert hasattr(rt, "_get_repo_changes")
    
    # SelfHealingMixin
    assert hasattr(rt, "_initialize_self_healing")

def test_initial_graph_build(mock_dependencies):
    """Test that the graph is built successfully."""
    rt = TrinityRuntime(verbose=False, enable_self_healing=False)
    assert rt.workflow is not None
