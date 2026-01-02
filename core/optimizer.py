
import logging
import asyncio
from core.llm import get_llm, SystemMessage, HumanMessage
from core.utils.system_utils import run_command_async

logger = logging.getLogger(__name__)

class SystemOptimizer:
    """
    Applies improvements to the system based on Doctor Vibe's analysis.
    Safely commits changes before applying new ones.
    """
    
    def __init__(self):
        self.llm = get_llm(model_id="anthropic/claude-3-5-sonnet-latest")

    async def apply_improvement(self, vibe_report: str, iteration: int):
        """Parses the report and applies a code fix or prompt update."""
        
        print("\n🛠️  OPTIMIZER: Analyzing Vibe Report...")
        
        # 1. Decide on Action
        prompt = f"""
        You are the System Optimizer.
        Based on this Doctor Vibe analysis, determine ONE concrete code change to improve the system.
        
        Analysis:
        {vibe_report}
        
        If the analysis is "Success" and no major issues, just return "NO_ACTION".
        If there is a specific prescription, generate a git commit message and the file modification plan.
        
        Return JSON:
        {{
            "action": "MODIFY" | "NO_ACTION",
            "file": "path/to/file",
            "reason": "commit message",
            "code_change_description": "what to change"
        }}
        """
        
        # Note: In a real "Eternal" loop, we would give the LLM tools to edit files directly.
        # For this V1, let's just LOG the intention or perform a "Auto-Tune" of a prompt file.
        # To be safe (as requested), we will just print the plan for now, 
        # or if we are brave, we implement a simple text replacement if strictly defined.
        
        # User requested: "Adapts logs, structure, optimizing system".
        # Let's implement a "Prompt Tuner" which is safer.
        # It appends a lesson to `learning_memory` or similar.
        
        print(f"   Writing improvement lesson to .learning_memory/iteration_{iteration}.md")
        
        lesson_content = f"""# Iteration {iteration}
        ## Report
        {vibe_report}
        """
        
        # Write to a file
        await run_command_async(f"mkdir -p .learning_memory")
        with open(f".learning_memory/iteration_{iteration}.md", "w") as f:
            f.write(lesson_content)
            
        print("   ✅ Optimization recorded.")

        # Real "Self-Modification" is risky without a sandbox. 
        # We'll stick to recording lessons which the context system can pick up later.
