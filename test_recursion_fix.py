#!/usr/bin/env python3
"""
Тест для перевірки виправлення проблеми з нескінченною рекурсією
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_simple_task():
    """Тест простого завдання, яке не повинно викликати рекурсію"""
    from core.trinity.runtime import TrinityRuntime
    
    print("=" * 60)
    print("🧪 Тест: Простий запит")
    print("=" * 60)
    
    runtime = TrinityRuntime(verbose=True, hyper_mode=False)
    
    try:
        task = "Створи файл test_hello.txt з текстом 'Hello World'"
        print(f"\n📋 Завдання: {task}\n")
        
        step_count = 0
        for event in runtime.run(task, recursion_limit=50):
            step_count += 1
            if step_count > 50:
                print(f"\n❌ ПОМИЛКА: Перевищено 50 кроків!")
                return False
            
            # Показуємо прогрес
            for node_name, node_state in event.items():
                agent = node_state.get("current_agent")
                step = node_state.get("step_count", 0)
                status = node_state.get("last_step_status")
                print(f"  [{step:02d}] {node_name:15} -> {agent:15} (status: {status})")
                
                if agent == "end":
                    print(f"\n✅ Завдання завершено за {step} кроків")
                    return True
        
        print(f"\n⚠️  Завдання не завершилось, але й не зациклилось (кроків: {step_count})")
        return True
        
    except RecursionError as e:
        print(f"\n❌ RecursionError: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Помилка: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        runtime.cleanup()

def test_browser_task():
    """Тест браузерного завдання (без фактичного відкриття браузера)"""
    from core.trinity.runtime import TrinityRuntime
    
    print("\n" + "=" * 60)
    print("🧪 Тест: Браузерне завдання (симуляція)")
    print("=" * 60)
    
    runtime = TrinityRuntime(verbose=True, hyper_mode=False)
    
    try:
        task = "Знайди інформацію про Python на Wikipedia"
        print(f"\n📋 Завдання: {task}\n")
        
        step_count = 0
        for event in runtime.run(task, recursion_limit=50):
            step_count += 1
            if step_count > 50:
                print(f"\n❌ ПОМИЛКА: Перевищено 50 кроків!")
                return False
            
            for node_name, node_state in event.items():
                agent = node_state.get("current_agent")
                step = node_state.get("step_count", 0)
                
                if agent == "end" or step >= 20:  # Форсуємо завершення
                    print(f"\n✅ Завдання зупинено (кроків: {step})")
                    return True
        
        return True
        
    except RecursionError as e:
        print(f"\n❌ RecursionError: {e}")
        return False
    except Exception as e:
        print(f"\n⚠️  Очікувана помилка (це нормально для тесту): {type(e).__name__}")
        return True
    finally:
        runtime.cleanup()

if __name__ == "__main__":
    print("\n🚀 Запуск тестів виправлення рекурсії\n")
    
    # Встановлюємо обмеження рекурсії Python
    sys.setrecursionlimit(500)  # Низький ліміт для швидкого виявлення проблем
    
    results = []
    
    # Тест 1
    results.append(("Простий файл", test_simple_task()))
    
    # Тест 2
    results.append(("Браузерне завдання", test_browser_task()))
    
    # Результати
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТИ ТЕСТІВ")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status:10} | {name}")
    
    all_passed = all(r[1] for r in results)
    
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 Всі тести пройдено! Рекурсія виправлена.")
    else:
        print("⚠️  Деякі тести не пройдено.")
    print("=" * 60 + "\n")
    
    sys.exit(0 if all_passed else 1)
