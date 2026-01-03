#!/usr/bin/env python3
"""
Test Trinity with real browser task to verify GoalStack recursion.

GoalStack забезпечує правильну рекурсію:
- Якщо падає завдання 3, головна ціль стає 3
- 3 розбивається на 3.1, 3.2, 3.3
- Якщо падає 3.2, ціль стає 3.2 -> 3.2.1, 3.2.2, 3.2.3
- По досягненню підцілі, повертається на попередній рівень
"""

import os
import sys

# Recursion limit для Python (не плутати з LangGraph recursion_limit)
sys.setrecursionlimit(500)

# Suppress warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from core.trinity import TrinityRuntime, TrinityPermissions
from core.trinity.goal_stack import GoalStack


def test_goal_stack_demo():
    """Demonstrate the GoalStack recursive decomposition."""
    print("🧪 Демо: GoalStack рекурсивна декомпозиція")
    print("=" * 60)
    
    # Симуляція сценарію з README
    stack = GoalStack("Відкрий YouTube і знайди Архангел виконавець")
    
    print(f"\n📋 Головна ціль: {stack.current_goal.description}")
    print(f"   Шлях: {stack.get_goal_path()}\n")
    
    # Симулюємо виконання плану
    plan = [
        ("1", "Відкрити браузер", True),
        ("2", "Перейти на YouTube", True),
        ("3", "Знайти відео", False),  # Це завдання провалиться
    ]
    
    # Декомпозуємо головну ціль
    stack.decompose_current_goal([
        {"description": task[1]} for task in plan
    ], "Початкова декомпозиція")
    
    print("📝 План виконання:")
    for task_id, desc, will_succeed in plan:
        status = "✓" if will_succeed else "✗"
        print(f"   {task_id}. {desc} [{status}]")
    
    print(f"\n🔄 Симуляція виконання:\n")
    
    # Виконуємо 1 і 2
    print(f"   [{stack.current_goal_id}] Відкрити браузер...")
    result = stack.complete_current_subtask()
    print(f"   ✅ Завершено -> {result}")
    
    print(f"   [{stack.current_goal_id}] Перейти на YouTube...")
    result = stack.complete_current_subtask()
    print(f"   ✅ Завершено -> {result}")
    
    # Завдання 3 провалюється
    print(f"   [{stack.current_goal_id}] Знайти відео...")
    for i in range(3):
        action = stack.handle_failure(f"Пошук не працює, спроба {i+1}")
        print(f"      ⚠️ Збій #{i+1} -> {action}")
    
    # Декомпозуємо завдання 3
    print(f"\n   🔀 Декомпозиція завдання 3:")
    stack.decompose_current_goal([
        {"description": "3.1: Знайти пошукове поле"},
        {"description": "3.2: Ввести текст пошуку"},
        {"description": "3.3: Натиснути кнопку пошуку"},
    ], "Пошук не працює напряму")
    
    print(f"      Новий шлях: {stack.get_goal_path()}")
    
    # Виконуємо 3.1
    print(f"\n   [{stack.current_goal_id}] Знайти пошукове поле...")
    result = stack.complete_current_subtask()
    print(f"   ✅ Завершено -> {result}")
    
    # 3.2 теж провалюється
    print(f"   [{stack.current_goal_id}] Ввести текст пошуку...")
    for i in range(3):
        action = stack.handle_failure(f"Введення не працює, спроба {i+1}")
        print(f"      ⚠️ Збій #{i+1} -> {action}")
    
    # Декомпозуємо 3.2
    print(f"\n   🔀 Декомпозиція завдання 3.2:")
    stack.decompose_current_goal([
        {"description": "3.2.1: Клікнути на поле вводу"},
        {"description": "3.2.2: Набрати текст 'Архангел'"},
        {"description": "3.2.3: Дочекатись підказок"},
    ], "Потрібна детальна робота з полем")
    
    print(f"      Шлях: {stack.get_goal_path()}")
    print(f"      Глибина: {stack.depth}/{GoalStack.MAX_DEPTH}")
    
    # Успішно виконуємо всі підзавдання 3.2.x
    print(f"\n   📍 Виконуємо підзавдання 3.2:")
    for i in range(3):
        goal = stack.current_goal
        print(f"      [{goal.id}] {goal.description[:30]}...")
        result = stack.complete_current_subtask()
        print(f"         ✅ -> {result}")
    
    # 3.3 виконується успішно
    print(f"\n   [{stack.current_goal_id}] Натиснути кнопку пошуку...")
    result = stack.complete_current_subtask()
    print(f"   ✅ Завершено -> {result}")
    
    print(f"\n{'='*60}")
    print(f"📊 Підсумок:")
    print(f"   Завершених цілей: {len(stack._history)}")
    print(f"   Стек порожній: {stack.is_empty}")
    print(f"   Результат: {'✅ Успіх!' if stack.is_empty else '❌ Не завершено'}")
    print(f"{'='*60}")
    
    return stack.is_empty


def test_browser_task():
    """Test with browser task that previously caused loops."""
    print("\n🧪 Тест: Браузерне завдання (реальний запуск)")
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
                
                # Show goal stack info if available
                goal_stack_data = state_update.get("goal_stack")
                goal_info = ""
                if goal_stack_data:
                    gs = GoalStack.from_dict(goal_stack_data)
                    goal_info = f" goal={gs.current_goal_id}"
                
                # Print progress
                print(f"  [{event_count:02d}] {node_name:15s} (step={step_count}, replan={replan_count}{goal_info})")
                
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
    print("🚀 Запуск тестів рекурсії з GoalStack\n")
    
    # First run the demo to show how GoalStack works
    demo_success = test_goal_stack_demo()
    
    # Ask if user wants to run real browser test
    print("\n" + "=" * 60)
    if demo_success:
        print("🎉 ДЕМО GoalStack УСПІШНЕ!")
    else:
        print("❌ ДЕМО GoalStack НЕ ПРОЙДЕНО!")
    
    # Uncomment to run real browser test:
    # success = test_browser_task()
    # if success:
    #     print("🎉 БРАУЗЕРНИЙ ТЕСТ ПРОЙДЕНО!")
    # else:
    #     print("❌ БРАУЗЕРНИЙ ТЕСТ НЕ ПРОЙДЕНО!")
    
    print("=" * 60)
    sys.exit(0 if demo_success else 1)
