
import asyncio
import os
import sys

# Add project root to sys.path
sys.path.append(os.getcwd())

from dotenv import load_dotenv
load_dotenv()

from core.trinity.runtime import TrinityRuntime
from core.trinity.state import TrinityPermissions

async def run_diagnostic():
    perms = TrinityPermissions(allow_gui=True, allow_shell=True, allow_applescript=True)
    runtime = TrinityRuntime(verbose=True, permissions=perms)
    
    task = "Знайди в гуглі фільм Матриця (The Matrix) і відкрий посилання на стрімінговий сервіс"
    
    print(f"\n🚀 Running diagnostic task: {task}\n")
    
    # We use a larger recursion limit for full execution
    for event in runtime.run(task, recursion_limit=50):
        for node, state in event.items():
            print(f"\n--- Node: {node} ---")
            if "messages" in state:
                last_msg = state["messages"][-1]
                content = getattr(last_msg, 'content', str(last_msg))
                print(f"Agent reply: {content[:300]}...")
            if state.get("vibe_assistant_pause"):
                print("⚠️ PAUSED for review")
                return

if __name__ == "__main__":
    asyncio.run(run_diagnostic())
