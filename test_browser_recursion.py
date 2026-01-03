#!/usr/bin/env python3
"""Test Trinity with real browser task to verify anti-loop fixes."""

import os
import sys

# Recursion limit для Python (не плутати з LangGraph recursion_limit)
sys.setrecursionlimit(500)

# Suppress warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from core.trinity import TrinityRuntime, TrinityPermissions

def test_browser_task():
    """Test with browser task that previously caused loops."""
    print("🧪 Тест: Браузерне завдання (реальний запуск)")
    print("=" * 60)
    
    permissions = TrinityPermissions(
        allow_shell=True,
        allow_applescript=True,
        allow_file_write=True,
        allow_gui=True,
        allow_shortcuts=True,
        hyper_mode=False
    )
    
    runtime = TrinityRuntime(
        verbose=True,
        permissions=permissions,
        preferred_language="uk"
    )
    
    # Task that previously caused recursion
    task = "Відкрий YouTube і знайди Архангел виконавець"
    
    print(f"📋 Завдання: {task}\n")
    
    event_count = 0
    step_count = 0
    agent_sequence = []
    
    try:
        # Use lower recursion_limit to catch issues early
        for event in runtime.run(task, gui_mode="auto", execution_mode="native", recursion_limit=100):
            event_count += 1
            
            for node_name, state_update in event.items():
                agent_sequence.append(node_name)
                step_count = state_update.get("step_count", step_count)
                replan_count = state_update.get("replan_count", 0)
                
                # Print progress
                print(f"  [{event_count:02d}] {node_name:15s} (step={step_count}, replan={replan_count})")
                
                # Safety check
                if event_count > 50:
                    print(f"\n⚠️ ABORT: Event count exceeded 50!")
                    return False
                    
                if step_count > 30:
                    print(f"\n⚠️ ABORT: Step count exceeded 30!")
                    return False
    
    except RecursionError as e:
        print(f"\n❌ RECURSION ERROR після {event_count} подій!")
        print(f"   Послідовність агентів: {' → '.join(agent_sequence[-20:])}")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print(f"\n✅ Завдання завершено успішно!")
    print(f"   Події: {event_count}, Кроки: {step_count}")
    print(f"   Послідовність: {' → '.join(agent_sequence)}")
    
    # Validate no excessive looping
    if event_count > 40:
        print(f"⚠️ WARN: Багато подій ({event_count}), можливі субоптимальні цикли")
    
    return True

if __name__ == "__main__":
    print("🚀 Запуск тесту рекурсії з браузерним завданням\n")
    success = test_browser_task()
    print("\n" + "=" * 60)
    if success:
        print("🎉 ТЕСТ ПРОЙДЕНО!")
    else:
        print("❌ ТЕСТ НЕ ПРОЙДЕНО!")
    print("=" * 60)
    sys.exit(0 if success else 1)
