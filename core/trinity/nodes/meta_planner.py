from typing import List, Dict, Any, Optional
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from core.trinity.state import TrinityState
from core.constants import VOICE_MARKER, MESSAGES, UNKNOWN_STEP
from core.utils import extract_json_object

class MetaPlannerMixin:
    """Mixin for TrinityRuntime containing Meta-Planner logic."""

    def _meta_planner_node(self, state: TrinityState):
        """The 'Controller Brain' that sets policies and manages replanning strategy."""
        if self.verbose: print(f"🧠 {VOICE_MARKER} [Meta-Planner] Analyzing strategy...")
        context = state.get("messages", [])
        last_msg = getattr(context[-1], "content", "Start") if context and context[-1] else "Start"
        
        # 1. Initialize and maintain state
        meta_config = self._prepare_meta_config(state, last_msg)
        summary = self._update_periodic_summary(state, context)
        
        # 2. Check hard limits
        limit_reached = self._check_master_limits(state, context)
        if limit_reached: return limit_reached
        
        # 3. Consume or handle previous step result
        plan = state.get("plan") or []
        last_status = state.get("last_step_status", "success")
        fail_count = int(state.get("current_step_fail_count") or 0)

        # If there's no active plan but the last step was uncertain, increment
        # the failure counter on repeated meta-planner invocations. This helps
        # escalate persistent uncertainty even across repair/replan cycles.
        if not plan and last_status == "uncertain":
            fail_count += 1
            state["current_step_fail_count"] = fail_count
            # If we've reached hard failure threshold, mark the status
            if fail_count >= 4:
                last_status = "failed"
                state["last_step_status"] = "failed"
        
        if plan:
            plan, last_status, fail_count = self._consume_execution_step(state, plan, last_status, fail_count, last_msg)
            
        # 4. Decide next action
        action = self._decide_meta_action(plan, last_status, fail_count, state)
        
        # 5. Execute meta-action (replan/repair/initialize)
        if action in ["initialize", "replan", "repair"]:
            verbals = {
                "initialize": "Розпочинаю планування завдання." if self.preferred_language == "uk" else "Initializing task planning.",
                "replan": "Попередній підхід не спрацював, розробляю новий план." if self.preferred_language == "uk" else "Previous approach failed, developing new plan.",
                "repair": "Крок не вдався, спробую виправити ситуацію іншим способом." if self.preferred_language == "uk" else "Step failed, attempting repair."
            }
            msg = verbals.get(action, "Аналізую стратегію." if self.preferred_language == "uk" else "Analyzing strategy.")
            state["messages"] = list(context) + [AIMessage(content=f"[VOICE] {msg}")]
            return self._handle_meta_action(state, action, plan, last_msg, meta_config, fail_count, summary, last_status=last_status)

        # 6. Default flow: Atlas dispatch
        out = self._atlas_dispatch(state, plan, last_status=last_status, fail_count=fail_count)
        out["summary"] = summary
        return out

    def _prepare_meta_config(self, state: TrinityState, last_msg: str) -> Dict[str, Any]:
        cfg = state.get("meta_config") or {}
        if not isinstance(cfg, dict): cfg = {}
        defaults = {
            "strategy": "hybrid", "verification_rigor": "standard",
            "recovery_mode": "local_fix", "tool_preference": "hybrid",
            "reasoning": "", "retrieval_query": last_msg, "n_results": 3
        }
        for k, v in defaults.items():
            cfg.setdefault(k, v)
        return cfg

    def _update_periodic_summary(self, state: TrinityState, context: List[Any]) -> str:
        summary = state.get("summary", "")
        step_count = state.get("step_count", 0)
        if len(context) > 6 and step_count % 3 == 0:
            try:
                recent = [str(getattr(m, "content", ""))[:4000] for m in context[-4:] if m]
                prompt = [
                    SystemMessage(content=f"Trinity archivist. Summarize (2-3 sentences) in {self.preferred_language}."),
                    HumanMessage(content=f"Summary: {summary}\n\nEvents:\n" + "\n".join(recent))
                ]
                summary = getattr(self.llm.invoke(prompt), "content", "")
            except Exception: pass
        return summary

    def _check_master_limits(self, state: TrinityState, context: List[Any]) -> Optional[Dict[str, Any]]:
        lang = self.preferred_language if self.preferred_language in MESSAGES else "en"
        max_steps = getattr(self, "MAX_STEPS", 30)
        max_replans = getattr(self, "MAX_REPLANS", 10)
        
        if state.get("step_count", 0) >= max_steps:
            msg = MESSAGES[lang]["step_limit_reached"].format(limit=max_steps)
            return {"current_agent": "end", "messages": list(context) + [AIMessage(content=f"{VOICE_MARKER} {msg}")]}
        if state.get("replan_count", 0) >= max_replans:
            msg = MESSAGES[lang]["replan_limit_reached"].format(limit=max_replans)
            return {"current_agent": "end", "messages": list(context) + [AIMessage(content=f"{VOICE_MARKER} {msg}")]}
        return None

    def _consume_execution_step(self, state: TrinityState, plan: List[Dict], status: str, fail_count: int, last_msg: str) -> tuple:
        hist = state.get("history_plan_execution") or []
        desc = plan[0].get('description', UNKNOWN_STEP) if plan else UNKNOWN_STEP
        
        if status == "success":
            plan.pop(0)
            hist.append(f"SUCCESS: {desc}")
            fail_count = 0
            state["gui_fallback_attempted"] = False
        elif status == "failed":
            fail_count += 1
            hist.append(f"FAILED: {desc} (Try #{fail_count})")
            # CRITICAL FIX: Add to forbidden after 2 fails, not 4!
            if fail_count >= 2:
                forbidden = state.get("forbidden_actions") or []
                # Extract tools from the failed step to forbid them
                if plan and plan[0].get('tools'):
                    for tool in plan[0]['tools']:
                        forbidden.append(f"AVOID: {tool} for '{desc}'")
                forbidden.append(f"FAILED APPROACH: {desc}")
                state["forbidden_actions"] = list(set(forbidden))  # Deduplicate
        elif status == "uncertain":
            fail_count += 1
            hist.append(f"UNCERTAIN: {desc} (Check #{fail_count})")
            # CRITICAL FIX: Treat repeated uncertainty as failure
            if fail_count >= 2:
                status = "failed"
                forbidden = state.get("forbidden_actions") or []
                forbidden.append(f"UNCERTAIN APPROACH: {desc}")
                state["forbidden_actions"] = list(set(forbidden))
                
        state["history_plan_execution"] = hist
        # Persist the updated status and fail count into state so subsequent
        # calls to the meta-planner and dispatch flow see consistent values.
        state["current_step_fail_count"] = fail_count
        state["last_step_status"] = status
        return plan, status, fail_count

    def _decide_meta_action(self, plan: List[Dict], status: str, fail_count: int, state: TrinityState) -> str:
        if not state.get("meta_config"): return "initialize"
        if not plan: return "replan"
        
        # If we are failing or stuck in uncertainty, trigger replan or repair
        if status == "failed":
            if fail_count >= 3:
                hist = state.get("history_plan_execution") or []
                if hist:
                    forbidden = state.get("forbidden_actions") or []
                    forbidden.append(f"FAILED ACTION: {hist[-1]}")
                    state["forbidden_actions"] = forbidden
                return "replan"
            
            cfg = state.get("meta_config") or {}
            return "replan" if cfg.get("recovery_mode") == "full_replan" else "repair"
            
        if status == "uncertain":
            # If we've been uncertain for more than 1 attempt on the same step, 
            # something is wrong with the plan or the agent's ability to verify.
            # Especially for browser tasks, repeating a click/navigate is a loop.
            if fail_count >= 1:
                if self.verbose: 
                    print(f"⚠️ [Meta-Planner] Uncertainty detected ({fail_count} tries). Triggering repair to avoid loops.")
                return "repair"
            return "proceed"
            
        vibe_ctx = state.get("vibe_assistant_context", "")
        if "background_mode" in vibe_ctx: return "proceed"
        
        return "proceed"

    def _handle_meta_action(self, state: TrinityState, action: str, plan: List[Dict], last_msg: str, 
                           meta_config: Dict, fail_count: int, summary: str, last_status: str = "success"):
        from core.agents.atlas import get_meta_planner_prompt
        task_ctx = f"Goal: {state.get('original_task')}\nReq: {last_msg}\nStep: {state.get('step_count')}\nStatus: {state.get('last_step_status')}"
        prompt = get_meta_planner_prompt(task_ctx, preferred_language=self.preferred_language)
        
        try:
            resp = self.llm.invoke(prompt.format_messages())
            data = extract_json_object(getattr(resp, "content", ""))
            if data and "meta_config" in data:
                meta_config.update(data["meta_config"])
                if meta_config.get("strategy") == "rag_heavy" or action in ["initialize", "replan", "repair"]:
                    self._perform_selective_rag(state, meta_config, last_msg)
        except Exception: pass

        plan_for_atlas = plan[1:] if action == "repair" and len(plan) > 0 else None
        meta_config["repair_mode"] = (action == "repair")
        meta_config["failed_step"] = plan[0].get("description", UNKNOWN_STEP) if action == "repair" and plan else UNKNOWN_STEP
        
        return {
            "current_agent": "atlas", "meta_config": meta_config, "plan": plan_for_atlas,
            "current_step_fail_count": fail_count, "summary": summary,
            "last_step_status": last_status,
            "gui_fallback_attempted": False if action == "replan" else state.get("gui_fallback_attempted"),
            "retrieved_context": state.get("retrieved_context", "")
        }

    def _classify_task_llm(self, task: str) -> Optional[Dict[str, Any]]:
        """Classify task using LLM for better intent recognition."""
        try:
            sys_prompt = (
                "You are a task router for a macOS developer assistant. "
                "Classify the user request into one of: DEV, GENERAL. "
                "DEV means software development work (debugging, code analysis, git, tests, repo files). "
                "GENERAL means completely unrelated non-technical/personal tasks. "
                "Default to DEV if there is any technical context."
                "Return STRICT JSON only with keys: task_type (DEV|GENERAL), confidence (0..1), reason (string)."
            )
            msgs = [
                SystemMessage(content=sys_prompt),
                HumanMessage(content=str(task or "")),
            ]
            resp = self.llm.invoke(msgs)
            data = extract_json_object(getattr(resp, "content", ""))
            if not data: return None
            
            task_type = str(data.get("task_type") or "").strip().upper()
            if task_type not in {"DEV", "GENERAL"}: return None
            
            return {
                "task_type": task_type,
                "confidence": float(data.get("confidence", 0.0)),
                "reason": str(data.get("reason") or ""),
            }
        except Exception:
            return None

    def _classify_task_fallback(self, task: str) -> Dict[str, Any]:
        """Keyword-based fallback for task classification."""
        task_lower = str(task or "").lower()
        # Use keywords from self (inherited from TrinityRuntime)
        dev_keywords = getattr(self, "DEV_KEYWORDS", set())
        general_keywords = getattr(self, "NON_DEV_KEYWORDS", set())

        for keyword in general_keywords:
            if keyword in task_lower:
                return {"task_type": "GENERAL", "confidence": 0.2, "reason": "keyword_fallback: non_dev"}

        for keyword in dev_keywords:
            if keyword in task_lower:
                return {"task_type": "DEV", "confidence": 0.2, "reason": "keyword_fallback: dev"}

        return {"task_type": "UNKNOWN", "confidence": 0.1, "reason": "keyword_fallback: unknown"}

    def _classify_task(self, task: str) -> tuple[str, bool, bool]:
        """
        Classify task as DEV or GENERAL.
        Returns: (task_type, is_dev, is_media)
        """
        from core.constants import MEDIA_KEYWORDS
        task_lower = str(task or "").lower()
        is_media = any(k in task_lower for k in MEDIA_KEYWORDS)
        
        llm_res = self._classify_task_llm(task)
        if llm_res:
            task_type = llm_res.get("task_type", "UNKNOWN")
            return (task_type, task_type == "DEV", is_media)
            
        fb = self._classify_task_fallback(task)
        task_type = fb.get("task_type", "UNKNOWN")
        return (task_type, task_type != "GENERAL", is_media)

    def _perform_selective_rag(self, state: TrinityState, meta_config: Dict, last_msg: str):
        query = meta_config.get("retrieval_query", last_msg)
        limit = int(meta_config.get("n_results", 3))
        # Assuming self.memory is available via TrinityRuntime
        mem_res = self.memory.query_memory("knowledge_base", query, n_results=limit)
        relevant = []
        for r in mem_res:
            m = r.get("metadata", {})
            if m.get("status") == "success" and float(m.get("confidence", 1.0)) > 0.3:
                relevant.append(f"[SUCCESS] {r.get('content')}")
            elif m.get("status") == "failed":
                relevant.append(f"[WARNING: FAILED] Avoid: {r.get('content')}")
        
        if not relevant:
            mem_res = self.memory.query_memory("strategies", query, n_results=limit)
            relevant = [r.get("content", "") for r in mem_res]
        state["retrieved_context"] = "\n".join(relevant)
