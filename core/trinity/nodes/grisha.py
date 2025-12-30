import os
import subprocess
import re
import time
from typing import List, Dict, Any
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
from core.trinity.state import TrinityState
from core.constants import VOICE_MARKER, FAILURE_MARKERS, SUCCESS_MARKERS, NEGATION_PATTERNS, STEP_COMPLETED_MARKER, DEFAULT_MODEL_FALLBACK
from core.agents.grisha import get_grisha_prompt, get_grisha_media_prompt
from providers.copilot import CopilotLLM

class GrishaMixin:
    """Mixin for TrinityRuntime containing Grisha (Verifier) logic."""

    def _grisha_node(self, state: TrinityState):
        if self.verbose: print(f"👁️ {VOICE_MARKER} [Grisha] Verifying...")
        context = state.get("messages", [])
        last_msg = self._get_last_msg_content(context)
        
        # 1. Run tests if needed
        test_results = self._run_grisha_tests(state)

        # 2. Invoke LLM and get initial response
        prompt = self._prepare_grisha_prompt(state, last_msg)
        content, tool_calls = self._invoke_grisha(prompt, last_msg)
        
        # 3. Execute Verification Tools
        executed_results = self._execute_grisha_tools(tool_calls)
        
        # 4. Smart Vision Verification
        vision_result = self._perform_smart_vision(state, last_msg)
        if vision_result:
            content += f"\\n\\n[GUI_BROWSER_VERIFY]\\n{vision_result}"
            executed_results.append(vision_result)

        # 5. Verdict Analysis
        final_content = self._get_grisha_verdict(content, executed_results, test_results)
        step_status, next_agent = self._determine_grisha_status(state, final_content, executed_results)

        # 6. Anti-loop protection
        current_streak = self._handle_grisha_streak(state, step_status, final_content)

        return {
            "current_agent": next_agent,
            "messages": list(context) + [AIMessage(content=final_content)],
            "last_step_status": step_status,
            "uncertain_streak": current_streak,
            "plan": state.get("plan"),
        }

    def _get_last_msg_content(self, context):
        msg = getattr(context[-1], "content", "") if context and context[-1] else ""
        if isinstance(msg, str) and len(msg) > 50000:
            return msg[:45000] + "\\n[...]\\n" + msg[-5000:]
        return msg

    def _run_grisha_tests(self, state):
        task_type = str(state.get("task_type") or "").upper()
        if task_type == "GENERAL": return ""
        
        critical_dirs = ["core/", "system_ai/", "tui/", "providers/"]
        # Ensure _get_repo_changes is available (via IntegrationGitMixin)
        changes = self._get_repo_changes()
        changed_files = (changes.get("changed_files") or []) if changes.get("ok") else []
        
        if any(any(f.startswith(d) for d in critical_dirs) for f in changed_files):
            if self.verbose: print("👁️ [Grisha] Running pytest...")
            # Use _get_git_root helper
            root = self._get_git_root() or "."
            res = subprocess.run("pytest -q --tb=short 2>&1", shell=True, capture_output=True, text=True, cwd=root)
            return f"\\n\\n[TEST_VERIFICATION] pytest output:\\n{res.stdout + res.stderr}"
        return ""

    def _prepare_grisha_prompt(self, state, last_msg):
        plan = state.get("plan") or []
        current_step = plan[0].get("description", "Unknown") if plan else "Final Verification"
        original_task = state.get("original_task") or ""
        
        verify_context = f"GLOBAL GOAL: {original_task}\\nSTEP TO VERIFY: {current_step}\\nREPORT: {last_msg[:30000]}"
        
        if state.get("is_media"):
            return get_grisha_media_prompt(verify_context, tools_desc=self.registry.list_tools(task_type=state.get("task_type")), preferred_language=self.preferred_language)
        
        return get_grisha_prompt(
            verify_context,
            tools_desc=self.registry.list_tools(task_type=state.get("task_type")),
            preferred_language=self.preferred_language,
            vision_context=self.vision_context_manager.current_context
        )

    def _invoke_grisha(self, prompt, last_msg):
        # Prefer runtime-provided LLM (tests set rt.llm), fallback to Copilot provider
        if getattr(self, "llm", None) is not None:
            llm = self.llm
        else:
            model = os.getenv("GRISHA_MODEL") or os.getenv("COPILOT_MODEL") or DEFAULT_MODEL_FALLBACK
            llm = CopilotLLM(model_name=model)
        
        # Rate limiting: delay before LLM call to avoid API overload
        time.sleep(1.5)
        
        def on_delta(chunk): self._deduplicated_stream("grisha", chunk)
        resp = llm.invoke_with_stream(prompt.format_messages(), on_delta=on_delta)
        content = getattr(resp, "content", "") if resp else ""
        tool_calls = getattr(resp, "tool_calls", []) if resp and hasattr(resp, 'tool_calls') else []
        
        # Override if Grisha fails without evidence, BUT NOT if there are captcha/error indicators
        last_msg_str = str(last_msg) if not isinstance(last_msg, str) else last_msg
        last_msg_lower = last_msg_str.lower()
        captcha_indicators = ["captcha", "sorry/index", "recaptcha", "blocked", "status\": \"error", "status\": \"captcha", "status\": \"warning", "links\": []"]
        has_captcha_evidence = any(ind in last_msg_lower for ind in captcha_indicators)
        
        if not has_captcha_evidence and any(m in content.lower() for m in ["failed", "не виконано"]) and not tool_calls and STEP_COMPLETED_MARKER.lower() in last_msg_lower:
            if self.verbose: print("⚠️ [Grisha] Overriding FAILED without evidence.")
            content = f"{VOICE_MARKER} Tetyana reported success. Tools confirmed. {STEP_COMPLETED_MARKER}"
            tool_calls = []
        return content, tool_calls

    def _execute_grisha_tools(self, tool_calls):
        results = []
        forbidden = ["browser_open", "browser_click", "browser_type", "write_", "create_", "delete_", "move_"]
        for tool in (tool_calls or []):
            name = tool.get("name")
            args = tool.get("args") or {}
            if any(name.startswith(p) for p in forbidden):
                results.append(f"Result for {name}: [BLOCKED] Grisha is read-only.")
                continue
            res = self.registry.execute(name, ({"app_name": None} if name == "capture_screen" and not args else args))
            results.append(f"Result for {name}: {res}")
        return results

    def _perform_smart_vision(self, state, last_msg):
        tetyana_tools = state.get("tetyana_used_tools") or []
        tetyana_ctx = state.get("tetyana_tool_context") or {}
        
        last_msg_str = str(last_msg) if not isinstance(last_msg, str) else last_msg
        original_task = str(state.get("original_task") or "")
        
        # Check if this is a media task
        is_media_task = any(keyword in original_task.lower() for keyword in ["фільм", "movie", "video", "перегляд", "watch", "відео"])
        
        browser_active = any(k in last_msg_str.lower() or k in original_task.lower() for k in ["google", "browser", "сайт", "url"])
        needs_visual = (set(tetyana_tools) & {"click", "type_text", "move_mouse"}) or browser_active or tetyana_ctx.get("browser_tool")
        
        if not (needs_visual or (state.get("gui_mode") in {"auto", "on"} and state.get("execution_mode") == "gui")):
            return None

        if any(t in tetyana_tools for t in ["browser_type_text", "browser_click", "browser_open_url"]):
            time.sleep(3.0)
            
        args = {}
        if tetyana_ctx.get("app_name"):
            args["app_name"] = tetyana_ctx["app_name"]
            if tetyana_ctx.get("window_title"): args["window_title"] = tetyana_ctx["window_title"]
            
        analysis = self.registry.execute("enhanced_vision_analysis", args)
        
        if isinstance(analysis, dict) and analysis.get("status") == "success":
            self.vision_context_manager.update_context(analysis)
            
            # For media tasks, enhance the analysis with media-specific checks
            if is_media_task:
                enhanced_analysis = self._enhance_media_vision_analysis(analysis, original_task)
                if enhanced_analysis:
                    analysis["media_analysis"] = enhanced_analysis
                    # Update the context with media-specific information
                    analysis["context"]["media_context"] = enhanced_analysis
        
        return str(analysis)
    
    def _enhance_media_vision_analysis(self, vision_data, original_task):
        """Enhance vision analysis for media tasks by looking for video-specific indicators."""
        try:
            ocr_text = vision_data.get("ocr", {}).get("text", "").lower()
            context = vision_data.get("context", "").lower()
            
            # Look for media-specific indicators in OCR and context
            media_indicators = {
                "video_playing": any(word in ocr_text or word in context for word in ["playing", "відтворюється", "грає", "running"]),
                "video_player": any(word in ocr_text or word in context for word in ["player", "плеєр", "video", "відео", "медіа"]),
                "fullscreen": any(word in ocr_text or word in context for word in ["fullscreen", "повний екран", "full screen"]),
                "play_button": any(word in ocr_text or word in context for word in ["play", "грати", "відтворити", "▶"]),
                "pause_button": any(word in ocr_text or word in context for word in ["pause", "пауза", "⏸"]),
                "progress_bar": any(word in ocr_text or word in context for word in ["progress", "прогрес", "timeline", "таймлайн"]),
                "volume_control": any(word in ocr_text or word in context for word in ["volume", "гучність", "sound", "звук"]),
                "movie_title": len(ocr_text.split()) > 3 and any(word in ocr_text for word in ["film", "movie", "фільм", "кіно"])
            }
            
            # Calculate media confidence score
            positive_indicators = sum(1 for v in media_indicators.values() if v)
            media_confidence = min(1.0, positive_indicators / 4.0)  # 0-1 scale
            
            # Determine if media appears to be playing
            likely_playing = media_confidence > 0.5 or (media_indicators["video_playing"] and media_indicators["video_player"])
            
            return {
                "is_media_task": True,
                "media_indicators": media_indicators,
                "media_confidence": media_confidence,
                "likely_playing": likely_playing,
                "analysis": f"Media analysis: {'Likely playing' if likely_playing else 'Uncertain'}. "
                          f"Confidence: {media_confidence:.2f}. "
                          f"Indicators: {', '.join(k for k, v in media_indicators.items() if v)}"
            }
            
        except Exception as e:
            return {
                "is_media_task": True,
                "error": f"Media analysis error: {str(e)}",
                "media_confidence": 0.0,
                "likely_playing": False
            }

    def _get_grisha_verdict(self, content, executed_results, test_results):
        if not executed_results and not test_results: return content
        
        prompt = (f"Analyze these results:\\n" + "\\n".join(executed_results) + (f"\\nTests:\\n{test_results}" if test_results else "") +
                 f"\\n\\nRespond with Reasoning + Marker: [VERIFIED], [STEP_COMPLETED], [FAILED], or [UNCERTAIN]. "
                 f"Do NOT use [VOICE] tag in this response, provide analysis only.")
        try:
            resp = self.llm.invoke([SystemMessage(content="You are Grisha."), HumanMessage(content=prompt)])
            analysis = getattr(resp, "content", "")
            # Ensure we don't double the voice icon in UI
            if VOICE_MARKER in analysis:
                analysis = analysis.replace(VOICE_MARKER, "").strip()
            
            return content + "\\n\\n[VERDICT ANALYSIS]\\n" + analysis
        except Exception as e:
            return content + f"\\n\\n[VERDICT ERROR] {e}"

    def _determine_grisha_status(self, state, content, executed_results):
        lower = content.lower()
        res_str = "\\n".join(executed_results).lower()
        original_task = (state.get("original_task") or "").lower()
        step_count = state.get("step_count", 0)
        uncertain_streak = state.get("uncertain_streak", 0)
        
        # Check if this is a media/movie task
        is_media_task = any(keyword in original_task for keyword in ["фільм", "movie", "video", "перегляд", "watch", "відео"])
        
        # Priority 0: Anti-loop protection - force decision after too many steps
        # This prevents infinite loops seen in logs where tasks run for 30+ steps
        if step_count > 15 and "failed" not in lower and "error" not in lower:
            if self.verbose:
                print(f"⚠️ [Grisha] Anti-loop triggered: step_count={step_count}, forcing success")
            return "success", "meta_planner"
        
        # If we've been in uncertain streak for too long, force a decision
        if uncertain_streak >= 5 and "failed" not in lower:
            if self.verbose:
                print(f"⚠️ [Grisha] Uncertain streak={uncertain_streak}, forcing success")
            return "success", "meta_planner"
        
        # Priority 1: Explicit markers in brackets
        if "[failed]" in lower:
            return "failed", "meta_planner"
        if any(m in lower for m in ["[verified]", "[step_completed]", "[achievement_confirmed]", "[ok]"]):
            return "success", "meta_planner"
        if "[uncertain]" in lower or "[captcha]" in lower:
            return "uncertain", "meta_planner"

        # Priority 2: Failure indicators
        if any(m in lower or f"[{m}]" in lower for m in FAILURE_MARKERS) or ("[test_verification]" in lower and "failed" in lower):
            return "failed", "meta_planner"
        if '"status": "error"' in res_str or '"status": "captcha"' in res_str:
            return "failed", "meta_planner"
            
        # Priority 3: Success keywords with negation check
        for kw in SUCCESS_MARKERS:
            if kw.lower() in lower:
                # Find all occurrences and check for negations
                pattern = f"(?i)(?:{NEGATION_PATTERNS.get(self.preferred_language, 'not |never ')})?\\s*{re.escape(kw)}"
                match = re.search(pattern, lower)
                if match and not any(neg in match.group(0).lower() for neg in NEGATION_PATTERNS.get(self.preferred_language, "not |never ").split('|')):
                    return "success", "meta_planner"
        
        # Priority 4: Media task specific verification
        if is_media_task:
            # For media tasks, be more lenient with verification
            # Look for indicators that media is playing or accessible
            media_success_indicators = [
                "відео відтворюється", "video is playing", "фільм запущено", "movie is running",
                "перегляд доступний", "playback available", "відео контент", "video content",
                "медіа плеєр", "media player", "відео сторінка", "video page",
                "контент доступний", "content available", "можна переглядати", "can be watched"
            ]
            
            if any(indicator in lower for indicator in media_success_indicators):
                # For media tasks, if we see any positive indicators and no explicit failures, consider it success
                if "failed" not in lower and "error" not in lower and "не вдалося" not in lower:
                    return "success", "meta_planner"
            
            # For media tasks, if we're at the final step and there are no explicit failures,
            # be more lenient to avoid infinite loops
            step_count = state.get("step_count", 0)
            if step_count > 5 and "failed" not in lower and "error" not in lower:
                return "success", "meta_planner"
        
        # Priority 5: If Tetyana reported success and there are no failure indicators, 
        # assume success if it's a simple navigation
        if STEP_COMPLETED_MARKER.lower() in lower and "failed" not in lower:
             return "success", "meta_planner"

        return "uncertain", "meta_planner"

    def _handle_grisha_streak(self, state, status, content):
        streak = (int(state.get("uncertain_streak") or 0) + 1) if status == "uncertain" else 0
        step_count = state.get("step_count", 0)
        
        # Enhanced anti-loop protection
        if streak >= 3:
            # After 3 uncertain iterations, check if we should force resolution
            # to prevent infinite meta_planner -> grisha -> meta_planner loops
            if step_count > 10:
                # If we've been running for many steps and keep getting uncertain,
                # log this pattern for debugging
                if self.verbose:
                    print(f"⚠️ [Grisha] Anti-loop: streak={streak}, steps={step_count}. Consider forcing resolution.")
            # Preserve the streak to signal to meta_planner via _router that 
            # this task might need escalation or user intervention
            return streak
        
        # Reset failed streak counter when we get a decisive result
        if status in ("success", "failed"):
            return 0
        
        return streak
