#!/usr/bin/env python3
"""Quick test script to verify Trinity loop fix."""

import os
import sys

# Suppress tokenizer warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from core.trinity import TrinityRuntime, TrinityPermissions

def test_simple_task():
    """Run a simple task and count events to verify no infinite loop."""
    print("🧪 Testing Trinity loop fix...")
    
    permissions = TrinityPermissions(
        allow_shell=True,
        allow_applescript=True,
        allow_gui=True,
        hyper_mode=True
    )
    
    rt = TrinityRuntime(verbose=True, permissions=permissions, preferred_language="uk")
    
    # Simple task that should complete without looping
    task = "Відкрий google.com у браузері"
    
    print(f"\n🚀 Starting task: {task}")
    print("=" * 60)
    
    event_count = 0
    max_events = 20  # If it exceeds this, we have a loop
    
    try:
        for event in rt.workflow.stream(
            {
                "messages": [{"role": "user", "content": task}],
                "current_agent": "meta_planner",
                "task_status": "pending",
                "step_count": 0,
                "replan_count": 0,
                "gui_mode": "auto",
            },
            {"recursion_limit": 30}
        ):
            event_count += 1
            print(f"\n📦 Event {event_count}:")
            for key in event:
                if key != "messages":
                    print(f"   {key}: {str(event[key])[:100]}")
            
            if event_count > max_events:
                print(f"\n❌ LOOP DETECTED! More than {max_events} events.")
                return False
                
    except Exception as e:
        print(f"\n⚠️ Error: {e}")
    
    print(f"\n{'=' * 60}")
    print(f"✅ Test completed with {event_count} events (limit: {max_events})")
    return event_count <= max_events

if __name__ == "__main__":
    success = test_simple_task()
    sys.exit(0 if success else 1)
