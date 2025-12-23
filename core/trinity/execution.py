import os
from typing import Dict, Any, List, Optional
from langchain_core.messages import AIMessage, BaseMessage
from langgraph.graph import StateGraph, END
from core.trinity.state import TrinityState
from core.constants import VOICE_MARKER, UNKNOWN_STEP
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

        # Set Entry Point
        workflow.set_entry_point("meta_planner")

        # Add Edges
        workflow.add_edge("atlas", "tetyana")
        workflow.add_edge("tetyana", "grisha")
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
        """Main routing logic after Grisha (Verifier)."""
        replan_count = state.get("replan_count") or 0
        step_count = state.get("step_count") or 0
        last_status = state.get("last_step_status")
        
        # 1. Handle Doctor Vibe Pauses (Interventions)
        pause = state.get("vibe_assistant_pause")
        if pause:
            return self._handle_existing_pause(state, pause)

        # 2. Check for manual intervention request (from last message)
        intervention = self._handle_new_intervention(state)
        if intervention:
            return intervention

        # 3. Handle Failures & Repairs
        if last_status == "failed":
            repair_node = self._try_auto_repair(state, replan_count)
            if repair_node: return repair_node
            # Default to meta_planner for replan
            return "meta_planner"

        # 4. Handle Uncertainty (Loop protection)
        if last_status == "uncertain":
            # If uncertain for too long, treat as failure to force replan
            if state.get("uncertain_streak", 0) >= 3:
                return "meta_planner"
            # Otherwise, meta_planner will decide if we continue or replan
            return "meta_planner"

        # 5. Success - Check for Completion
        return self._check_knowledge_transition(state, step_count)

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
        last_msg = messages[-1].content.lower()
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
