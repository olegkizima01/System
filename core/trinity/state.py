"""
Trinity state definitions and permissions.

This module contains the core state types for the Trinity runtime:
- TrinityPermissions: Permission flags for system actions
- TrinityState: TypedDict defining the full graph state schema
"""

from typing import TypedDict, List, Dict, Any, Optional
from dataclasses import dataclass
import os

from langchain_core.messages import BaseMessage


@dataclass
class TrinityPermissions:
    """Permission flags for Trinity system actions.
    
    These flags control what actions the Trinity runtime is allowed to perform.
    Can be set programmatically or via environment variables.
    
    Environment Variables:
        TRINITY_ALLOW_SHELL: Allow shell command execution
        TRINITY_ALLOW_APPLESCRIPT: Allow AppleScript execution
        TRINITY_ALLOW_WRITE: Allow file write operations
        TRINITY_ALLOW_GUI: Allow GUI automation
        TRINITY_ALLOW_SHORTCUTS: Allow macOS Shortcuts execution
        TRINITY_HYPER_MODE: Enable all permissions (Doctor Vibe mode)
    
    Example:
        ```python
        # Programmatic
        perms = TrinityPermissions(allow_shell=True, allow_gui=True)
        
        # Environment-based
        os.environ["TRINITY_ALLOW_SHELL"] = "true"
        perms = TrinityPermissions()  # Will pick up env var
        ```
    """
    allow_shell: bool = False
    allow_applescript: bool = False
    allow_file_write: bool = False
    allow_gui: bool = False
    allow_shortcuts: bool = False
    hyper_mode: bool = False  # Automation without confirmation

    def __post_init__(self):
        """Allow environment overrides for all permission flags."""
        def _is_env_true(var: str, default: bool) -> bool:
            val = str(os.getenv(var) or "").strip().lower()
            if not val:
                return default
            return val in {"1", "true", "yes", "on"}

        self.allow_shell = _is_env_true("TRINITY_ALLOW_SHELL", self.allow_shell)
        self.allow_applescript = _is_env_true("TRINITY_ALLOW_APPLESCRIPT", self.allow_applescript)
        self.allow_file_write = _is_env_true("TRINITY_ALLOW_WRITE", self.allow_file_write)
        self.allow_gui = _is_env_true("TRINITY_ALLOW_GUI", self.allow_gui)
        self.allow_shortcuts = _is_env_true("TRINITY_ALLOW_SHORTCUTS", self.allow_shortcuts)
        self.hyper_mode = _is_env_true("TRINITY_HYPER_MODE", self.hyper_mode)
    
    def to_dict(self) -> Dict[str, bool]:
        """Convert permissions to dictionary."""
        return {
            "allow_shell": self.allow_shell,
            "allow_applescript": self.allow_applescript,
            "allow_file_write": self.allow_file_write,
            "allow_gui": self.allow_gui,
            "allow_shortcuts": self.allow_shortcuts,
            "hyper_mode": self.hyper_mode,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, bool]) -> "TrinityPermissions":
        """Create permissions from dictionary."""
        return cls(
            allow_shell=data.get("allow_shell", False),
            allow_applescript=data.get("allow_applescript", False),
            allow_file_write=data.get("allow_file_write", False),
            allow_gui=data.get("allow_gui", False),
            allow_shortcuts=data.get("allow_shortcuts", False),
            hyper_mode=data.get("hyper_mode", False),
        )
    
    def enable_all(self) -> "TrinityPermissions":
        """Enable all permissions (for testing/hyper mode)."""
        self.allow_shell = True
        self.allow_applescript = True
        self.allow_file_write = True
        self.allow_gui = True
        self.allow_shortcuts = True
        self.hyper_mode = True
        return self


