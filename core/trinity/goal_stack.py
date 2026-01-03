"""
Recursive Goal Stack Management for Trinity Runtime.

Implements a stack-based goal decomposition system:
- When a subtask fails, it becomes the new main goal
- Failed goal is decomposed into sub-goals (e.g., 3 -> 3.1, 3.2, 3.3)
- On completion, returns to parent goal
- Proper tail-recursion without memory overhead

Example flow:
  Main Goal: "Open YouTube and search"
    └── Task 1: Open browser ✓
    └── Task 2: Navigate to YouTube ✓  
    └── Task 3: Search for video ✗ (fails)
        → Goal becomes 3, decomposed to:
        └── Task 3.1: Find search box ✓
        └── Task 3.2: Enter text ✗ (fails)
            → Goal becomes 3.2, decomposed to:
            └── Task 3.2.1: Click on search box ✓
            └── Task 3.2.2: Type text ✓
            └── Task 3.2.3: Press Enter ✓
            → Goal 3.2 complete, return to 3
        └── Task 3.3: Click search ✓
        → Goal 3 complete, return to Main
    └── Task 4: Verify results ✓
  → Main Goal complete!
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class Goal:
    """Represents a single goal in the stack."""
    id: str                           # e.g., "main", "3", "3.2", "3.2.1"
    description: str                  # Human-readable description
    parent_id: Optional[str] = None   # Parent goal ID
    subtasks: List[Dict[str, Any]] = field(default_factory=list)  # Decomposed subtasks
    current_subtask_idx: int = 0      # Current subtask index
    status: str = "pending"           # pending|in_progress|completed|failed
    fail_count: int = 0               # Number of failures at this level
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    error_context: Optional[str] = None  # Context about why it failed

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for state serialization."""
        return {
            "id": self.id,
            "description": self.description,
            "parent_id": self.parent_id,
            "subtasks": self.subtasks,
            "current_subtask_idx": self.current_subtask_idx,
            "status": self.status,
            "fail_count": self.fail_count,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "error_context": self.error_context,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Goal":
        """Create Goal from dictionary."""
        return cls(
            id=data["id"],
            description=data["description"],
            parent_id=data.get("parent_id"),
            subtasks=data.get("subtasks", []),
            current_subtask_idx=data.get("current_subtask_idx", 0),
            status=data.get("status", "pending"),
            fail_count=data.get("fail_count", 0),
            created_at=data.get("created_at", datetime.now().isoformat()),
            completed_at=data.get("completed_at"),
            error_context=data.get("error_context"),
        )


class GoalStack:
    """
    Stack-based goal management with recursive decomposition.
    
    Key principles:
    1. Goals form a tree but are processed as a stack (LIFO)
    2. When a task fails, it's decomposed into subtasks
    3. Subtasks become the new focus until completed
    4. On completion, control returns to parent goal
    5. No deep recursion - purely iterative with explicit stack
    """
    
    MAX_DEPTH = 5       # Maximum nesting depth (main -> 3 -> 3.2 -> 3.2.1 -> 3.2.1.1)
    MAX_SUBTASKS = 5    # Maximum subtasks per decomposition
    MAX_RETRIES = 3     # Maximum retries before decomposition
    
    def __init__(self, initial_goal: Optional[str] = None):
        self._stack: List[Goal] = []
        self._history: List[Dict[str, Any]] = []  # Completed goals for learning
        
        if initial_goal:
            self.push_goal("main", initial_goal)
    
    @property
    def depth(self) -> int:
        """Current stack depth."""
        return len(self._stack)
    
    @property
    def current_goal(self) -> Optional[Goal]:
        """Get the current active goal (top of stack)."""
        return self._stack[-1] if self._stack else None
    
    @property
    def is_empty(self) -> bool:
        """Check if goal stack is empty (all goals completed)."""
        return len(self._stack) == 0
    
    @property
    def current_goal_id(self) -> str:
        """Get current goal ID for display."""
        return self.current_goal.id if self.current_goal else "none"
    
    def push_goal(self, goal_id: str, description: str, parent_id: Optional[str] = None) -> Goal:
        """Push a new goal onto the stack."""
        goal = Goal(
            id=goal_id,
            description=description,
            parent_id=parent_id,
            status="in_progress"
        )
        self._stack.append(goal)
        return goal
    
    def pop_goal(self) -> Optional[Goal]:
        """Pop and return the current goal (marks as completed)."""
        if not self._stack:
            return None
        
        goal = self._stack.pop()
        goal.status = "completed"
        goal.completed_at = datetime.now().isoformat()
        self._history.append(goal.to_dict())
        return goal
    
    def get_goal_path(self) -> str:
        """Get the full path of current goals (e.g., 'main > 3 > 3.2')."""
        return " > ".join(g.id for g in self._stack)
    
    def decompose_current_goal(self, subtasks: List[Dict[str, Any]], error_context: str = "") -> bool:
        """
        Decompose current failing goal into subtasks.
        
        Args:
            subtasks: List of subtask dicts with 'description' key
            error_context: Why the goal failed (for learning)
            
        Returns:
            True if decomposition happened, False if max depth reached
        """
        if not self.current_goal:
            return False
        
        # Check depth limit
        if self.depth >= self.MAX_DEPTH:
            return False
        
        # Limit subtasks
        subtasks = subtasks[:self.MAX_SUBTASKS]
        if not subtasks:
            return False
        
        current = self.current_goal
        current.error_context = error_context
        current.subtasks = subtasks
        current.status = "decomposed"
        
        # Generate subtask IDs
        base_id = current.id
        if base_id == "main":
            base_id = ""
        
        # Push first subtask onto stack (others will be pushed as we complete)
        # We only push the FIRST subtask to start
        first_subtask = subtasks[0]
        subtask_id = f"{base_id}.1" if base_id else "1"
        
        self.push_goal(
            goal_id=subtask_id,
            description=first_subtask.get("description", f"Subtask {subtask_id}"),
            parent_id=current.id
        )
        
        return True
    
    def complete_current_subtask(self) -> Optional[str]:
        """
        Mark current subtask as complete and move to next.
        
        Returns:
            - "next_subtask" if there are more subtasks
            - "parent_complete" if parent goal is now complete
            - "all_complete" if main goal is complete
            - None if error
        """
        if not self.current_goal:
            return None
        
        completed = self.pop_goal()
        if not completed:
            return None
        
        # Check if there's a parent
        if not self._stack:
            # Main goal completed!
            return "all_complete"
        
        parent = self.current_goal
        
        # Move to next subtask in parent
        parent.current_subtask_idx += 1
        
        if parent.current_subtask_idx < len(parent.subtasks):
            # Push next subtask
            next_subtask = parent.subtasks[parent.current_subtask_idx]
            
            # Generate subtask ID
            base_id = parent.id
            if base_id == "main":
                base_id = ""
            idx = parent.current_subtask_idx + 1
            subtask_id = f"{base_id}.{idx}" if base_id else str(idx)
            
            self.push_goal(
                goal_id=subtask_id,
                description=next_subtask.get("description", f"Subtask {subtask_id}"),
                parent_id=parent.id
            )
            return "next_subtask"
        else:
            # All subtasks of parent complete - parent is now complete too
            # Recursively complete the parent
            return self.complete_current_subtask()
    
    def handle_failure(self, error_context: str = "") -> str:
        """
        Handle a failure at the current goal level.
        
        Returns:
            - "retry" if we should retry the same goal
            - "decompose" if we should decompose into subtasks
            - "abort" if max depth reached, should fail gracefully
        """
        if not self.current_goal:
            return "abort"
        
        goal = self.current_goal
        goal.fail_count += 1
        goal.error_context = error_context
        
        # Check if we should retry
        if goal.fail_count < self.MAX_RETRIES:
            return "retry"
        
        # Check if we can decompose (depth limit)
        if self.depth >= self.MAX_DEPTH:
            return "abort"
        
        return "decompose"
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize the entire goal stack to dict."""
        return {
            "stack": [g.to_dict() for g in self._stack],
            "history": self._history,
            "depth": self.depth,
            "current_goal_id": self.current_goal_id,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GoalStack":
        """Deserialize goal stack from dict."""
        stack = cls()
        stack._stack = [Goal.from_dict(g) for g in data.get("stack", [])]
        stack._history = data.get("history", [])
        return stack
    
    def get_status_summary(self) -> str:
        """Get a human-readable status summary."""
        if not self._stack:
            return "✅ Всі цілі виконані"
        
        lines = [f"📍 Шлях цілей: {self.get_goal_path()}"]
        lines.append(f"📊 Глибина: {self.depth}/{self.MAX_DEPTH}")
        
        if self.current_goal:
            g = self.current_goal
            lines.append(f"🎯 Поточна ціль [{g.id}]: {g.description}")
            if g.fail_count > 0:
                lines.append(f"   ⚠️ Спроб: {g.fail_count}/{self.MAX_RETRIES}")
            if g.subtasks:
                lines.append(f"   📝 Підзавдань: {g.current_subtask_idx + 1}/{len(g.subtasks)}")
        
        return "\n".join(lines)
    
    def __repr__(self) -> str:
        return f"GoalStack(depth={self.depth}, current={self.current_goal_id})"


def generate_subtask_decomposition(
    goal_description: str,
    error_context: str,
    num_subtasks: int = 3
) -> List[Dict[str, Any]]:
    """
    Generate subtask decomposition for a failed goal.
    
    This is a placeholder - in production this would call the LLM
    to intelligently decompose the failed task.
    
    Args:
        goal_description: What we were trying to do
        error_context: Why it failed
        num_subtasks: How many subtasks to generate
        
    Returns:
        List of subtask dicts with 'description' key
    """
    # In production, this would use Atlas/LLM to decompose
    # For now, return generic breakdown
    return [
        {"description": f"Крок {i+1} для: {goal_description[:50]}..."}
        for i in range(num_subtasks)
    ]
