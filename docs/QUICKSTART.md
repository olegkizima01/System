# Trinity Improvements - Quick Start Guide

## 🚀 Швидкий старт

### 1️⃣ Валідація Pydantic моделей

```python
from core.trinity_models import TrinityStateModel, MetaConfig

# Створити стан з автоматичною валідацією
state = TrinityStateModel(
    current_agent="meta_planner",
    task_type="DEV",
    is_dev=True,
    step_count=0,
)

# Valдувати стан перед запуском
state.validate_state()  # ✅ Валідний

# Конвертити у dict для LangGraph
state_dict = state.to_dict()
```

### 2️⃣ State Logging для діагностики

```python
from core.state_logger import log_initial_state, log_state_transition

# На початку виконання завдання
log_initial_state(
    task="Write a Python function",
    state=initial_state
)

# При переходах між агентами
log_state_transition(
    from_agent="atlas",
    to_agent="tetyana",
    step_count=5,
    last_status="success",
    reason="Plan execution complete"
)

# Перевірити логи
# ~/.system_cli/logs/trinity_state_20251220.log
```

### 3️⃣ Type Checking з MyPy

```bash
# Перевірити типи в файлі
mypy core/trinity.py --config-file=setup.cfg

# Перевірити увесь проект
mypy . --config-file=setup.cfg

# З детальним виводом
mypy core/ --config-file=setup.cfg --show-error-context
```

### 4️⃣ Unit Тести

```bash
# Запустити всі тести
pytest tests/test_trinity_models.py -v

# Запустити конкретний тест
pytest tests/test_trinity_models.py::TestMetaConfigModel -v

# З покриттям кода
pytest tests/test_trinity_models.py --cov=core.trinity_models --cov-report=html
```

---

## 📊 Приклади використання

### Приклад 1: Створення та валідація стану

```python
from core.trinity_models import TrinityStateModel, MetaConfig

# Валідний стан
try:
    state = TrinityStateModel(
        task_type="DEV",
        meta_config=MetaConfig(
            strategy="linear",
            verification_rigor="high"
        )
    )
    print("✅ State is valid")
except ValueError as e:
    print(f"❌ Invalid state: {e}")
```

### Приклад 2: Трансформація dict <-> model

```python
# Конвертувати з dict
state_dict = {
    "current_agent": "atlas",
    "task_type": "DEV",
    "step_count": 5,
}

state_model = TrinityStateModel.from_dict(state_dict)

# Конвертувати назад в dict
result_dict = state_model.to_dict()
```

### Приклад 3: Логування з контекстом

```python
from core.state_logger import StateInitLogger

logger = StateInitLogger()

# Логувати ініціалізацію
logger.log_initial_state("Write a function", initial_state)

# Логувати помилку зі снімком стану
try:
    # ... код ...
    pass
except Exception as e:
    logger.log_error(
        context="plan execution",
        error=e,
        state_snapshot=state_dict
    )
```

### Приклад 4: Перевірка типів

```python
# trinity.py з типами
from typing import Dict, Any
from core.trinity_models import TrinityStateModel

def run_task(input_text: str) -> TrinityStateModel:
    """Run a Trinity task."""
    state = TrinityStateModel()
    state.validate_state()
    return state

# MyPy перевірить типи автоматично!
```

---

## 📈 Переваги

| Функція | Користь |
|---------|---------|
| **Pydantic Models** | 🔒 Гарантовані типи і значення за замовчуванням |
| **State Logger** | 🔍 Легко діагностувати проблеми з ініціалізацією |
| **MyPy Checking** | ⚡ Перехоплювати помилки до runtime |
| **Unit Tests** | ✅ Упевненість в коректності коду |

---

## 🔧 Налаштування

### Оновити requirements.txt

Переконайтеся що у вас встановлено:
```
pydantic>=2.0.0
mypy>=1.0.0
pytest>=8.0.0
```

### Активувати pre-commit hooks (майбутнє)

```bash
# Установити pre-commit
pip install pre-commit

# Додати в .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.5.1
    hooks:
      - id: mypy
```

---

## ❓ FAQ

**Q: Чи буде сповільнення від валідації?**
A: Ні! Валідація виконується тільки при ініціалізації, не при кожній операції.

**Q: Як інтегрувати в існуючий код?**
A: Поступово! Почніть з нових кодів, старий залишиться сумісним.

**Q: Де знайти логи?**
A: `~/.system_cli/logs/trinity_state_YYYYMMDD.log`

**Q: Як запустити тести?**
A: `pytest tests/test_trinity_models.py -v`

---

## 📚 Документація

- **Моделі:** `core/trinity_models.py`
- **Логування:** `core/state_logger.py`
- **Тести:** `tests/test_trinity_models.py`
- **MyPy Config:** `setup.cfg`
- **Повна документація:** `TRINITY_IMPROVEMENTS_IMPLEMENTATION.md`

---

**Версія:** 1.0  
**Дата:** 20 грудня 2025  
**Статус:** ✅ Готово до використання
