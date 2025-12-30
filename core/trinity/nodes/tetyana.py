import os
import time
import json
import re
import difflib
from typing import List, Dict, Any, Optional
from langchain_core.messages import AIMessage
from core.trinity.state import TrinityState
from core.constants import VOICE_MARKER, UNKNOWN_STEP, STEP_COMPLETED_MARKER, DEFAULT_MODEL_FALLBACK
from core.agents.tetyana import get_tetyana_prompt
from providers.copilot import CopilotLLM

class TetyanaMixin:
    """Mixin for TrinityRuntime containing Tetyana (Executor) logic."""

    def _tetyana_node(self, state: TrinityState):
        """Executes the next step in the plan using Tetyana (Executor)."""
        if self.verbose:
            print(f"🔧 {VOICE_MARKER} [Tetyana] Executing step...")
        
        context = state.get("messages", [])
        original_task = state.get("original_task") or UNKNOWN_STEP
        last_msg = getattr(context[-1], "content", UNKNOWN_STEP) if context and context[-1] else UNKNOWN_STEP

        # 1. Prepare context and prompt
        full_context = self._prepare_tetyana_context(state, original_task, last_msg)
        try:
            tools_desc = self.registry.list_tools(task_type=state.get("task_type"))
        except TypeError:
            tools_desc = self.registry.list_tools()

        prompt = get_tetyana_prompt(
            full_context,
            tools_desc=tools_desc,
            preferred_language=self.preferred_language,
            vision_context=self.vision_context_manager.current_context,
        )

        # 2. Invoke LLM with rate limiting delay
        time.sleep(1.5)  # Delay to prevent API rate limiting
        tetyana_llm = self._init_tetyana_llm()
        
        # Ensure LLM knows how to use tools via custom JSON protocol in CopilotLLM
        try:
            tools_defs = self.registry.get_all_tool_definitions(task_type=state.get("task_type"))
        except TypeError:
            tools_defs = self.registry.get_all_tool_definitions()
        if hasattr(tetyana_llm, "bind_tools") and tools_defs:
            tetyana_llm = tetyana_llm.bind_tools(tools_defs)
        
        try:
            def on_delta(chunk): self._deduplicated_stream("tetyana", chunk)
            response = tetyana_llm.invoke_with_stream(prompt.format_messages(), on_delta=on_delta)
            
            content = getattr(response, "content", "") if response else ""
            tool_calls = getattr(response, "tool_calls", []) if response and hasattr(response, 'tool_calls') else []

            # Determine dev_edit_mode
            # Consider environment override in addition to state value
            if self._is_env_true("TRINITY_DEV_BY_VIBE", False):
                dev_edit_mode = "vibe"
            else:
                dev_edit_mode = str(state.get("dev_edit_mode") or "").strip().lower()

            # If Doctor Vibe is enabled and the LLM content explicitly mentions
            # 'Windsurf', pre-emptively pause so a human (Doctor Vibe) can intervene.
            try:
                lower_content = (content or "").lower()
                if dev_edit_mode == "vibe" and "windsurf" in lower_content:
                    # Create pause and return a sanitized message to avoid displaying 'Windsurf'
                    pause = self._create_vibe_assistant_pause_state(state, "doctor_vibe_dev", "Doctor Vibe: Manual dev intervention required for this step")
                    try:
                        diags = self._collect_pause_diagnostics(state)
                        if diags:
                            pause["diagnostics"] = diags
                    except Exception:
                        pass
                    # Sanitize content for UI (replace Windsurf with Doctor Vibe note)
                    sanitized = re.sub(r"(?i)windsurf", "Doctor Vibe (paused)", str(content or ""))
                    return {**state, "messages": list(context) + [AIMessage(content=sanitized)], "vibe_assistant_pause": pause}
            except Exception:
                pass

            # 3. Handle acknowledgment loops
            if not tool_calls and content:
                ack_retry = self._check_tetyana_acknowledgment(content, context)
                if ack_retry:
                    return ack_retry

            # 4. Execute tools
            # If the runtime is configured to let Doctor Vibe handle DEV edits,
            # pause and notify the Vibe CLI Assistant instead of executing dev
            # tool calls.
            dev_tools = {"send_to_windsurf", "open_file_in_windsurf", "open_project_in_windsurf", "write_file", "copy_file"}
            if dev_edit_mode == "vibe" and any((t.get("name") in dev_tools) for t in (tool_calls or [])):
                # Create a pause state for Doctor Vibe to intervene and return
                # a paused state so execution stops until human continues.
                pause = self._create_vibe_assistant_pause_state(state, "doctor_vibe_dev", "Doctor Vibe: Manual dev intervention required for this step")
                # Enhance pause with diagnostics about the tools that triggered it
                try:
                    diags = self._collect_pause_diagnostics(state, tools=tool_calls)
                    if diags:
                        pause["diagnostics"] = diags
                except Exception:
                    pass
                return {**state, "vibe_assistant_pause": pause}

            results, pause_info, had_failure = self._execute_tetyana_tools(state, tool_calls)
            
            # 5. Process tool responses
            content = self._process_tetyana_tool_results(content, results, had_failure, pause_info)

            # 6. Fallback and Final State
            return self._finalize_tetyana_state(state, context, content, tool_calls, had_failure, pause_info)

        except Exception as e:
            if self.verbose:
                print(f"⚠️ [Tetyana] Exception: {e}")
            return self._handle_tetyana_error(state, context, e)

    def _init_tetyana_llm(self):
        """Initialize LLM for Tetyana node."""
        tetyana_model = os.getenv("TETYANA_MODEL") or os.getenv("COPILOT_MODEL") or DEFAULT_MODEL_FALLBACK
        return self.llm if hasattr(self, 'llm') and self.llm else CopilotLLM(model_name=tetyana_model)

    def _process_tetyana_tool_results(self, content: str, results: List[str], had_failure: bool, pause_info: Any) -> str:
        """Append tool results and success markers to content."""
        if not results:
            return content
            
        content_with_results = content + "\\n\\nTool Results:\\n" + "\\n".join(results)
        if not had_failure and not pause_info:
            return self._append_success_marker(content_with_results)
        return content_with_results

    def _prepare_tetyana_context(self, state, original_task, last_msg):
        task_type = state.get("task_type")
        requires_windsurf = state.get("requires_windsurf")
        dev_edit_mode = state.get("dev_edit_mode")
        
        routing = f"\\n\\n[ROUTING] task_type={task_type} requires_windsurf={requires_windsurf} dev_edit_mode={dev_edit_mode}"
        retry = ""
        fail_count = int(state.get("current_step_fail_count") or 0)
        if fail_count > 0:
            retry = f"\\n\\n[SYSTEM NOTICE] This is retry #{fail_count} for this step. Adjust approach."
            
        return f"Global Goal: {original_task}\\nRequest: {last_msg}{routing}{retry}"

    def _check_tetyana_acknowledgment(self, content, context):
        lower_content = content.lower()
        # Using word boundaries to avoid matching "ок" inside words like "список"
        acknowledgment_patterns = [r"\\bзрозуміла\\b", r"\\bзрозумів\\b", r"\\bок\\b", r"\\bдобре\\b", r"\\bпочинаю\\b", r"\\bбуду використовувати\\b"]
        if any(re.search(p, lower_content) for p in acknowledgment_patterns) and len(lower_content) < 300:
            if self.verbose: print("⚠️ [Tetyana] Acknowledgment loop detected.")
            new_msg = AIMessage(content=f"{VOICE_MARKER} Error: No tool call provided. USE A TOOL. {content}")
            return {"messages": context + [new_msg], "last_step_status": "failed"}
        return None

    def _is_env_true(self, var: str, default: bool = False) -> bool:
        """Check if environment variable is true."""
        val = str(os.getenv(var) or "").strip().lower()
        if not val:
            return default
        return val in {"1", "true", "yes", "on"}

    def _execute_tetyana_tools(self, state, tool_calls):
        results = []
        pause_info = None
        had_failure = False
        
        for tool in (tool_calls or []):
            name = tool.get("name")
            args = tool.get("args") or {}
            
            # Permission checks
            pause_info = self._check_tool_permissions(state, name, args)
            if pause_info:
                results.append(f"[BLOCKED] {name}: permission required")
                continue
            
            # Task-type constraints
            blocked_reason = self._check_task_constraints(state, name, args)
            if blocked_reason:
                results.append(blocked_reason)
                continue

            # Execution
            # If Doctor Vibe is in charge for DEV edits, handle dev tools specially
            dev_mode = str(state.get("dev_edit_mode") or "").strip().lower()
            vibe_auto = bool(state.get("vibe_auto_apply") or self._is_env_true("TRINITY_VIBE_AUTO_APPLY", False))

            if dev_mode == "vibe" and name in {"open_file_in_windsurf", "send_to_windsurf", "open_project_in_windsurf"}:
                # Skip opening Windsurf; either create a pause or auto-apply changes
                if vibe_auto:
                    try:
                        exec_res = self.registry.execute(name, args, task_type=state.get("task_type"))
                        results.append(f"[VIBE-AUTO] Executed {name}: {exec_res}")
                        try:
                            diags = {"files": [args.get('path') or args.get('dst')], "diffs": [{"file": args.get('path') or args.get('dst'), "diff": "N/A"}]}
                            self.vibe_assistant.handle_pause_request({"reason": "doctor_vibe_edit_done", "message": f"Doctor Vibe: Applied changes to {name}", "diagnostics": diags})
                        except Exception:
                            pass
                        continue
                    except Exception:
                        results.append(f"[VIBE-AUTO] Failed to execute {name}")
                        pause_info = {"permission": "doctor_vibe", "message": "Doctor Vibe: Manual dev intervention required"}
                        continue
                results.append(f"[BLOCKED] {name}: Doctor Vibe required")
                pause_info = {"permission": "doctor_vibe", "message": "Doctor Vibe: Manual dev intervention required"}
                continue

            if name in {"write_file", "copy_file"} and dev_mode == "vibe":
                # Show diff preview and let Doctor Vibe auto-apply if enabled
                path = args.get("path") or args.get("dst") or ""
                old_content = ""
                try:
                    full = path if os.path.isabs(path) else os.path.join(self._get_git_root() or os.getcwd(), path)
                    if os.path.exists(full):
                        with open(full, "r", encoding="utf-8", errors="ignore") as f:
                            old_content = f.read()
                except Exception:
                    old_content = ""

                new_content = args.get("content") or ""
                diff = "\\n".join(difflib.unified_diff(old_content.splitlines(), str(new_content).splitlines(), lineterm="", n=3))

                # Notify Doctor Vibe with diagnostics before applying
                diag = {"files": [path], "diffs": [{"file": path, "diff": diff}], "stack_trace": None}
                self.vibe_assistant.handle_pause_request({"reason": "doctor_vibe_edit", "message": f"Doctor Vibe: Applying changes to {path}", "diagnostics": diag})

                if not vibe_auto:
                    # Pause execution to wait for human approval
                    pause_info = {"permission": "doctor_vibe", "message": "Doctor Vibe: Awaiting human approval for edit"}
                    results.append(f"[PENDING VIBE] {path}")
                    continue

                # auto-apply: execute write via registry
                try:
                    try:
                        res_str = self.registry.execute(name, args, task_type=state.get("task_type"))
                    except TypeError:
                        res_str = self.registry.execute(name, args)
                except Exception as e:
                    res_str = f"Error: {e}"

                # after apply, show confirmation with diff
                self.vibe_assistant.handle_pause_request({"reason": "doctor_vibe_edit_done", "message": f"Doctor Vibe: Applied changes to {path}", "diagnostics": {"files": [path], "diffs": [{"file": path, "diff": diff}]}})
                results.append(f"Result for {name}: {res_str}")
                if self._is_execution_failure(res_str):
                    had_failure = True
                continue

            if name in {"browser_get_links", "browser_get_text", "browser_get_visible_html", "browser_screenshot"}:
                time.sleep(2.0)

            # For run_shell, inject sudo password if requested and available
            if name == "run_shell":
                if args.get("use_sudo") and str(os.getenv("SUDO_PASSWORD") or "").strip():
                    cmd = args.get("cmd") or args.get("command") or ""
                    if cmd:
                        sudo_prefix = f"echo {os.getenv('SUDO_PASSWORD')} | sudo -S "
                        args = {**args, "cmd": sudo_prefix + cmd}

            res_str = None
            try:
                try:
                    res_str = self.registry.execute(name, args, task_type=state.get("task_type"))
                except TypeError:
                    res_str = self.registry.execute(name, args)
            except Exception as e:
                res_str = f"Error: {e}"
            results.append(f"Result for {name}: {res_str}")
            
            # Failure tracking
            if self._is_execution_failure(res_str):
                had_failure = True
                
        return results, pause_info, had_failure

    def _check_tool_permissions(self, state, name, args):
        perm_map = {
            "file_write": (["write_file", "copy_file"], self.permissions.allow_file_write),
            "shell": (["run_shell", "open_file_in_windsurf", "open_project_in_windsurf"], self.permissions.allow_shell),
            "applescript": (["run_applescript", "native_applescript"], self.permissions.allow_applescript),
            "gui": (["move_mouse", "click_mouse", "click", "type_text", "press_key"], self.permissions.allow_gui),
            "shortcuts": (["run_shortcut"], self.permissions.allow_shortcuts),
        }
        
        for perm, (tools, allowed) in perm_map.items():
            if name in tools and not (allowed or self.permissions.hyper_mode):
                # Map internal permission name to macOS privacy pane name where they differ
                mac_pane = perm
                if perm == "applescript" or perm == "shortcuts" or perm == "shell":
                    mac_pane = "automation"
                elif perm == "gui":
                    mac_pane = "accessibility"
                
                return {
                    "permission": perm, 
                    "mac_pane": mac_pane,
                    "message": f"Permission required for {perm} (macOS {mac_pane}).", 
                    "blocked_tool": name, 
                    "blocked_args": args
                }
        return None

    def _check_task_constraints(self, state, name, args):
        task_type = state.get("task_type")
        windsurf_tools = {"send_to_windsurf", "open_file_in_windsurf", "open_project_in_windsurf"}
        
        if task_type == "GENERAL":
            if name in windsurf_tools:
                return f"[BLOCKED] {name}: GENERAL task must not use Windsurf dev subsystem"
            if name in {"write_file", "copy_file"} and not self._is_safe_path(name, args):
                return f"[BLOCKED] {name}: GENERAL write allowed only outside repo."
        
        if task_type in {"DEV", "UNKNOWN"} and state.get("requires_windsurf") and state.get("dev_edit_mode") == "windsurf":
            if name in {"write_file", "copy_file"}:
                return f"[BLOCKED] {name}: DEV task requires Windsurf-first"
        return None

    def _is_safe_path(self, name, args):
        try:
            from system_ai.tools.filesystem import _normalize_special_paths
            git_root = self._get_git_root() or ""
            home = os.path.expanduser("~")
            path = args.get("path") if name == "write_file" else args.get("dst")
            ap = os.path.abspath(os.path.expanduser(_normalize_special_paths(str(path or ""))))
            if git_root and (ap == git_root or ap.startswith(git_root + os.sep)): return False
            return ap.startswith(home + os.sep) or ap.startswith(os.path.join(os.sep, "tmp") + os.sep)
        except Exception: return False

    def _is_execution_failure(self, res_str):
        try:
            res_dict = json.loads(res_str)
            if isinstance(res_dict, dict):
                status = str(res_dict.get("status", res_dict.get("state", ""))).lower()
                # Check for error, captcha, or warning statuses
                if status in {"error", "failed", "captcha", "failure"}:
                    return True
                # Warning with empty links is a failure (blocked page)
                if status == "warning" and not res_dict.get("links"):
                    return True
                # Check has_captcha flag for backward compatibility
                if res_dict.get("has_captcha"):
                    return True
                # Check for captcha/blocked indicators in output or URL
                output = str(res_dict.get("output", "") or res_dict.get("url", "") or res_dict.get("error", ""))
                captcha_markers = ["sorry/index", "recaptcha", "hcaptcha", "unusual traffic", "captcha"]
                if any(k in output.lower() for k in captcha_markers):
                    return True
        except Exception:
            if str(res_str).strip().startswith("Error"):
                return True
        res_lower = str(res_str).lower()
        return "sorry/index" in res_lower or "recaptcha" in res_lower or "captcha" in res_lower

    def _append_success_marker(self, content):
        if STEP_COMPLETED_MARKER not in content:
            msg = "Actions completed." if self.preferred_language != "uk" else "Дії виконано."
            return f"{content}\\n\\n{STEP_COMPLETED_MARKER} {msg}"
        return content

    def _finalize_tetyana_state(self, state, context, content, tool_calls, had_failure, pause_info):
        # Sanitize LLM messages that reference Windsurf when Doctor Vibe handles dev edits
        try:
            dev_mode = str(state.get("dev_edit_mode") or "").strip().lower()
            if dev_mode == "vibe" and content and "windsurf" in str(content).lower():
                content = re.sub(r"(?i)windsurf", "Doctor Vibe (paused)", str(content))
        except Exception:
            pass

        updated_messages = list(context) + [AIMessage(content=content)]
        used_tools = [t.get("name") for t in tool_calls] if tool_calls else []

        if pause_info:
            # Convert low-level pause info (permission map) into a full Vibe pause
            reason = pause_info.get("permission") or "permission_required"
            message = pause_info.get("message") or "Permission required for action."
            pause = self._create_vibe_assistant_pause_state(state, "permission_required", message)
            try:
                pause["permission"] = pause_info.get("permission")
                pause["mac_pane"] = pause_info.get("mac_pane")
                pause["blocked_tool"] = pause_info.get("blocked_tool")
                pause["blocked_args"] = pause_info.get("blocked_args")
                pause["auto_resume_available"] = bool(self._is_env_true("TRINITY_VIBE_AUTO_RESUME_PERMISSIONS", False))
            except Exception:
                pass
            return {**state, "messages": updated_messages, "vibe_assistant_pause": pause, "last_step_status": "uncertain", "current_agent": "meta_planner"}
            
        if had_failure and state.get("execution_mode") != "gui" and state.get("gui_mode") in {"auto", "on"} and not state.get("gui_fallback_attempted"):
            return {**state, "messages": updated_messages, "execution_mode": "gui", "gui_fallback_attempted": True, "last_step_status": "failed", "current_agent": "tetyana"}

        return {
            **state,
            "messages": updated_messages,
            "current_agent": "grisha",
            "last_step_status": "failed" if had_failure else "success",
            "tetyana_used_tools": used_tools,
            "tetyana_tool_context": self._extract_tool_context(tool_calls)
        }

    def _extract_tool_context(self, tool_calls):
        ctx = {}
        for t in (tool_calls or []):
            args = t.get("args") or {}
            for k in ["app_name", "app", "window_title", "window", "url"]:
                if k in args: ctx[k] = args[k]
        return ctx

    def _handle_tetyana_error(self, state, context, e):
        err_msg = f"Error invoking Tetyana: {e}"
        return {**state, "messages": list(context) + [AIMessage(content=err_msg)], "last_step_status": "failed", "current_agent": "grisha"}
