#!/usr/bin/env python3
"""
Test for recursive goal decomposition (GoalStack).

Tests the proper recursion pattern:
1. If task 3 fails, main goal becomes task 3
2. Task 3 splits into 3.1, 3.2, 3.3
3. If 3.2 fails, goal becomes 3.2
4. 3.2 splits into 3.2.1, 3.2.2, 3.2.3
5. On completion, return to parent goal (3.2 -> 3 -> main)

This ensures replanning happens at the failure point with proper
stack-based recursion (no memory overhead).
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.trinity.goal_stack import GoalStack, Goal, generate_subtask_decomposition


def test_basic_goal_stack():
    """Test basic GoalStack operations."""
    print("=" * 60)
    print("🧪 Тест 1: Базові операції GoalStack")
    print("=" * 60)
    
    # Create stack with main goal
    stack = GoalStack("Відкрити YouTube та знайти відео")
    
    assert stack.depth == 1, f"Expected depth 1, got {stack.depth}"
    assert stack.current_goal_id == "main", f"Expected 'main', got {stack.current_goal_id}"
    assert not stack.is_empty
    
    print(f"✅ Створено стек: {stack}")
    print(f"   {stack.get_status_summary()}")
    
    # Complete main goal
    result = stack.complete_current_subtask()
    assert result == "all_complete", f"Expected 'all_complete', got {result}"
    assert stack.is_empty
    
    print("✅ Головна ціль виконана")
    print()
    return True


def test_single_failure_decomposition():
    """Test decomposition when a task fails."""
    print("=" * 60)
    print("🧪 Тест 2: Декомпозиція при збої")
    print("=" * 60)
    
    stack = GoalStack("Виконати складне завдання")
    
    # Simulate failure
    action = stack.handle_failure("Завдання не вдалося виконати")
    assert action == "retry", f"First failure should be retry, got {action}"
    print(f"✅ Перший збій -> {action}")
    
    action = stack.handle_failure("Знову не вдалося")
    assert action == "retry", f"Second failure should be retry, got {action}"
    print(f"✅ Другий збій -> {action}")
    
    action = stack.handle_failure("Третій раз не вдалося")
    assert action == "decompose", f"Third failure should be decompose, got {action}"
    print(f"✅ Третій збій -> {action}")
    
    # Now decompose
    subtasks = [
        {"description": "Крок 1: Підготовка"},
        {"description": "Крок 2: Виконання"},
        {"description": "Крок 3: Перевірка"},
    ]
    
    success = stack.decompose_current_goal(subtasks, "Завдання занадто складне")
    assert success, "Decomposition should succeed"
    
    print(f"✅ Декомпозиція успішна")
    print(f"   {stack.get_status_summary()}")
    
    assert stack.depth == 2
    assert stack.current_goal_id == "1"
    
    print()
    return True


def test_recursive_decomposition():
    """Test recursive decomposition (3 -> 3.2 -> 3.2.1)."""
    print("=" * 60)
    print("🧪 Тест 3: Рекурсивна декомпозиція (головний тест)")
    print("=" * 60)
    
    stack = GoalStack("Головна ціль: відкрити YouTube та знайти відео")
    print(f"📍 Старт: {stack.get_goal_path()}")
    
    # Simulate main goal failing
    for i in range(GoalStack.MAX_RETRIES):
        stack.handle_failure(f"Спроба {i+1}")
    
    # Decompose main -> 1, 2, 3
    stack.decompose_current_goal([
        {"description": "Завдання 1: Відкрити браузер"},
        {"description": "Завдання 2: Перейти на YouTube"},
        {"description": "Завдання 3: Знайти відео"},
    ])
    
    print(f"📍 Після декомпозиції main: {stack.get_goal_path()}")
    assert stack.current_goal_id == "1"
    
    # Complete task 1
    result = stack.complete_current_subtask()
    print(f"   ✅ Завдання 1 виконано, результат: {result}")
    assert result == "next_subtask"
    assert stack.current_goal_id == "2"
    
    # Complete task 2
    result = stack.complete_current_subtask()
    print(f"   ✅ Завдання 2 виконано, результат: {result}")
    assert result == "next_subtask"
    assert stack.current_goal_id == "3"
    
    # Task 3 fails and needs decomposition
    for i in range(GoalStack.MAX_RETRIES):
        stack.handle_failure(f"Завдання 3 провалено, спроба {i+1}")
    
    # Decompose 3 -> 3.1, 3.2, 3.3
    stack.decompose_current_goal([
        {"description": "Завдання 3.1: Знайти пошукове поле"},
        {"description": "Завдання 3.2: Ввести текст"},
        {"description": "Завдання 3.3: Натиснути Enter"},
    ])
    
    print(f"📍 Після декомпозиції 3: {stack.get_goal_path()}")
    assert stack.current_goal_id == "3.1"
    
    # Complete 3.1
    result = stack.complete_current_subtask()
    print(f"   ✅ Завдання 3.1 виконано, результат: {result}")
    assert result == "next_subtask"
    assert stack.current_goal_id == "3.2"
    
    # Task 3.2 fails and needs decomposition
    for i in range(GoalStack.MAX_RETRIES):
        stack.handle_failure(f"Завдання 3.2 провалено, спроба {i+1}")
    
    # Decompose 3.2 -> 3.2.1, 3.2.2, 3.2.3
    stack.decompose_current_goal([
        {"description": "Завдання 3.2.1: Клікнути на поле"},
        {"description": "Завдання 3.2.2: Набрати текст"},
        {"description": "Завдання 3.2.3: Підтвердити"},
    ])
    
    print(f"📍 Після декомпозиції 3.2: {stack.get_goal_path()}")
    assert stack.current_goal_id == "3.2.1"
    assert stack.depth == 4  # main -> 3 -> 3.2 -> 3.2.1
    
    print(f"\n🔍 Стек цілей:")
    for i, goal in enumerate(stack._stack):
        indent = "  " * i
        print(f"   {indent}[{goal.id}] {goal.description[:40]}...")
    
    # Complete 3.2.1, 3.2.2, 3.2.3
    result = stack.complete_current_subtask()
    print(f"\n   ✅ Завдання 3.2.1 виконано, результат: {result}")
    assert result == "next_subtask"
    assert stack.current_goal_id == "3.2.2"
    
    result = stack.complete_current_subtask()
    print(f"   ✅ Завдання 3.2.2 виконано, результат: {result}")
    assert result == "next_subtask"
    assert stack.current_goal_id == "3.2.3"
    
    result = stack.complete_current_subtask()
    print(f"   ✅ Завдання 3.2.3 виконано, результат: {result}")
    # 3.2 should now complete, then move to 3.3
    assert result == "next_subtask"
    assert stack.current_goal_id == "3.3", f"Expected 3.3, got {stack.current_goal_id}"
    
    print(f"📍 Після завершення 3.2: {stack.get_goal_path()}")
    
    # Complete 3.3
    result = stack.complete_current_subtask()
    print(f"   ✅ Завдання 3.3 виконано, результат: {result}")
    # 3 should now complete, and since main has no more subtasks, all complete
    assert result == "all_complete", f"Expected all_complete, got {result}"
    assert stack.is_empty
    
    print(f"\n✅ Всі цілі виконані!")
    print(f"   Історія: {len(stack._history)} завершених цілей")
    
    print()
    return True


def test_max_depth_limit():
    """Test that max depth limit is enforced."""
    print("=" * 60)
    print("🧪 Тест 4: Ліміт глибини рекурсії")
    print("=" * 60)
    
    stack = GoalStack("Глибоко вкладене завдання")
    
    # Keep decomposing until we hit the limit
    depth_reached = 1
    for level in range(GoalStack.MAX_DEPTH + 2):
        # Fail enough times to trigger decomposition
        for i in range(GoalStack.MAX_RETRIES):
            action = stack.handle_failure(f"Рівень {level}, спроба {i+1}")
            if action == "abort":
                break
        
        if action == "abort":
            print(f"   ⛔ Досягнуто ліміт на глибині {stack.depth}")
            break
        
        # Decompose
        success = stack.decompose_current_goal([
            {"description": f"Підзавдання рівня {level + 1}"}
        ])
        
        if not success:
            print(f"   ⛔ Декомпозиція заблокована на глибині {stack.depth}")
            break
        
        depth_reached = stack.depth
        print(f"   📍 Рівень {depth_reached}: {stack.get_goal_path()}")
    
    assert depth_reached <= GoalStack.MAX_DEPTH, \
        f"Depth {depth_reached} exceeded MAX_DEPTH {GoalStack.MAX_DEPTH}"
    
    print(f"\n✅ Ліміт глибини працює коректно (max={GoalStack.MAX_DEPTH})")
    print()
    return True


def test_serialization():
    """Test serialization and deserialization."""
    print("=" * 60)
    print("🧪 Тест 5: Серіалізація стану")
    print("=" * 60)
    
    # Create a stack with some state
    stack = GoalStack("Тестове завдання")
    
    for i in range(GoalStack.MAX_RETRIES):
        stack.handle_failure("Тестовий збій")
    
    stack.decompose_current_goal([
        {"description": "Підзавдання 1"},
        {"description": "Підзавдання 2"},
    ])
    
    # Serialize
    data = stack.to_dict()
    print(f"   📦 Серіалізовано: {len(str(data))} bytes")
    
    # Deserialize
    restored = GoalStack.from_dict(data)
    
    assert restored.depth == stack.depth
    assert restored.current_goal_id == stack.current_goal_id
    assert restored.current_goal.description == stack.current_goal.description
    
    print(f"   ✅ Відновлено: {restored}")
    print(f"   📍 Шлях: {restored.get_goal_path()}")
    
    print()
    return True


def run_all_tests():
    """Run all GoalStack tests."""
    print("\n" + "=" * 60)
    print("🚀 Запуск тестів рекурсивної декомпозиції GoalStack")
    print("=" * 60 + "\n")
    
    tests = [
        ("Базові операції", test_basic_goal_stack),
        ("Декомпозиція при збої", test_single_failure_decomposition),
        ("Рекурсивна декомпозиція", test_recursive_decomposition),
        ("Ліміт глибини", test_max_depth_limit),
        ("Серіалізація", test_serialization),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"❌ Тест '{name}' повернув False")
        except Exception as e:
            failed += 1
            print(f"❌ Тест '{name}' викинув виняток: {e}")
            import traceback
            traceback.print_exc()
    
    print("=" * 60)
    print(f"📊 Результати: {passed}/{len(tests)} тестів пройдено")
    
    if failed == 0:
        print("🎉 ВСІ ТЕСТИ ПРОЙДЕНО!")
    else:
        print(f"❌ {failed} тестів провалено")
    
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