class TrinityState(TypedDict, total=False):
    """State schema for Trinity graph execution.
    
    This TypedDict defines all fields that can be present in the Trinity
    runtime state. The state is passed between graph nodes and represents
    the current execution context.
    
    Core Fields:
        messages: List of conversation messages (LangChain format)
        current_agent: Currently active agent (meta_planner, atlas, tetyana, grisha)
        task_status: Overall task status (pending, in_progress, completed, failed)
        final_response: Final response to user when task completes
        
    Planning Fields:
        plan: List of plan steps (each step is a dict)
        summary: Periodic execution summary
        step_count: Number of steps executed
        replan_count: Number of replanning iterations
        
    Execution Fields:
        pause_info: Permission pause information
        gui_mode: GUI automation mode (off|on|auto)
        execution_mode: Execution strategy (native|gui)
        gui_fallback_attempted: Whether GUI fallback was tried
        
    Task Classification:
        task_type: DEV|GENERAL|UNKNOWN
        is_dev: Whether task is development-related
        is_media: Whether task involves media (video, audio)
        requires_windsurf: Whether Windsurf IDE is needed
        dev_edit_mode: windsurf|cli
        intent_reason: Reasoning for classification
        original_task: The original user request (Golden Goal)
        
    Progress Tracking:
        last_step_status: success|failed|uncertain
        uncertain_streak: Consecutive uncertain decisions (anti-loop)
        current_step_fail_count: Consecutive failures on current step
        
    Meta-Planning:
        meta_config: Strategy config (strategy, verification_rigor, recovery_mode, etc.)
        retrieved_context: Structured findings from RAG
        
    Assistant Integration:
        vibe_assistant_pause: Vibe CLI Assistant pause state
        vibe_assistant_context: Context for Vibe CLI Assistant
        
    Vision:
        vision_context: Enhanced visual context from differential analysis
        
    Learning:
        learning_mode: Whether learning/experience extraction is enabled
    """
    # Core fields
    messages: List[BaseMessage]
    current_agent: str
    task_status: str
    final_response: Optional[str]
    
    # Planning
    plan: Optional[List[Dict[str, Any]]]
    summary: Optional[str]
    step_count: int
    replan_count: int
    
    # Execution control
    pause_info: Optional[Dict[str, Any]]
    gui_mode: Optional[str]
    execution_mode: Optional[str]
    gui_fallback_attempted: Optional[bool]
    
    # Task classification
    task_type: Optional[str]
    is_dev: Optional[bool]
    is_media: Optional[bool]
    requires_windsurf: Optional[bool]
    dev_edit_mode: Optional[str]
    intent_reason: Optional[str]
    original_task: Optional[str]
    
    # Progress tracking
    last_step_status: Optional[str]
    uncertain_streak: Optional[int]
    current_step_fail_count: Optional[int]
    
    # Meta-planning
    meta_config: Optional[Dict[str, Any]]
    retrieved_context: Optional[str]
    
    # Assistant integration
    vibe_assistant_pause: Optional[Dict[str, Any]]
    vibe_assistant_context: Optional[str]
    
    # Vision
    vision_context: Optional[Dict[str, Any]]
    
    # Learning
    learning_mode: Optional[bool]
    
    # Recursive Goal Stack (for proper task decomposition)
    goal_stack: Optional[Dict[str, Any]]  # Serialized GoalStack
    goal_stack_action: Optional[str]  # retry|decompose|complete|abort


def create_initial_state(
    task: str,
    task_type: str = "UNKNOWN",
    is_dev: bool = False,
    is_media: bool = False,
    gui_mode: str = "auto",
    execution_mode: str = "native",
    learning_mode: bool = False,
) -> TrinityState:
    """Create a properly initialized Trinity state.
    
    This factory function ensures all required fields have safe defaults.
    
    Args:
        task: The user's task/request
        task_type: DEV, GENERAL, or UNKNOWN
        is_dev: Whether this is a development task
        is_media: Whether this involves media
        gui_mode: GUI automation mode (off|on|auto)
        execution_mode: Execution strategy (native|gui)
        learning_mode: Whether to enable learning
        
    Returns:
        Properly initialized TrinityState
    """
    from langchain_core.messages import HumanMessage
    
    return TrinityState(
        messages=[HumanMessage(content=task)],
        current_agent="meta_planner",  # Always start with meta_planner
        task_status="pending",
        final_response=None,
        plan=None,
        summary=None,
        step_count=0,
        replan_count=0,
        pause_info=None,
        gui_mode=gui_mode,
        execution_mode=execution_mode,
        gui_fallback_attempted=False,
        task_type=task_type,
        is_dev=is_dev,
        is_media=is_media,
        requires_windsurf=False,
        dev_edit_mode=None,
        intent_reason=None,
        original_task=task,
        last_step_status=None,
        uncertain_streak=0,
        current_step_fail_count=0,
        meta_config={
            "strategy": "hybrid",
            "verification_rigor": "standard",
            "recovery_mode": "local_fix",
            "tool_preference": "hybrid",
            "reasoning": "",
            "retrieval_query": task[:100] if task else "",
            "n_results": 3,
        },
        retrieved_context=None,
        vibe_assistant_pause=None,
        vibe_assistant_context=None,
        vision_context=None,
        learning_mode=learning_mode,
        goal_stack=None,  # Will be initialized by GoalStack
        goal_stack_action=None,
    )
