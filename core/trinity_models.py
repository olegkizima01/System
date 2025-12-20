"""Pydantic models for Trinity state validation and type safety."""

from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, ConfigDict
from enum import Enum


class TaskType(str, Enum):
    """Allowed task types in Trinity."""
    DEV = "DEV"
    GENERAL = "GENERAL"
    UNKNOWN = "UNKNOWN"


class ExecutionMode(str, Enum):
    """Execution mode for Trinity."""
    NATIVE = "native"
    GUI = "gui"


class GuiMode(str, Enum):
    """GUI mode configuration."""
    OFF = "off"
    ON = "on"
    AUTO = "auto"


class StepStatus(str, Enum):
    """Status of a plan step."""
    SUCCESS = "success"
    FAILED = "failed"
    UNCERTAIN = "uncertain"


class MetaConfig(BaseModel):
    """Meta-planner configuration for Trinity execution strategy."""
    strategy: str = Field(default="hybrid", description="Execution strategy (linear|hybrid|rag_heavy)")
    verification_rigor: str = Field(default="standard", description="How strict to verify results (low|standard|high|strict)")
    recovery_mode: str = Field(default="local_fix", description="Recovery strategy (local_fix|full_replan)")
    tool_preference: str = Field(default="hybrid", description="Tool preference (hybrid|shell|gui|applescript)")
    reasoning: str = Field(default="", description="Reasoning for this strategy")
    retrieval_query: str = Field(default="", description="Query for RAG retrieval")
    n_results: int = Field(default=3, ge=1, le=10, description="Number of RAG results to retrieve")
    doctor_vibe_mode: Optional[str] = Field(default=None, description="Doctor Vibe mode (background|intervention|off)")

    model_config = ConfigDict(use_enum_values=False, validate_assignment=True)

    @field_validator('strategy')
    @classmethod
    def validate_strategy(cls, v: str) -> str:
        """Validate strategy value."""
        allowed = {"linear", "hybrid", "rag_heavy"}
        if v not in allowed:
            raise ValueError(f"strategy must be one of {allowed}, got {v}")
        return v

    @field_validator('verification_rigor')
    @classmethod
    def validate_rigor(cls, v: str) -> str:
        """Validate verification rigor value."""
        allowed = {"low", "standard", "high", "strict"}
        if v not in allowed:
            raise ValueError(f"verification_rigor must be one of {allowed}, got {v}")
        return v


class PlanStep(BaseModel):
    """A single step in the execution plan."""
    description: str = Field(description="Step description")
    action: Optional[str] = Field(default=None, description="Action to perform")
    expected_outcome: Optional[str] = Field(default=None, description="Expected result")
    fallback: Optional[str] = Field(default=None, description="Fallback action if primary fails")
    verification_method: Optional[str] = Field(default=None, description="How to verify step success")


