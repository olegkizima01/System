import json
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, Generator, List, Optional, Tuple

from system_ai.memory.summary_memory import SummaryMemory
from system_ai.rag.rag_pipeline import RagPipeline
from system_ai.tools import executor
from system_ai.tools.screenshot import take_screenshot
from system_ai.tools.vision import summarize_image_for_prompt


try:
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
except Exception:  # pragma: no cover
    AIMessage = HumanMessage = SystemMessage = None


try:
    from providers.copilot import CopilotLLM
except Exception:  # pragma: no cover
    CopilotLLM = None


try:
    from dotenv import load_dotenv  # type: ignore
except Exception:  # pragma: no cover
    load_dotenv = None


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")


def _load_env() -> None:
    if load_dotenv is None:
        return
    load_dotenv(os.path.join(REPO_ROOT, ".env"))


SYSTEM_PROMPT = """Ти — системний автопілот, що керує локальним macOS-комп'ютером користувача.

Ти працюєш ітеративно в циклі: PLAN -> ACT -> OBSERVE -> VERIFY -> NEXT.

Доступні інструменти:
- open_app: args {"name": string}
- run_shell: args {"command": string}
- run_applescript: args {"script": string}
- take_screenshot: args {"app_name": string|null}

Правила:
- На кожному кроці ВІДПОВІДАЙ СТРОГО валідним JSON (без markdown/пояснень).
- Формат відповіді:
{
  "thought": "коротко що робиш",
  "summary": "оновлений підсумок стану (memory)",
  "actions": [ {"tool": "...", "args": {...}} ],
  "done": true|false,
  "result_message": "що сказати користувачу"
}

Після виконання actions, ти отримаєш tool_results. Використай їх для наступного планування.
"""


@dataclass
class ToolAction:
    tool: str
    args: Dict[str, Any]


@dataclass
class StepPlan:
    thought: str
    summary: str
    actions: List[ToolAction]
    done: bool
    result_message: str
    raw_response: str


class AutopilotAgent:
    def __init__(
        self,
        *,
        allow_autopilot: bool,
        allow_shell: bool,
        allow_applescript: bool,
        persist_dir: str = "~/.system_cli/chroma",
    ) -> None:
        if CopilotLLM is None or SystemMessage is None or HumanMessage is None:
            raise RuntimeError("LLM dependencies not available")

        _load_env()

        self.llm = CopilotLLM()
        self.allow_autopilot = allow_autopilot
        self.allow_shell = allow_shell
        self.allow_applescript = allow_applescript
        self.memory = SummaryMemory()
        self.rag = RagPipeline(persist_dir=persist_dir)

    def _parse_plan(self, ai_message: Any) -> StepPlan:
        text = str(getattr(ai_message, "content", "") or "")
        match = re.search(r"\{[\s\S]*\}", text)
        json_str = match.group(0) if match else text
        try:
            data = json.loads(json_str)
        except Exception:
            return StepPlan(
                thought="Модель повернула не-JSON відповідь",
                summary=self.memory.summary,
                actions=[],
                done=True,
                result_message=text,
                raw_response=text,
            )

        actions_raw = data.get("actions") or []
        actions: List[ToolAction] = []
        for item in actions_raw:
            tool = str(item.get("tool", ""))
            args = item.get("args") or {}
            if tool:
                actions.append(ToolAction(tool=tool, args=args))

        return StepPlan(
            thought=str(data.get("thought", "")),
            summary=str(data.get("summary", "")),
            actions=actions,
            done=bool(data.get("done", False)),
            result_message=str(data.get("result_message", "")) or text,
            raw_response=text,
        )

    def _execute(self, actions: List[ToolAction]) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for a in actions:
            if a.tool == "open_app":
                results.append(executor.open_app(str(a.args.get("name", ""))))
            elif a.tool == "run_shell":
                results.append(executor.run_shell(str(a.args.get("command", "")), allow=self.allow_shell and self.allow_autopilot))
            elif a.tool == "run_applescript":
                results.append(executor.run_applescript(str(a.args.get("script", "")), allow=self.allow_applescript and self.allow_autopilot))
            elif a.tool == "take_screenshot":
                app_name = a.args.get("app_name")
                results.append(take_screenshot(str(app_name)) if app_name else take_screenshot(None))
            else:
                results.append({"tool": a.tool, "status": "error", "error": "Unknown tool"})
        return results

    def run_task(self, task: str, *, max_steps: int = 30) -> Generator[Dict[str, Any], None, None]:
        if not self.allow_autopilot:
            raise RuntimeError("Autopilot not confirmed")

        history: List[str] = []
        last_results: List[Dict[str, Any]] = []

        for step in range(1, max_steps + 1):
            retrieved = self.rag.retrieve(task, k=5)

            user_text = json.dumps(
                {
                    "task": task,
                    "summary_memory": self.memory.summary,
                    "history_tail": history[-5:],
                    "rag": retrieved,
                    "last_results": last_results[-8:],
                },
                ensure_ascii=False,
            )

            # Add last screenshot observation as TEXT (Copilot multimodal is not reliable here)
            last_shot = next((r for r in reversed(last_results) if r.get("tool") == "take_screenshot" and r.get("status") == "success"), None)
            if last_shot:
                path = str(last_shot.get("path") or "")
                if path:
                    user_text = user_text + "\n\n" + summarize_image_for_prompt(path)

            messages: List[Any] = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=user_text)]

            ai_msg = self.llm.invoke(messages)
            plan = self._parse_plan(ai_msg)

            if plan.summary:
                self.memory.update(plan.summary)

            action_results = self._execute(plan.actions)

            # OBSERVE: always capture a screenshot after actions unless already captured in this step
            if not any(r.get("tool") == "take_screenshot" for r in action_results):
                try:
                    action_results.append(take_screenshot(None))
                except Exception:
                    pass

            # Store a compact trace in RAG (best-effort)
            try:
                self.rag.ingest_text(
                    json.dumps(
                        {
                            "step": step,
                            "task": task,
                            "thought": plan.thought,
                            "result_message": plan.result_message,
                            "actions": [a.__dict__ for a in plan.actions],
                            "tool_results": action_results,
                        },
                        ensure_ascii=False,
                    ),
                    metadata={"type": "autopilot_step", "step": step},
                )
            except Exception:
                pass

            history.append(f"Step {step}: {plan.thought} | {plan.result_message}")
            last_results.extend(action_results)

            yield {
                "step": step,
                "plan": plan,
                "actions_results": action_results,
                "done": plan.done,
            }

            if plan.done:
                break
