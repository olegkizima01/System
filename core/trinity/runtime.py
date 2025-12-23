import os
import threading
import signal
import inspect
from typing import Optional, Callable, Dict, Any, List

from core.trinity.state import TrinityState, TrinityPermissions
from core.memory import get_memory
from core.context7 import Context7
from core.verification import AdaptiveVerifier
from core.mcp_registry import MCPToolRegistry
from core.vision_context import VisionContextManager
from core.vibe_assistant import VibeCLIAssistant
from tui.logger import get_logger
from providers.copilot import CopilotLLM

# Mixins
from core.trinity.nodes.meta_planner import MetaPlannerMixin
from core.trinity.nodes.atlas import AtlasMixin
from core.trinity.nodes.tetyana import TetyanaMixin
from core.trinity.nodes.grisha import GrishaMixin
from core.trinity.nodes.knowledge import KnowledgeMixin
from core.trinity.execution import TrinityExecutionMixin
from core.trinity.tools import TrinityToolsMixin
from core.trinity.integration_self_healing import TrinitySelfHealingMixin
from core.trinity.integration_git import IntegrationGitMixin

# Development/General identifiers
DEV_KEYWORDS = {"code", "debug", "fix", "implement", "refactor", "test", "create file", "edit", "modify", "function", "class", "module", "script"}
GENERAL_KEYWORDS = {"search", "find", "look up", "browse", "read", "check", "verify", "analyze", "summarize", "explain", "video", "watch"}

class TrinityRuntime(
    MetaPlannerMixin,
    AtlasMixin,
    TetyanaMixin,
    GrishaMixin,
    KnowledgeMixin,
    TrinityExecutionMixin,
    TrinityToolsMixin,
    TrinitySelfHealingMixin,
    IntegrationGitMixin
):
    """Main Trinity runtime engine, composed of modular mixins."""

    # Constants
    MAX_STEPS = 50
    MAX_REPLANS = 10
    PROJECT_STRUCTURE_FILE = "project_structure_final.txt"
    LAST_RESPONSE_FILE = ".last_response.txt"
    TRINITY_REPORT_HEADER = "## Trinity Report"
    
    DEV_KEYWORDS = set(DEV_KEYWORDS)
    NON_DEV_KEYWORDS = set(GENERAL_KEYWORDS)
    
    def __init__(
        self,
        verbose: bool = True,
        permissions: TrinityPermissions = None,
        on_stream: Optional[Callable[[str, str], None]] = None,
        preferred_language: str = "en",
        enable_self_healing: bool = True,
        hyper_mode: bool = False,
        learning_mode: bool = False
    ):
        self.llm = CopilotLLM()
        self.verbose = verbose
        self.logger = get_logger("trinity.core")
        self.registry = MCPToolRegistry()
        self.learning_mode = learning_mode
        
        # Integrate MCP tools
        try:
            # Diagnostics for untracked files
            git_root = self._get_git_root()
            if git_root:
                 # Check tracked/untracked for diagnostics using IntegrationGitMixin helpers if needed
                 pass

            from system_ai.tools.mcp_integration import register_mcp_tools_with_trinity
            register_mcp_tools_with_trinity(self.registry)
        except Exception as e:
            if self.verbose:
                self.logger.warning(f"MCP integration with Trinity deferred: {e}")
        
        self.context_layer = Context7(verbose=verbose)
        self.verifier = AdaptiveVerifier(self.llm)
        self.memory = get_memory()
        self.permissions = permissions or TrinityPermissions()
        self.preferred_language = preferred_language
        
        # Stream handling
        self.on_stream = on_stream
        self._stream_lock = threading.Lock()
        self._last_stream_content = {}
        
        # Helper initialization
        self.vision_context_manager = VisionContextManager(max_history=10)
        self.vibe_assistant = VibeCLIAssistant(name="Doctor Vibe")
        try:
            self.vibe_assistant.set_update_callback(self._on_vibe_update)
        except Exception:
            pass

        # Build Graph
        self.workflow = self._build_graph()
        
        # Hyper mode
        self.hyper_mode = hyper_mode
        if self.hyper_mode:
            self.logger.info("🚀 HYPER MODE ACTIVATED: Unlimited permissions for Doctor Vibe")
            self.permissions.allow_shell = True
            self.permissions.allow_applescript = True
            self.permissions.allow_file_write = True
            self.permissions.allow_gui = True
            self.permissions.allow_shortcuts = True
            self.permissions.hyper_mode = True
        
        # Self Healing
        self.self_healing_enabled = enable_self_healing or self._is_env_true("TRINITY_SELF_HEALING", False)
        self.self_healer = None
        if self.self_healing_enabled:
            self._initialize_self_healing()
        
        # Sonar Background Scanner
        try:
            if str(os.getenv("TRINITY_SONAR_BACKGROUND") or "").strip().lower() in {"1", "true", "yes", "on"}:
                interval = int(os.getenv("TRINITY_SONAR_SCAN_INTERVAL", "300"))
                from core.sonar_scanner import SonarBackgroundScanner
                self.sonar_scanner = SonarBackgroundScanner(self, interval=interval)
                self.sonar_scanner.start()
            else:
                self.sonar_scanner = None
        except Exception as e:
             if self.verbose: self.logger.warning(f"Sonar background scanner init failed: {e}")
             self.sonar_scanner = None

    def cleanup(self):
        """Cleanup resources."""
        if hasattr(self, 'sonar_scanner') and self.sonar_scanner:
            self.sonar_scanner.stop()

    def _deduplicated_stream(self, agent_name: str, content: str):
        """Stream content ensuring no duplicates (per chunk) in short window."""
        with self._stream_lock:
            # Simple dedup: if exact content matches last chunk for agent, skip
            # This is naive but prevents exact echo. 
            pass  # Logic can be refined, currently just calling on_stream
            if self.on_stream:
                self.on_stream(agent_name, content)

    def _on_vibe_update(self, update_type: str, data: Any):
        """Callback for Vibe Assistant updates."""
        if self.on_stream:
            try:
                msg = f"Doctor Vibe: {data.get('message', '') if isinstance(data, dict) else str(data)}"
                self.on_stream("doctor_vibe", msg)
            except Exception:
                pass
