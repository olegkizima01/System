import os
import threading
import subprocess
import time
from typing import Optional, Callable, Dict, Any, List, Generator
from datetime import datetime

from core.trinity.state import TrinityState, TrinityPermissions
from core.memory import get_memory
from core.context7 import Context7
from core.verification import AdaptiveVerifier
from core.mcp_registry import MCPToolRegistry
from core.vision_context import VisionContextManager
from core.vibe_assistant import VibeCLIAssistant
from tui.logger import get_logger, trace
from providers.copilot import CopilotLLM
from core.state_logger import log_initial_state, log_state_transition
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

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
        self.preferred_language = preferred_language
        
        # Integrate MCP tools
        try:
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

        # Register custom tools (vision, window detection, etc.)
        self._register_tools()

        # Build Graph
        self.workflow = self._build_graph()
        
        # Execution tracing
        self.execution_trace = []
        self.max_execution_steps = 100  # Safety limit
        self.enable_execution_tracing = verbose
        
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

        # ChromaDB health check and recovery
        try:
            from core.memory import get_memory as get_memory_func
            memory = get_memory_func()
            if hasattr(memory, 'check_chroma_health'):
                health_status = memory.check_chroma_health()
                if not health_status.get('healthy', True):
                    if self.verbose:
                        self.logger.warning(f"ChromaDB health check failed: {health_status.get('error', 'Unknown error')}")
                    # Attempt recovery
                    if hasattr(memory, 'recover_chroma'):
                        recovery_result = memory.recover_chroma()
                        if self.verbose:
                            if recovery_result.get('success'):
                                self.logger.info("ChromaDB recovery successful")
                            else:
                                self.logger.warning(f"ChromaDB recovery failed: {recovery_result.get('error', 'Unknown error')}")
        except Exception as e:
            if self.verbose:
                self.logger.debug(f"ChromaDB health check failed (non-critical): {e}")

    def _is_env_true(self, var: str, default: bool) -> bool:
        val = str(os.getenv(var) or "").strip().lower()
        if not val: return default
        return val in {"1", "true", "yes", "on"}

    def cleanup(self):
        """Cleanup resources."""
        if hasattr(self, 'sonar_scanner') and self.sonar_scanner:
            self.sonar_scanner.stop()
    
    def get_execution_trace(self) -> List[Dict[str, Any]]:
        """Get the execution trace for debugging"""
        return self.execution_trace
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Get execution statistics"""
        if not self.execution_trace:
            return {'steps': 0, 'agents': {}, 'duration': 0}
        
        stats = {
            'steps': len(self.execution_trace),
            'agents': {},
            'duration': 0
        }
        
        # Count agent transitions
        for step in self.execution_trace:
            agent = step.get('agent')
            if agent:
                stats['agents'][agent] = stats['agents'].get(agent, 0) + 1
        
        # Calculate duration if we have timestamps
        if len(self.execution_trace) > 1:
            try:
                start_time = datetime.fromisoformat(self.execution_trace[0]['timestamp'])
                end_time = datetime.fromisoformat(self.execution_trace[-1]['timestamp'])
                stats['duration'] = (end_time - start_time).total_seconds()
            except:
                pass
        
        return stats

    def _deduplicated_stream(self, agent_name: str, content: str):
        """Stream content ensuring no duplicates (per chunk) in short window."""
        with self._stream_lock:
            # Simple dedup: if exact content matches last chunk for agent, skip
            last = self._last_stream_content.get(agent_name, "")
            if content == last or (len(content) < len(last) and last.startswith(content)):
                return
            self._last_stream_content[agent_name] = content
            if self.on_stream:
                self.on_stream(agent_name, content)

    def _on_vibe_update(self, update_type: str, data: Any = None):
        """Callback for Vibe Assistant updates."""
        if self.on_stream:
            try:
                # Handle both string messages and dict data
                if isinstance(update_type, str) and data is None:
                    msg = update_type
                else:
                    msg = f"Doctor Vibe: {data.get('message', '') if isinstance(data, dict) else str(data)}"
                self.on_stream("doctor_vibe", msg)
            except Exception:
                pass

    def run(self, task: str, gui_mode: str = "auto", execution_mode: str = "native", recursion_limit: int = 200) -> Generator[Dict[str, Any], None, None]:
        """Core execution loop using the LangGraph workflow."""
        # Reset execution trace
        self.execution_trace = []
        
        # Safety checks
        self._check_safety_limits = True
        self._execution_start_time = time.time()
        
        # 1. Classify task
        task_type, is_dev, is_media = self._classify_task(task)
        
        state = {
            "messages": [HumanMessage(content=task)],
            "original_task": task,
            "current_agent": "meta_planner",
            "task_status": "pending",
            "step_count": 0,
            "replan_count": 0,
            "gui_mode": gui_mode,
            "execution_mode": execution_mode,
            "last_step_status": "success",
            "uncertain_streak": 0,
            "current_step_fail_count": 0,
            "history_plan_execution": [],
            "plan": [],
            "task_type": task_type,
            "is_dev": is_dev,
            "is_media": is_media,
            "is_media": is_media,
            "requires_windsurf": False 
        }

        # Log initial state
        log_initial_state(task, state)

        try:
            for event in self.workflow.stream(state, config={"recursion_limit": recursion_limit}):
                # Safety timeout check
                current_time = time.time()
                execution_time = current_time - self._execution_start_time
                
                if self._check_safety_limits and execution_time > 60:  # 60 second timeout
                    if self.verbose:
                        self.logger.warning(f"Execution timeout reached: {execution_time:.1f}s > 60s")
                    
                    # Force completion
                    final_state = {
                        **state,
                        "current_agent": "end",
                        "task_status": "completed",
                        "final_response": "Task completed (safety timeout)"
                    }
                    self._handle_post_task_completion(task, final_state)
                    yield final_state
                    break
                
                # Log execution step
                for node_name, node_state in event.items():
                    agent = node_state.get("current_agent")
                    if agent:
                        self._log_execution_step(agent, node_state)
                    
                    # Process post-completion hooks if needed
                    step = node_state.get("step_count", 0)
                    status = node_state.get("last_step_status", "unknown")
                    # We log that node_name just finished
                    log_state_transition(
                        from_agent="trinity", # Graph step
                        to_agent=node_name,
                        step_count=step,
                        last_status=status
                    )

                    if node_name == "knowledge" or node_state.get("current_agent") == "end":
                        self._handle_post_task_completion(task, node_state)
                yield event
        except Exception as e:
            self.logger.error(f"Runtime workflow error: {e}")
            raise

    def _log_execution_step(self, step_name: str, state: Dict[str, Any]):
        """Log execution steps for debugging and tracing"""
        if not self.enable_execution_tracing:
            return
        
        plan = state.get('plan')
        plan_length = len(plan) if plan is not None else 0
        
        step_info = {
            'timestamp': datetime.now().isoformat(),
            'step': step_name,
            'agent': state.get('current_agent'),
            'step_count': state.get('step_count', 0),
            'replan_count': state.get('replan_count', 0),
            'plan_length': plan_length,
            'last_status': state.get('last_step_status')
        }
        
        self.execution_trace.append(step_info)
        
        # Safety check for infinite loops
        if len(self.execution_trace) >= self.max_execution_steps:
            if self.verbose:
                print(f"⚠️  Maximum execution steps reached: {self.max_execution_steps}")
            return
        
        # Periodic logging
        if len(self.execution_trace) % 10 == 0 and self.verbose:
            print(f"🔄 Execution trace: {len(self.execution_trace)} steps")

    def _handle_post_task_completion(self, task: str, state: Dict[str, Any]):
        """Runs auto-commit and other cleanup after successful task."""
        try:
            last_msg = ""
            messages = state.get("messages", [])
            if messages:
                last_msg = getattr(messages[-1], "content", "")
            
            # 1. Regenerate structure
            self._regenerate_project_structure(last_msg)
            
            # 2. Auto-commit
            repo_changes = self._get_repo_changes()
            if repo_changes.get("ok"):
                self._auto_commit_on_success(task=task, report=last_msg, repo_changes=repo_changes)
        except Exception as e:
            self.logger.warning(f"Post-task hooks failed: {e}")

