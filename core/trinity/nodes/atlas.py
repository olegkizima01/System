import os
import subprocess
import time
from typing import List, Dict, Any, Optional
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from core.trinity.state import TrinityState
from core.constants import VOICE_MARKER, UNKNOWN_STEP
from core.utils import extract_json_object
from providers.copilot import CopilotLLM
from core.verification import AdaptiveVerifier

class AtlasMixin:
    """Mixin for TrinityRuntime containing Atlas (Planner) logic."""

    def _atlas_node(self, state: TrinityState):
        """Generates the plan based on Meta-Planner policy."""
        if self.verbose: print("🌐 [Atlas] Generating steps...")
        
        # 1. State extraction
        plan = state.get("plan")
        replan_count = state.get("replan_count", 0)
        context = state.get("messages", [])
        last_msg = getattr(context[-1], "content", "Start") if context and len(context) > 0 and context[-1] is not None else "Start"

        # 2. Check for existing plan (Anti-loop)
        if plan and len(plan) > 0:
            if self.verbose: print(f"🌐 [Atlas] Using existing plan ({len(plan)} steps). Dispatching to execution.")
            return self._atlas_dispatch(state, plan)

        # 3. Check for replan loop (Anti-loop)
        loop_break = self._check_atlas_loop(state, replan_count, last_msg)
        if loop_break:
            return loop_break

        # 4. Prepare for new planning
        replan_count += 1
        meta_config = state.get("meta_config") or {}
        if self.verbose: print(f"🔄 [Atlas] Replan #{replan_count}")

        try:
            # 5. Prepare prompt
            prompt = self._prepare_atlas_prompt(state, last_msg, meta_config)
            
            # 6. Execute planning request
            raw_plan_data = self._execute_atlas_planning_request(prompt)
            
            # 7. Check for completion or valid plan
            if isinstance(raw_plan_data, dict) and raw_plan_data.get("status") == "completed":
                # Only accept "completed" if global goal is truly achieved
                if self._is_global_goal_achieved(state, context):
                    return {"current_agent": "end", "messages": list(context) + [AIMessage(content=f"[VOICE] {raw_plan_data.get('message', 'Done.')}")]}
                else:
                    # Force LLM to generate remaining steps
                    if self.verbose: print("⚠️ [Atlas] LLM claimed completion but global goal not achieved. Forcing continuation.")
                    forced_plan = self._force_continuation_plan(state, context)
                    if forced_plan:
                        return self._atlas_dispatch(state, forced_plan, replan_count=replan_count, fail_count=state.get("current_step_fail_count", 0))
                    # If no forced plan, try to re-prompt with stronger instruction
                    raw_plan_data = None
                
            raw_plan = self._extract_raw_plan(raw_plan_data, meta_config)
            
            # 8. Optimize or Repair Plan
            optimized_plan = self._process_atlas_plan(raw_plan, plan, meta_config)
            
            return self._atlas_dispatch(state, optimized_plan, replan_count=replan_count, fail_count=state.get("current_step_fail_count", 0))

        except Exception as e:
            err_msg = f"[VOICE] Вибачте, у мене виникла помилка під час планування: {str(e)[:100]}. Спробую ще раз." if self.preferred_language == "uk" else f"[VOICE] Planning error: {str(e)[:100]}. Retrying."
            state["messages"] = list(context) + [AIMessage(content=err_msg)]
            return self._handle_atlas_planning_error(e, state, last_msg, context, replan_count)

    def _check_atlas_loop(self, state, replan_count, last_msg):
        """Check if we're stuck in a replan loop and break it if necessary."""
        last_status = state.get("last_step_status", "success")
        if replan_count >= 3 and last_status != "success":
            if self.verbose: print(f"⚠️ [Atlas] Replan loop detected (#{replan_count}). Forcing simple execution.")
            fallback = [{"id": 1, "type": "execute", "description": last_msg, "agent": "tetyana", "tools": ["browser_open_url"]}]
            return self._atlas_dispatch(state, fallback, replan_count=replan_count, fail_count=state.get("current_step_fail_count", 0))
        return None

    def _prepare_atlas_prompt(self, state, last_msg, meta_config):
        """Prepare the prompt for Atlas planning."""
        from core.agents.atlas import get_atlas_plan_prompt
        
        rag_context = state.get("retrieved_context", "")
        structure_context = self._get_project_structure_context()
        
        final_context = self.context_layer.prepare(
            rag_context=rag_context,
            project_structure=structure_context,
            meta_config=meta_config,
            last_msg=last_msg
        )

        execution_history = []
        hist = state.get("history_plan_execution") or []
        for h in hist:
            execution_history.append(f"- {h}")
        
        history_str = "\n".join(execution_history) if execution_history else "No steps executed yet. Starting fresh."
        
        prompt = get_atlas_plan_prompt(
            f"Global Goal: {state.get('original_task')}\nCurrent Request: {last_msg}\n\nEXECUTION HISTORY SO FAR (Status of steps):\n{history_str}",
            tools_desc=self.registry.list_tools(task_type=state.get("task_type")),
            context=final_context + ("\n\n[MEDIA_MODE] This is a media-related task. Use the Two-Phase Media Strategy." if state.get("is_media") else ""),
            preferred_language=self.preferred_language,
            forbidden_actions="\n".join(state.get("forbidden_actions") or []),
            vision_context=self.vision_context_manager.current_context
        )
        
        self._inject_prompt_modifiers(prompt, state, meta_config)
        return prompt

    def _inject_prompt_modifiers(self, prompt, state, meta_config):
        """Inject specific modifiers like REPAIR or REPLAN instructions into the prompt."""
        plan = state.get("plan")
        if meta_config.get("repair_mode"):
            failed_step = meta_config.get("failed_step", "Unknown")
            remaining_plan = plan if plan else []
            remaining_desc = ", ".join([s.get("description", "?")[:30] for s in remaining_plan[:3]]) if remaining_plan else "none"
            prompt.messages.append(HumanMessage(content=f'''🔧 REPAIR MODE: Generate ONLY ONE alternative step to replace the failed step.
FAILED STEP: {failed_step}
REMAINING PLAN: {remaining_desc}
Generate ONE step that achieves the same goal as the failed step but uses a DIFFERENT approach.
Return JSON with ONLY the replacement step.'''))
        elif state.get("last_step_status") == "failed":
            prompt.messages.append(HumanMessage(content=f"PREVIOUS ATTEMPT FAILED. Current history shows what didn't work. AVOID REPEATING FAILED ACTIONS. Respecify the plan starting from the current state. RESUME, DO NOT RESTART."))
        elif state.get("last_step_status") == "uncertain":
            prompt.messages.append(HumanMessage(content=f"PREVIOUS STEP WAS UNCERTAIN. Review output and verify if you need to retry differently or try alternative."))

    def _execute_atlas_planning_request(self, prompt):
        """Execute the LLM request for planning."""
        def on_delta(chunk):
            self._deduplicated_stream("atlas", chunk)

        atlas_model = os.getenv("ATLAS_MODEL") or os.getenv("COPILOT_MODEL") or "gpt-4.1"
        atlas_llm = CopilotLLM(model_name=atlas_model)

        plan_resp = atlas_llm.invoke_with_stream(prompt.format_messages(), on_delta=on_delta)
        plan_resp_content = getattr(plan_resp, "content", "") if plan_resp is not None else ""
        return extract_json_object(plan_resp_content)

    def _extract_raw_plan(self, data, meta_config):
        """Extract raw plan from JSON data."""
        raw_plan = []
        if isinstance(data, list): 
            raw_plan = data
        elif isinstance(data, dict):
            raw_plan = data.get("steps") or data.get("plan") or []
            if data.get("meta_config"):
                meta_config.update(data["meta_config"])
                if self.verbose: 
                    print(f"🌐 [Atlas] Strategy Justification: {meta_config.get('reasoning')}")
                    print(f"🌐 [Atlas] Preferences: tool_pref={meta_config.get('tool_preference', 'hybrid')}")

        if not raw_plan: 
            raise ValueError("No steps generated")
        return raw_plan

    def _process_atlas_plan(self, raw_plan, existing_plan, meta_config):
        """Process the raw plan (repair or full optimization)."""
        if meta_config.get("repair_mode") and existing_plan:
            # Repair mode: Prepend new step
            repair_step = raw_plan[0] if raw_plan else None
            if repair_step:
                optimized_plan = [repair_step] + list(existing_plan)
                if self.verbose: print(f"🔧 [Atlas] REPAIR: Prepended new step to {len(existing_plan)} remaining steps")
            else:
                optimized_plan = list(existing_plan)
            meta_config["repair_mode"] = False
            return optimized_plan
        else:
            # Full replan: optimize new plan
            grisha_model = os.getenv("GRISHA_MODEL") or os.getenv("COPILOT_MODEL") or "gpt-4.1"
            grisha_llm = CopilotLLM(model_name=grisha_model)
            local_verifier = AdaptiveVerifier(grisha_llm)
            return local_verifier.optimize_plan(raw_plan, meta_config=meta_config)

    def _handle_atlas_planning_error(self, e, state, last_msg, context, replan_count):
        """Handle errors during Atlas planning phase."""
        if self.verbose: print(f"⚠️ [Atlas] Error: {e}")
        
        error_str = str(e).lower()
        if "no steps generated" in error_str or "empty plan" in error_str or "cannot" in error_str:
            if self.verbose:
                print(f"🚨 [Atlas] Planning failure detected. Activating Doctor Vibe intervention.")
            
            pause_context = {
                "reason": "planning_failure",
                "message": f"Doctor Vibe: Atlas failed to create plan for task: {last_msg}",
                "timestamp": str(time.time()),
                "suggested_action": "Please clarify the task or break it into simpler steps",
                "atlas_status": "planning_failed",
                "auto_resume_available": False,
                "original_task": state.get("original_task"),
                "current_attempt": last_msg
            }
                
            self.vibe_assistant.handle_pause_request(pause_context)
            
            return {
                **state,
                "vibe_assistant_pause": pause_context,
                "vibe_assistant_context": f"PAUSED: Planning failure for task: {last_msg}",
                "current_agent": "meta_planner",
                "messages": list(context) + [AIMessage(content=f"[VOICE] Doctor Vibe: Planning issue. Please clarify task.")]
            }
        else:
            if self.verbose:
                print(f"🔄 [Atlas] Using fallback plan due to error: {e}")
            fallback = [{"id": 1, "type": "execute", "description": last_msg, "agent": "tetyana"}]
            return self._atlas_dispatch(state, fallback, replan_count=replan_count)

    def _is_global_goal_achieved(self, state: TrinityState, context: list) -> bool:
        """Check if the global goal was actually achieved based on task type and history."""
        is_media = state.get("is_media", False)
        
        # For media tasks, check if video/content is actually playing
        if is_media:
            history = state.get("history_plan_execution", [])
            history_str = " ".join(str(h) for h in history).lower()
            
            # Media tasks require: search + select + play (+ optional fullscreen)
            required_actions = ["search", "пошук", "google", "click", "відкри"]
            completion_actions = ["play", "відтвор", "fullscreen", "весь екран", "video", "відео"]
            
            has_search = any(a in history_str for a in required_actions)
            has_playback = any(a in history_str for a in completion_actions)
            
            # If only search/open was done but no playback, goal not achieved
            if has_search and not has_playback:
                if self.verbose: print(f"⚠️ [Atlas] Media task: search done but playback not confirmed")
                return False
                
            # Check step count - media tasks typically need 4+ steps
            step_count = state.get("step_count", 0)
            if step_count < 3:
                if self.verbose: print(f"⚠️ [Atlas] Media task: only {step_count} steps completed, likely incomplete")
                return False
        
        # Check if last message indicates actual completion
        if context:
            last_content = str(getattr(context[-1], "content", "")).lower() if context[-1] else ""
            completion_indicators = ["fullscreen", "весь екран", "playing", "відтворюється", "watching", "дивимось", "video started", "відео запущено"]
            if any(ind in last_content for ind in completion_indicators):
                return True
        
        # Default: check if plan was fully executed AND enough steps were done
        plan = state.get("plan", [])
        step_count = state.get("step_count", 0)
        return len(plan) == 0 and step_count > 3

    def _force_continuation_plan(self, state: TrinityState, context: list) -> list:
        """Generate continuation plan when LLM incorrectly claims completion."""
        is_media = state.get("is_media", False)
        history = state.get("history_plan_execution", [])
        history_str = " ".join(str(h) for h in history).lower()
        
        if is_media:
            # Check what stage we're at based on history
            has_open = any(k in history_str for k in ["google", "browser", "браузер", "open", "відкри"])
            has_search = any(k in history_str for k in ["search", "type", "пошук", "ввести"])
            has_links = any(k in history_str for k in ["link", "result", "результат", "get_links"])
            has_click = any(k in history_str for k in ["click", "select", "вибр", "відкри"])
            has_play = any(k in history_str for k in ["play", "відтвор"])
            
            if has_open and not has_search:
                return [
                    {"id": 1, "type": "execute", "description": "Ввести пошуковий запит у Google", "agent": "tetyana", "tools": ["browser_type_text", "press_key"]},
                    {"id": 2, "type": "execute", "description": "Отримати результати пошуку", "agent": "tetyana", "tools": ["browser_get_links"]},
                    {"id": 3, "type": "execute", "description": "Відкрити перший релевантний результат", "agent": "tetyana", "tools": ["browser_click"]},
                    {"id": 4, "type": "execute", "description": "Запустити відео на весь екран", "agent": "tetyana", "tools": ["press_key"]}
                ]
            elif has_search and not has_links:
                return [
                    {"id": 1, "type": "execute", "description": "Отримати посилання з результатів пошуку", "agent": "tetyana", "tools": ["browser_get_links"]},
                    {"id": 2, "type": "execute", "description": "Відкрити перший безкоштовний сайт", "agent": "tetyana", "tools": ["browser_click"]},
                    {"id": 3, "type": "execute", "description": "Запустити відео на весь екран", "agent": "tetyana", "tools": ["press_key"]}
                ]
            elif has_links and not has_click:
                return [
                    {"id": 1, "type": "execute", "description": "Вибрати та відкрити перший релевантний результат", "agent": "tetyana", "tools": ["browser_click"]},
                    {"id": 2, "type": "execute", "description": "Запустити відео та увімкнути повноекранний режим", "agent": "tetyana", "tools": ["browser_click", "press_key"]}
                ]
            elif has_click and not has_play:
                return [
                    {"id": 1, "type": "execute", "description": "Знайти кнопку відтворення та натиснути", "agent": "tetyana", "tools": ["browser_click"]},
                    {"id": 2, "type": "execute", "description": "Перемкнути на повноекранний режим (натиснути F)", "agent": "tetyana", "tools": ["press_key"]}
                ]
            elif has_play:
                return [{"id": 1, "type": "execute", "description": "Перемкнути на повноекранний режим (натиснути F)", "agent": "tetyana", "tools": ["press_key"]}]
        
        return None  # Let normal replan handle it

    def _atlas_dispatch(self, state, plan, replan_count=None, fail_count=None, last_status=None, uncertain_streak=None):
        """Internal helper to format the dispatch message and return state."""
        context = state.get("messages", [])
        step_count = state.get("step_count", 0) + 1
        replan_count = replan_count or state.get("replan_count", 0)
        fail_count = fail_count if fail_count is not None else state.get("current_step_fail_count", 0)
        last_status = last_status if last_status is not None else state.get("last_step_status", "success")
        streak = uncertain_streak if uncertain_streak is not None else state.get("uncertain_streak", 0)
        
        current_step = plan[0] if plan else None
        if not current_step:
            return {"current_agent": "end", "messages": list(context) + [AIMessage(content="[VOICE] План порожній.")]}

        desc = current_step.get('description', '')
        step_type = current_step.get("type", "execute")
        next_agent = "grisha" if step_type == "verify" else "tetyana"
        
        voice = f"[VOICE] {next_agent.capitalize()}, {desc}."
        content = voice
        
        return {
            "current_agent": next_agent,
            "messages": list(context) + [AIMessage(content=content)],
            "plan": plan,
            "step_count": step_count,
            "replan_count": replan_count,
            "meta_config": state.get("meta_config"),
            "current_step_fail_count": fail_count,
            "last_step_status": last_status,
            "uncertain_streak": streak,
            "gui_mode": state.get("gui_mode"),
            "execution_mode": state.get("execution_mode"),
            "task_type": state.get("task_type"),
            "vision_context": self.vision_context_manager.get_context_for_api()
        }

    def _get_project_structure_context(self) -> str:
        """Read project_structure_final.txt for Atlas context."""
        try:
            git_root = self._get_git_root()
            if not git_root:
                return ""
            
            structure_file = os.path.join(git_root, getattr(self, "PROJECT_STRUCTURE_FILE", "project_structure_final.txt"))
            if not os.path.exists(structure_file):
                return ""
            
            # Read only first part of file to avoid memory issues with huge files
            with open(structure_file, 'r', encoding='utf-8') as f:
                content = f.read(100000)
            
            return self._parse_context_sections(content)
            
        except Exception as e:
            if self.verbose:
                print(f"⚠️ [Trinity] Error reading project structure: {e}")
            return ""

    def _parse_context_sections(self, content: str) -> str:
        """Extract key sections (Metadata, Logs, Structure) from project structure file."""
        lines = content.split('\n')
        context_lines = []
        current_section = None
        section_count = 0
        
        for line in lines:
            # Each line limited to 500 chars to avoid prompt blowup
            line = line[:500]
            lstrip = line.strip()
            
            # Identify or switch sections
            new_section = self._identify_structure_section(lstrip, current_section)
            if new_section != current_section:
                current_section = new_section
                section_count = 0
            
            # Collect lines
            if current_section and section_count < 30:
                 if lstrip and not lstrip.startswith('```'):
                    context_lines.append(line)
                    section_count += 1
        
        return '\n'.join(context_lines[:150])

    def _identify_structure_section(self, lstrip: str, current_section: Optional[str]) -> Optional[str]:
        """Identify which section a line belongs to."""
        if lstrip.startswith('## Metadata'): return 'metadata'
        if '## Program Execution Logs' in lstrip: return 'logs'
        if '## Project Structure' in lstrip: return 'structure'
        
        if lstrip.startswith('## ') and current_section:
            # New section that isn't one of the known ones -> exit section
            return None
        return current_section

    def _regenerate_project_structure(self, response_text: str) -> bool:
        """Regenerate project_structure_final.txt with last response."""
        try:
            git_root = self._get_git_root()
            if not git_root:
                if getattr(self, "verbose", False):
                    print("⚠️ [Trinity] Not a git repo, skipping structure regeneration")
                return False
            
            # Save response to LAST_RESPONSE_FILE
            response_file = os.path.join(git_root, getattr(self, "LAST_RESPONSE_FILE", ".last_response.txt"))
            with open(response_file, 'w', encoding='utf-8') as f:
                f.write(response_text)
            
            # Run regenerate_structure.sh
            regenerate_script = os.path.join(git_root, "regenerate_structure.sh")
            if not os.path.exists(regenerate_script):
                if getattr(self, "verbose", False):
                    print("⚠️ [Trinity] regenerate_structure.sh not found")
                return False
            
            result = subprocess.run(
                ["bash", regenerate_script],
                cwd=git_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                if getattr(self, "verbose", False):
                    print("✓ [Trinity] Project structure regenerated")
                return True
            else:
                if getattr(self, "verbose", False):
                    print(f"⚠️ [Trinity] Structure regeneration failed: {result.stderr}")
                return False
                
        except Exception as e:
            if getattr(self, "verbose", False):
                print(f"⚠️ [Trinity] Error regenerating structure: {e}")
            return False
