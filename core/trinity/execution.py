import os
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from langchain_core.messages import AIMessage, BaseMessage
from langgraph.graph import StateGraph, END
from core.trinity.state import TrinityState
from core.trinity.goal_stack import GoalStack, Goal
from core.constants import VOICE_MARKER, UNKNOWN_STEP
from core.trinity.nodes.vibe import vibe_analyst_node
from tui.logger import trace

class TrinityExecutionMixin:
    """Mixin for TrinityRuntime containing Graph construction and execution routing."""

    def _build_graph(self):
        """Constructs the Trinity StateGraph."""
        workflow = StateGraph(TrinityState)

        # Add Nodes (methods must be available via mixins)
        workflow.add_node("meta_planner", self._meta_planner_node)
        workflow.add_node("atlas", self._atlas_node)
        workflow.add_node("tetyana", self._tetyana_node)
        workflow.add_node("grisha", self._grisha_node)
        workflow.add_node("knowledge", self._knowledge_node)
        workflow.add_node("vibe", vibe_analyst_node)

        # Set Entry Point
        workflow.set_entry_point("meta_planner")

        # Add Edges
        workflow.add_edge("atlas", "tetyana")
        workflow.add_edge("tetyana", "grisha")
        # Route knowledge -> vibe -> END
        workflow.add_edge("knowledge", "vibe")
        workflow.add_edge("vibe", END)

        workflow.add_conditional_edges(
            "meta_planner",
            self._meta_router,
            {"atlas": "atlas", "end": "knowledge"}
        )
        workflow.add_conditional_edges(
            "grisha",
            self._router,
            {"meta_planner": "meta_planner", "knowledge": "knowledge", "end": "knowledge"} 
        )

        return workflow.compile()

    def _meta_router(self, state: TrinityState):
        """Routing logic from Meta-Planner."""
        # Simple routing: if finished -> knowledge/end, else atlas
        current = state.get("current_agent")
        if current == "end":
            return "end"
        return "atlas"

    def _router(self, state: TrinityState):
        """Main routing logic after Grisha (Verifier).
        
        Uses GoalStack for proper recursive task decomposition:
        - When a task fails, it becomes a sub-goal
        - Sub-goal is decomposed into smaller steps
        - On completion, returns to parent goal
        """
        replan_count = state.get("replan_count") or 0
        step_count = state.get("step_count") or 0
        last_status = state.get("last_step_status")
        
        # Initialize or restore GoalStack
        goal_stack = self._get_goal_stack(state)
        
        # CRITICAL: Anti-recursion protection
        if step_count >= self.MAX_STEPS:
            if self.verbose:
                print(f"⚠️ [Router] MAX_STEPS ({self.MAX_STEPS}) reached, forcing completion")
            return "knowledge"
        
        if replan_count >= self.MAX_REPLANS:
            if self.verbose:
                print(f"⚠️ [Router] MAX_REPLANS ({self.MAX_REPLANS}) reached, forcing completion")
            return "knowledge"
        
        # Check goal stack depth limit
        if goal_stack and goal_stack.depth >= GoalStack.MAX_DEPTH:
            if self.verbose:
                print(f"⚠️ [Router] Goal stack depth limit reached ({goal_stack.depth})")
            return "knowledge"
        
        # 1. Handle Doctor Vibe Pauses (Interventions)
        pause = state.get("vibe_assistant_pause")
        if pause:
            return self._handle_existing_pause(state, pause)

        # 2. Check for manual intervention request (from last message)
        intervention = self._handle_new_intervention(state)
        if intervention:
            return intervention

        # 3. Handle Failures with Goal Stack decomposition
        if last_status == "failed":
            return self._handle_failure_with_goal_stack(state, goal_stack, replan_count)

        # 4. Handle Uncertainty (Loop protection)
        if last_status == "uncertain":
            if state.get("uncertain_streak", 0) >= 3:
                if replan_count >= 3:
                    if self.verbose:
                        print(f"⚠️ [Router] Uncertain + many replans, forcing completion")
                    return "knowledge"
                return "meta_planner"
            return "meta_planner"

        # 5. Success - Handle goal completion with stack
        return self._handle_success_with_goal_stack(state, goal_stack, step_count)

    def _get_goal_stack(self, state: TrinityState) -> GoalStack:
        """Get or create GoalStack from state."""
        stack_data = state.get("goal_stack")
        if stack_data:
            return GoalStack.from_dict(stack_data)
        
        # Initialize with main goal
        original_task = state.get("original_task", "Unknown task")
        return GoalStack(initial_goal=original_task)

    def _handle_failure_with_goal_stack(
        self, 
        state: TrinityState, 
        goal_stack: GoalStack, 
        replan_count: int
    ) -> str:
        """
        Handle task failure using GoalStack for proper recursion.
        
        Flow:
        1. Try retry if under limit
        2. Decompose goal into subtasks if retry limit hit
        3. Abort if max depth reached
        """
        # Get error context from last message
        error_context = self._extract_error_context(state)
        
        # Let GoalStack decide what to do
        action = goal_stack.handle_failure(error_context)
        
        if self.verbose:
            print(f"🔄 [GoalStack] Failure action: {action}")
            print(f"   {goal_stack.get_status_summary()}")
        
        if action == "retry":
            # Simple retry - go back to meta_planner
            if self.verbose:
                print(f"   ↻ Retry #{goal_stack.current_goal.fail_count}")
            return "meta_planner"
        
        elif action == "decompose":
            # Decompose current goal into subtasks
            # This will be handled by meta_planner with decomposition context
            if self.verbose:
                print(f"   🔀 Decomposing goal into subtasks...")
            
            # Mark that decomposition is needed
            state["goal_stack_action"] = "decompose"
            state["goal_stack"] = goal_stack.to_dict()
            return "meta_planner"
        
        else:  # abort
            # Max depth reached, force completion
            if replan_count >= 5:
                if self.verbose:
                    print(f"⚠️ [Router] Goal stack abort + too many replans, forcing completion")
                return "knowledge"
            
            # Try one more replan before giving up
            return "meta_planner"

    def _handle_success_with_goal_stack(
        self, 
        state: TrinityState, 
        goal_stack: GoalStack, 
        step_count: int
    ) -> str:
        """
        Handle successful step completion with goal stack.
        
        Flow:
        1. Mark current subtask as complete
        2. Move to next subtask or return to parent
        3. Check if all goals are complete
        """
        # Complete current goal/subtask
        result = goal_stack.complete_current_subtask()
        
        if self.verbose:
            print(f"✅ [GoalStack] Completion result: {result}")
            if not goal_stack.is_empty:
                print(f"   {goal_stack.get_status_summary()}")
        
        if result == "all_complete":
            # All goals done!
            return "knowledge"
        
        elif result == "parent_complete":
            # Parent goal completed, check recursively
            # GoalStack handles this internally
            return self._check_knowledge_transition(state, step_count)
        
        elif result == "next_subtask":
            # Move to next subtask
            state["goal_stack"] = goal_stack.to_dict()
            return "meta_planner"
        
        # Default: check for knowledge transition
        return self._check_knowledge_transition(state, step_count)

    def _extract_error_context(self, state: TrinityState) -> str:
        """Extract error context from state messages."""
        messages = state.get("messages", [])
        if not messages:
            return "Unknown error"
        
        last_msg = messages[-1]
        content = getattr(last_msg, 'content', str(last_msg))
        
        # Extract error indicators
        if isinstance(content, str):
            if "error" in content.lower() or "failed" in content.lower():
                return content[:500]  # Truncate long errors
        
        return "Step failed without specific error"

    def _create_vibe_assistant_pause_state(self, state: TrinityState, pause_reason: str, message: str) -> Dict[str, Any]:
        """Create a pause state for Vibe CLI Assistant intervention."""
        # Use simple dict instead of TrinityState for the pause_info itself to avoid recursion
        pause_info = {
            "reason": pause_reason,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "status": "awaiting_human_input"
        }
        
        if state.get("original_task"):
            pause_info["original_task"] = state["original_task"]
        
        # Attach diagnostics
        try:
            diags = self._collect_pause_diagnostics(state)
            if diags:
                pause_info["diagnostics"] = diags
        except Exception:
            pass
        
        # Notify Vibe Assistant
        if hasattr(self, 'vibe_assistant'):
            try:
                self.vibe_assistant.handle_pause_request(pause_info)
            except Exception:
                pass
        
        return pause_info

    def _collect_pause_diagnostics(self, state: TrinityState, tools: Optional[list] = None) -> Dict[str, Any]:
        """Collect truncated diagnostics for a Vibe pause."""
        diagnostics = {"files": [], "diffs": [], "tools": tools or [], "stack_trace": None}
        # Best-effort collection
        try:
            if hasattr(self, '_get_repo_changes'):
                changes = self._get_repo_changes()
                if isinstance(changes, dict) and "changed_files" in changes:
                    diagnostics["files"] = list(changes["changed_files"])[:5]
            
            # Add sonar info if available
            if hasattr(self, '_fetch_sonar_issues'):
                sonar = self._fetch_sonar_issues()
                if sonar and "error" not in sonar:
                    diagnostics["sonar"] = sonar
        except Exception:
            pass
        return diagnostics

    def _handle_existing_pause(self, state, pause):
        """Handle execution when a pause state is active."""
        # Check if pause is resolved? (Runtime loop usually handles waiting)
        # But if we are here, we might need to route.
        # Actually, if we are paused, we shouldn't be stepping effectively unless resume happened.
        # If we are routed here with a pause, we probably loop back to meta_planner 
        # but the runtime loop will stop execution.
        return "meta_planner" 

    def _handle_new_intervention(self, state):
        """Check if user/messages requested intervention."""
        messages = state.get("messages", [])
        if not messages: return None
        last_content = messages[-1].content
        last_msg_str = str(last_content) if not isinstance(last_content, str) else last_content
        last_msg = last_msg_str.lower()
        if "pause" in last_msg or "doctor vibe" in last_msg:
             # This might trigger a pause in next step
             return "meta_planner"
        return None

    def _try_auto_repair(self, state, replan_count):
        """Logic to attempt auto-repair or return None."""
        # If fail count is high, we go to meta_planner which handles replanning logic.
        return "meta_planner"

    def _check_knowledge_transition(self, state, step_count):
        """Decide if we transition to Knowledge (End) or Continue."""
        # If plan empty and goal achieved -> knowledge
        plan = state.get("plan")
        if not plan:
            return "knowledge"
        
        # If steps maxed out -> knowledge (forced end)
        if step_count >= getattr(self, "MAX_STEPS", 50):
            return "knowledge"
            
        return "meta_planner"
