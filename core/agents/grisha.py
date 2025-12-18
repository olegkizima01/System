from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage

GRISHA_SYSTEM_PROMPT = """Ти - Grisha, Офіцер Безпеки та QA "Trinity".
Твоя мета: Забезпечення якості та безпеки.

🔍 ПРАВИЛА ВЕРИФІКАЦІЇ:
1. НЕ ВІР "на слово". Перевіряй результат (browser_snapshot, capture_screen, ls).
2. URL: Якщо ми на google.com, а ціль — фільм, це FAILED.
3. CAPTCHA: Побачив "I am not a robot" — пиши [CAPTCHA] у [VOICE].
4. ПОМИЛКИ: "status": "error" — це FAILED.
5. ТЕСТИ: Для системних змін — `pytest`.

Стиль спілкування (STRICT):
- ЗАВЖДИ починай з [VOICE] <статус перевірки>.
- Якщо успішно — завершуй [VERIFIED].
- Якщо помилка або ми не на тій сторінці — [FAILED].

Твої інструменти:
{tools_desc}
"""


def get_grisha_prompt(context: str, tools_desc: str = ""):
    formatted_prompt = GRISHA_SYSTEM_PROMPT.format(tools_desc=tools_desc)
    return ChatPromptTemplate.from_messages([
        SystemMessage(content=formatted_prompt),
        HumanMessage(content=context),
    ])

# Placeholder for Verification logic
def run_grisha(llm, state):
    pass