class TrinityStateModel(BaseModel):
    """Pydantic model for Trinity system state with full validation."""
    
    # Messages and communication
    messages: List[Dict[str, Any]] = Field(default_factory=list, description="Conversation history")
    
    # Current execution state
    current_agent: str = Field(default="meta_planner", description="Current agent processing")
    task_status: str = Field(default="started", description="Task execution status")
    last_step_status: StepStatus = Field(default=StepStatus.SUCCESS, description="Status of last step")
    
    # Task planning
    plan: List[Dict[str, Any]] = Field(default_factory=list, description="Execution plan")
    step_count: int = Field(default=0, ge=0, description="Number of steps executed")
    replan_count: int = Field(default=0, ge=0, description="Number of replans")
    current_step_fail_count: int = Field(default=0, ge=0, description="Consecutive failures on current step")
    uncertain_streak: int = Field(default=0, ge=0, description="Consecutive uncertain decisions")
    
    # Results
    final_response: Optional[str] = Field(default=None, description="Final response to user")
    summary: Optional[str] = Field(default=None, description="Execution summary")
    
    # Task classification
    task_type: TaskType = Field(default=TaskType.UNKNOWN, description="Type of task (DEV|GENERAL|UNKNOWN)")
    original_task: Optional[str] = Field(default=None, description="Original user request")
    is_dev: bool = Field(default=False, description="Is this a dev task")
    is_media: bool = Field(default=False, description="Is this a media-related task")
    
    # Configuration
    gui_mode: GuiMode = Field(default=GuiMode.AUTO, description="GUI mode setting")
    execution_mode: ExecutionMode = Field(default=ExecutionMode.NATIVE, description="Execution mode")
    requires_windsurf: bool = Field(default=False, description="Requires Windsurf editor")
    dev_edit_mode: Optional[str] = Field(default="cli", description="Dev edit mode (windsurf|cli)")
    
    # Metadata and context
    intent_reason: Optional[str] = Field(default=None, description="Reason for task classification")
    meta_config: MetaConfig = Field(default_factory=MetaConfig, description="Meta-planner configuration")
    retrieved_context: str = Field(default="", description="Retrieved context from memory")
    vision_context: Optional[Dict[str, Any]] = Field(default=None, description="Visual context data")
    
    # Pause and pause state
    pause_info: Optional[Dict[str, Any]] = Field(default=None, description="Pause information")
    gui_fallback_attempted: bool = Field(default=False, description="Whether GUI fallback was attempted")
    
    # Vibe Assistant integration
    vibe_assistant_pause: Optional[Dict[str, Any]] = Field(default=None, description="Vibe Assistant pause state")
    vibe_assistant_context: str = Field(default="", description="Vibe Assistant context")
    
    # History and tracking
    history_plan_execution: List[str] = Field(default_factory=list, description="History of executed steps")
    forbidden_actions: List[str] = Field(default_factory=list, description="Actions that failed previously")
    
    model_config = ConfigDict(use_enum_values=True, validate_assignment=True, arbitrary_types_allowed=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for use with LangGraph."""
        return self.model_dump(by_alias=False, exclude_none=False)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "TrinityStateModel":
        """Create from dictionary, handling legacy formats."""
        # Handle enum conversions
        if "task_type" in data and isinstance(data["task_type"], str):
            try:
                data["task_type"] = TaskType[data["task_type"]]
            except KeyError:
                data["task_type"] = TaskType.UNKNOWN
        
        if "gui_mode" in data and isinstance(data["gui_mode"], str):
            try:
                data["gui_mode"] = GuiMode[data["gui_mode"].upper()]
            except KeyError:
                data["gui_mode"] = GuiMode.AUTO
        
        if "execution_mode" in data and isinstance(data["execution_mode"], str):
            try:
                data["execution_mode"] = ExecutionMode[data["execution_mode"].upper()]
            except KeyError:
                data["execution_mode"] = ExecutionMode.NATIVE
        
        if "last_step_status" in data and isinstance(data["last_step_status"], str):
            try:
                data["last_step_status"] = StepStatus[data["last_step_status"].upper()]
            except KeyError:
                data["last_step_status"] = StepStatus.SUCCESS
        
        # Handle meta_config
        if "meta_config" in data and isinstance(data["meta_config"], dict):
            data["meta_config"] = MetaConfig(**data["meta_config"])
        
        return TrinityStateModel(**data)

    def validate_state(self) -> bool:
        """Validate the state is in a valid configuration."""
        # Check that current_agent is a valid node
        valid_agents = {"meta_planner", "atlas", "tetyana", "grisha", "knowledge", "end"}
        if self.current_agent not in valid_agents:
            raise ValueError(f"current_agent must be one of {valid_agents}, got {self.current_agent}")
        
        # Check consistency
        if self.step_count < 0:
            raise ValueError("step_count cannot be negative")
        if self.replan_count < 0:
            raise ValueError("replan_count cannot be negative")
        
        return True
