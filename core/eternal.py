
import asyncio
import logging
import random
from datetime import datetime
from typing import List, Dict, Any

from core.llm import get_llm, SystemMessage, HumanMessage
from core.trinity.execution import TrinityExecutionMixin
from core.trinity.state import TrinityState
from core.trinity.nodes.vibe import vibe_analyst_node
from tui.logger import trace
from core.optimizer import SystemOptimizer

logger = logging.getLogger(__name__)

class EternalEngine:
    """
    The Engine of Perceptual Logic.
    Continuously generates tasks, executes them, analyzes results, and optimizes the system.
    """
    
    def __init__(self):
        self.llm = get_llm(model_id="anthropic/claude-3-5-sonnet-latest")
        self.optimizer = SystemOptimizer()
        self.iteration = 0
        self.running = False

    async def run_forever(self):
        """Main Infinite Loop."""
        self.running = True
        logger.info("🔥 ETERNAL ENGINE STARTED. Press Ctrl+C to stop.")
        
        while self.running:
            self.iteration += 1
            logger.info(f"🔁 === ITERATION {self.iteration} ===")
            
            # 1. Generate Task
            task = await self._generate_task()
            logger.info(f"📋 Generated Task: {task}")
            
            # 2. Execute Task (using Trinity Runtime logic)
            # We need a fresh Trinity instance or similar entry point.
            # For now, we simulate the runtime call or use a helper if available.
            # Since Trinity is usually run via CLI, we might invoke it conceptually or import.
            # To keep it clean, we'll use a simplified execution wrapper here 
            # or realistically, we should instantiate the graph.
            
            success, vibe_report = await self._execute_and_analyze(task)
            
            # 3. Optimize
            logger.info(f"💊 Doctor Vibe Report: {vibe_report[:100]}...")
            if vibe_report:
                await self.optimizer.apply_improvement(vibe_report, self.iteration)
            
            # 4. Sleep briefly
            await asyncio.sleep(5)

    async def _generate_task(self) -> str:
        """Generates a novel, challenging task for the system."""
        prompt = f"""
        Generate a unique, challenging, but achievable task for a MacOS AI Agent.
        The task should test different capabilities: Web browsing, File management, System diagnostics, or Coding.
        Current Iteration: {self.iteration}
        
        Return ONLY the task description string. No quotes.
        Examples:
        - "Check the disk usage of the home directory and save top 5 folders to a file."
        - "Open Wikipedia, find the article on 'Entropy', and summarize the first paragraph."
        """
        response = await self.llm.ainvoke([HumanMessage(content=prompt)])
        return response.content.strip()

    async def _execute_and_analyze(self, task: str):
        """Executes the task using Trinity and gets Vibe's analysis."""
        logger.info("🚀 Executing with Trinity...")
        
        try:
            from core.trinity import TrinityRuntime, TrinityPermissions
            
            # Setup permissions for "Eternal" mode
            permissions = TrinityPermissions(
                allow_shell=True,
                allow_applescript=True, 
                allow_file_write=True,
                allow_gui=True,
                allow_shortcuts=True,
                hyper_mode=False
            )
            
            # Initialize Runtime
            # Note: We are in a dedicated thread, so blocking calls are acceptable.
            runtime = TrinityRuntime(
                verbose=True, 
                permissions=permissions, 
                learning_mode=True
            )
            
            last_state = {}
            # Execute synchronously (generator)
            for event in runtime.run(task):
                for node_name, node_state in event.items():
                    last_state = node_state
            
            # Extract Vibe report from the final state
            # Vibe writes to 'last_vibe_analysis' in the state if it ran.
            report = last_state.get("last_vibe_analysis", "No analysis generated.")
            success = last_state.get("last_step_status") == "success"
            
            return success, report
            
        except Exception as e:
            logger.error(f"❌ Execution Error: {e}")
            import traceback
            traceback.print_exc()
            return False, f"Execution failed with error: {e}"

if __name__ == "__main__":
    eng = EternalEngine()
    asyncio.run(eng.run_forever())
