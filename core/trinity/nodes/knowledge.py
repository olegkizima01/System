import time
from langchain_core.messages import AIMessage
from core.trinity.state import TrinityState
from tui.logger import trace

class KnowledgeMixin:
    """Mixin for TrinityRuntime containing Knowledge/Learning logic."""

    def _knowledge_node(self, state: TrinityState):
        """Final node to extract and store knowledge from completion."""
        if self.verbose:
            print("🧠 [Learning] Extracting structured experience...")
        
        context = state.get("messages", [])
        plan = state.get("plan") or []
        summary = state.get("summary", "")
        replan_count = state.get("replan_count", 0)
        
        actual_status = self._determine_knowledge_status(state, context)
        confidence = self._calculate_confidence(actual_status, replan_count, len(plan))
        
        self._store_experience(summary, actual_status, plan, confidence, replan_count)
        
        final_msg = "[VOICE] Досвід збережено. Завдання завершено." if self.preferred_language == "uk" else "[VOICE] Experience stored. Task completed."
        return {"current_agent": "end", "messages": context + [AIMessage(content=final_msg)]}

    def _determine_knowledge_status(self, state: TrinityState, context: list) -> str:
        """Determine actual status for knowledge storage."""
        if state.get("last_step_status") == "failed":
            return "failed"
        if context and context[-1] is not None:
            last_content = getattr(context[-1], "content", "").lower()
            if "failed" in last_content:
                return "failed"
        return "success"

    def _calculate_confidence(self, status: str, replan_count: int, plan_len: int) -> float:
        """Calculate confidence score."""
        if status != "success":
            return 0.5
        confidence = 1.0 - (min(replan_count, 5) * 0.1) - (min(plan_len, 10) * 0.02)
        return max(0.1, round(confidence, 2))

    def _store_experience(self, summary: str, status: str, plan: list, confidence: float, replan_count: int):
        """Store experience in knowledge base."""
        try:
            experience = f"Task: {summary}\\nStatus: {status}\\nSteps: {len(plan)}\\n"
            if plan:
                experience += "Plan Summary:\\n" + "\\n".join([f"- {s.get('description')}" for s in plan])
            
            # Use self.memory which should be available on the runtime
            self.memory.add_memory(
                category="knowledge_base",
                content=experience,
                metadata={
                    "type": "experience_log", "status": status, "source": "trinity_runtime",
                    "timestamp": int(time.time()), "confidence": confidence, "replan_count": replan_count
                }
            )
            if self.verbose:
                print(f"🧠 [Learning] {status.upper()} experience stored (conf: {confidence})")
            try:
                trace(self.logger, "knowledge_stored", {"status": status, "confidence": confidence})
            except Exception:
                pass
        except Exception as e:
            if self.verbose:
                print(f"⚠️ [Learning] Error: {e}")
