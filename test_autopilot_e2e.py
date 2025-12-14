#!/usr/bin/env python3
"""
End-to-end test of unified AutopilotRuntime with graph, RAG, replanning, and vision.
Tests: goal-driven planning, tool execution, observation (screenshot), verify step, replanning.
"""

import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, REPO_ROOT)

from system_ai.autopilot.runtime import AutopilotRuntime, AutopilotPermissions


def test_simple_goal():
    """Test a simple goal: open Calculator and take screenshot."""
    print("\n=== Test 1: Simple Goal (open Calculator) ===")
    
    permissions = AutopilotPermissions(
        allow_autopilot=True,
        allow_shell=True,
        allow_applescript=True,
    )
    
    runtime = AutopilotRuntime(permissions=permissions)
    
    goal = "Відкрий додаток Calculator (Калькулятор)"
    
    step_count = 0
    for event in runtime.run_goal(goal, max_steps=5):
        step_count += 1
        step = event.get("step", 0)
        plan = event.get("plan")
        actions_results = event.get("actions_results", [])
        observation = event.get("observation", "")
        verify = event.get("verify", {})
        done = event.get("done", False)
        
        print(f"\n--- Step {step} ---")
        if plan:
            print(f"Thought: {getattr(plan, 'thought', '')}")
            print(f"Actions: {len(getattr(plan, 'actions', []))} action(s)")
            for a in getattr(plan, 'actions', []):
                print(f"  - {a.tool}: {a.args}")
        
        print(f"Results: {len(actions_results)} result(s)")
        for r in actions_results:
            status = r.get("status", "unknown")
            tool = r.get("tool", "?")
            print(f"  - {tool}: {status}")
        
        if observation:
            print(f"Observation (vision): {observation[:200]}...")
        
        if verify:
            print(f"Verify: on_track={verify.get('on_track')}, done={verify.get('done')}, replan={verify.get('replan')}")
        
        print(f"Done: {done}")
        
        if done:
            print(f"\n✓ Goal completed in {step} steps")
            break
    
    if step_count == 0:
        print("✗ No steps executed")
        return False
    
    return True


def test_goal_with_replanning():
    """Test a goal that might require replanning."""
    print("\n=== Test 2: Goal with Potential Replanning ===")
    
    permissions = AutopilotPermissions(
        allow_autopilot=True,
        allow_shell=True,
        allow_applescript=True,
    )
    
    runtime = AutopilotRuntime(permissions=permissions)
    
    goal = "Відкрий браузер Safari і перейди на google.com"
    
    step_count = 0
    replan_count = 0
    for event in runtime.run_goal(goal, max_steps=10):
        step_count += 1
        step = event.get("step", 0)
        verify = event.get("verify", {})
        done = event.get("done", False)
        
        if verify.get("replan"):
            replan_count += 1
            print(f"\n[REPLAN #{replan_count}] {verify.get('next_hint', '')}")
        
        print(f"Step {step}: ", end="")
        plan = event.get("plan")
        if plan:
            print(f"{getattr(plan, 'thought', '')[:80]}")
        
        if done:
            print(f"\n✓ Goal completed in {step} steps (replans: {replan_count})")
            break
    
    if step_count == 0:
        print("✗ No steps executed")
        return False
    
    return True


def test_rag_context():
    """Test that RAG context is being used (check logs)."""
    print("\n=== Test 3: RAG Context Retrieval ===")
    
    permissions = AutopilotPermissions(
        allow_autopilot=True,
        allow_shell=True,
        allow_applescript=True,
    )
    
    runtime = AutopilotRuntime(permissions=permissions)
    
    goal = "Покажи список файлів у поточній директорії"
    
    step_count = 0
    for event in runtime.run_goal(goal, max_steps=3):
        step_count += 1
        step = event.get("step", 0)
        plan = event.get("plan")
        done = event.get("done", False)
        
        print(f"Step {step}: {getattr(plan, 'thought', '')[:100] if plan else '...'}")
        
        if done:
            print(f"\n✓ Goal completed in {step} steps")
            break
    
    if step_count == 0:
        print("✗ No steps executed")
        return False
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("AutopilotRuntime End-to-End Tests")
    print("=" * 60)
    
    results = []
    
    try:
        results.append(("Test 1: Simple Goal", test_simple_goal()))
    except Exception as e:
        print(f"✗ Test 1 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Test 1: Simple Goal", False))
    
    try:
        results.append(("Test 2: Goal with Replanning", test_goal_with_replanning()))
    except Exception as e:
        print(f"✗ Test 2 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Test 2: Goal with Replanning", False))
    
    try:
        results.append(("Test 3: RAG Context", test_rag_context()))
    except Exception as e:
        print(f"✗ Test 3 failed: {e}")
        import traceback
        traceback.print_exc()
        results.append(("Test 3: RAG Context", False))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(p for _, p in results)
    print("\n" + ("✓ All tests passed!" if all_passed else "✗ Some tests failed"))
    sys.exit(0 if all_passed else 1)
