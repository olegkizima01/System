
import os
import glob
import logging
from typing import Dict, Any, List, Optional
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from core.trinity.state import TrinityState
from core.llm import get_llm
from tui.logger import trace

logger = logging.getLogger(__name__)

class VibeAnalyst:
    """
    Doctor Vibe: The System Analyst.
    Investigates every execution, reads logs, and suggests improvements.
    """
    
    def __init__(self):
        self.llm = get_llm(model_id="anthropic/claude-3-5-sonnet-latest") # High intelligence for analysis
        
    def _read_recent_logs(self, lines: int = 200) -> str:
        """Reads recent CLI and State logs."""
        log_content = ""
        
        # 1. State Log (Logic)
        try:
            # Find latest state log
            state_logs = glob.glob("logs/trinity_state_*.log")
            if state_logs:
                latest_state = max(state_logs, key=os.path.getmtime)
                with open(latest_state, "r", encoding="utf-8") as f:
                    content = f.readlines()
                    log_content += f"\n--- TRINITY LOGIC LOG ({os.path.basename(latest_state)}) ---\n"
                    log_content += "".join(content[-lines:])
        except Exception as e:
            log_content += f"\n[Error reading state log: {e}]\n"

        # 2. CLI Log (Actions)
        try:
            cli_log_path = os.path.expanduser("~/.system_cli/logs/cli.log")
            if os.path.exists(cli_log_path):
                with open(cli_log_path, "r", encoding="utf-8") as f:
                    content = f.readlines()
                    log_content += f"\n--- CLI ACTION LOG ---\n"
                    log_content += "".join(content[-lines:])
        except Exception as e:
            log_content += f"\n[Error reading cli log: {e}]\n"
            
        return log_content

    async def analyze(self, state: TrinityState) -> Dict[str, Any]:
        """Main analysis entry point."""
        trace("💉 Doctor Vibe is analyzing execution...", "VibeAnalyst")
        
        task = state.get("original_task", "Unknown Task")
        logs = self._read_recent_logs(lines=150)
        plan = state.get("plan", [])
        status = state.get("last_step_status", "unknown")
        
        # Determine Verdict from state
        verdict = "SUCCESS" if status == "success" else "FAILURE"
        if not plan: verdict = "UNCERTAIN (No Plan)"
        
        prompt = f"""
You are Doctor Vibe, the Lead System Analyst for the Trinity AI System.
Your job is to INVESTIGATE the recent task execution and provide a "Post-Mortem" or "Success Analysis".

TASK: "{task}"
VERDICT: {verdict}

CONTEXT:
- The system just finished executing this task.
- You have access to the internal logic logs and the action logs below.

LOGS:
{logs}

INSTRUCTIONS:
1. Analyze the LOGS to understand what happened step-by-step.
2. If FAILED: Identify the ROOT CAUSE (e.g., Recursion, Timeout, Selector not found, Logic loop).
3. If SUCCESS: Identify any INEFFICIENCIES or risky actions (e.g., "Safari fallback", "Slow selector").
4. Suggest 1 specific SYSTEM IMPROVEMENT to prevent future issues.

FORMAT:
## 💉 Vibe Analysis: [Success/Failure]
**Root Cause/Observation**: <One sentence summary>
**Details**: <Bullet points of what happened>
**Prescription**: <Concrete improvement for the codebase or prompt>
"""
        
        messages = [
            SystemMessage(content="You are Doctor Vibe. Analytical, precise, slightly cynical but helpful."),
            HumanMessage(content=prompt)
        ]
        
        response = await self.llm.ainvoke(messages)
        
        # We don't change state much, just log/notify
        # We could potentially return a 'repair' action, but for now just report.
        report = response.content
        
        # Print to console prominently
        print(f"\n{report}\n")

        # Save report to state (optional)
        state["last_vibe_analysis"] = report
        
        return {"last_vibe_analysis": report}

# Expose callable for Graph
vibe_analyst_node = VibeAnalyst().analyze
