#!/usr/bin/env python3
"""
🤖 EMAIL SERVICES DEMO - Демонстрація роботи з двома email сервісами
Temp-mail.org (отримання) + Proton.me (реєстрація)
"""

import subprocess
import time
import random
from datetime import datetime

# Кольори для вивода
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def log(message: str, level: str = "INFO"):
    """Логування з кольорами"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    if level == "SUCCESS":
        print(f"{Colors.OKGREEN}[{timestamp}] ✅ {message}{Colors.ENDC}")
    elif level == "ERROR":
        print(f"{Colors.FAIL}[{timestamp}] ❌ {message}{Colors.ENDC}")
    elif level == "WARNING":
        print(f"{Colors.WARNING}[{timestamp}] ⚠️  {message}{Colors.ENDC}")
    elif level == "INFO":
        print(f"{Colors.OKBLUE}[{timestamp}] ℹ️  {message}{Colors.ENDC}")
    elif level == "STEP":
        print(f"{Colors.OKCYAN}[{timestamp}] 🔄 {message}{Colors.ENDC}")
    elif level == "INPUT":
        print(f"{Colors.BOLD}[{timestamp}] 📝 {message}{Colors.ENDC}")
    else:
        print(f"[{timestamp}] {message}")

# Реалістичні дані
FIRST_NAMES = ["Alex", "James", "Michael", "Emma", "Olivia", "William", "Benjamin"]
LAST_NAMES = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller"]

def generate_email_data():
    """Генерація даних для email сервісів"""
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    
    # Email для temp-mail (отримання листів)
    temp_email = f"{first_name.lower()}{last_name.lower()}@temp-mail.org"
    
    # Email для Proton (реєстрація)
    proton_email = f"{first_name.lower()}.{last_name.lower()}@proton.me"
    
    password = "Qwas@000"
    
    return temp_email, proton_email, first_name, last_name, password

def demo_safari_temp_mail(temp_email: str):
    """ДЕМО: Відкриття temp-mail у Safari"""
    log(f"ДЕМО: Відкриття temp-mail у Safari", "STEP")
    log(f"Email: {temp_email}", "INPUT")
    
    try:
        # Apple Script для Safari
        apple_script = f"""
        tell application "Safari"
            activate
            open location "https://temp-mail.org/?email={temp_email}"
        end tell
        
        delay 2
        
        display notification "Temp-mail відкрито у Safari" with title "Email Demo"
        """
        
        process = subprocess.run(
            ["osascript", "-e", apple_script],
            capture_output=True,
            text=True
        )
        
        if process.returncode == 0:
            log("Safari відкрито з temp-mail", "SUCCESS")
            log("Готово до отримання листів від Proton", "INFO")
            return True
        else:
            log(f"Помилка Safari: {process.stderr}", "ERROR")
            return False
            
    except Exception as e:
        log(f"Помилка при відкритті Safari: {str(e)}", "ERROR")
        return False

def demo_chrome_proton(proton_email: str, password: str):
    """ДЕМО: Відкриття Proton у Chrome"""
    log(f"ДЕМО: Відкриття Proton у Chrome", "STEP")
    log(f"Email: {proton_email}", "INPUT")
    log(f"Пароль: {password}", "INPUT")
    
    try:
        # Apple Script для Chrome
        apple_script = f"""
        tell application "Google Chrome"
            activate
            open location "https://proton.me/mail"
        end tell
        
        delay 3
        
        display notification "Proton Mail відкрито у Chrome" with title "Email Demo"
        """
        
        process = subprocess.run(
            ["osascript", "-e", apple_script],
            capture_output=True,
            text=True
        )
        
        if process.returncode == 0:
            log("Chrome відкрито з Proton Mail", "SUCCESS")
            log("Готово до реєстрації", "INFO")
            return True
        else:
            log(f"Помилка Chrome: {process.stderr}", "ERROR")
            return False
            
    except Exception as e:
        log(f"Помилка при відкритті Chrome: {str(e)}", "ERROR")
        return False

def demo_registration_flow(proton_email: str, password: str):
    """ДЕМО: Процес реєстрації на Proton"""
    log("ДЕМО: Процес реєстрації на Proton", "STEP")
    
    steps = [
        "🔍 Пошук кнопки 'Create a free account'",
        "📝 Заповнення email поля",
        "🔒 Заповнення пароля",
        "🔒 Підтвердження пароля",
        "🚀 Натиснення кнопки 'Почніть використовувати Proton Mail'",
        "🧩 Розв'язання капчі (ручно)",
        "💰 Вибір безплатного тарифу (0€)",
        "📧 Очікування листа від Proton"
    ]
    
    for i, step in enumerate(steps, 1):
        log(f"Крок {i}: {step}", "INFO")
        time.sleep(1)
    
    log("Реєстрація на Proton завершена", "SUCCESS")

def demo_email_verification(temp_email: str):
    """ДЕМО: Підтвердження email через temp-mail"""
    log("ДЕМО: Підтвердження email через temp-mail", "STEP")
    
    verification_steps = [
        "🔄 Перехід до Safari з temp-mail",
        "🔄 Оновлення сторінки temp-mail",
        "📧 Пошук листа від Proton",
        "📖 Відкриття листа від Proton",
        "🔗 Пошук посилання для підтвердження",
        "✅ Натиснення посилання підтвердження",
        "🎉 Email підтверджено!"
    ]
    
    for i, step in enumerate(verification_steps, 1):
        log(f"Верифікація {i}: {step}", "INFO")
        time.sleep(1)
    
    log("Email підтверджено успішно", "SUCCESS")

def demo_javascript_automation():
    """ДЕМО: JavaScript код для автоматизації"""
    log("ДЕМО: JavaScript код для автоматизації", "STEP")
    
    js_code = """
    // ЗАПОВНЕННЯ EMAIL ПОЛЯ
    var emailInput = document.querySelector('input[type="email"]');
    if (emailInput) {
        emailInput.value = 'alex.smith@proton.me';
        emailInput.dispatchEvent(new Event('input', { bubbles: true }));
        emailInput.dispatchEvent(new Event('change', { bubbles: true }));
    }
    
    // ЗАПОВНЕННЯ ПАРОЛЯ
    var passwordInputs = document.querySelectorAll('input[type="password"]');
    if (passwordInputs.length > 0) {
        passwordInputs[0].value = 'Qwas@000';
        passwordInputs[0].dispatchEvent(new Event('input', { bubbles: true }));
        passwordInputs[0].dispatchEvent(new Event('change', { bubbles: true }));
    }
    
    // НАТИСНЕННЯ КНОПКИ
    var buttons = document.querySelectorAll('button');
    for (var i = 0; i < buttons.length; i++) {
        var text = buttons[i].textContent.toLowerCase();
        if (text.includes('почніть') || text.includes('create')) {
            buttons[i].click();
            break;
        }
    }
    """
    
    log("JavaScript код готовий для виконання", "SUCCESS")
    print(f"\n{Colors.OKCYAN}JavaScript код:{Colors.ENDC}")
    print(js_code)

def main():
    """Головна демонстрація"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  🤖 EMAIL SERVICES DEMO - Два email сервіси               ║")
    print("║  Safari → Temp-mail | Chrome → Proton                     ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}\n")
    
    # КРОК 1: Генерація даних
    log("═══════════════════════════════════════════════════════════", "STEP")
    log("КРОК 1: ГЕНЕРАЦІЯ ДАНИХ ДЛЯ ДВОХ EMAIL СЕРВІСІВ", "STEP")
    log("═══════════════════════════════════════════════════════════", "STEP")
    
    temp_email, proton_email, first_name, last_name, password = generate_email_data()
    
    log(f"Ім'я: {first_name}", "INPUT")
    log(f"Прізвище: {last_name}", "INPUT")
    log(f"📧 Temp-mail (отримання): {temp_email}", "INPUT")
    log(f"📧 Proton (реєстрація): {proton_email}", "INPUT")
    log(f"🔒 Пароль: {password}", "INPUT")
    
    time.sleep(2)
    
    # КРОК 2: Safari + Temp-mail
    log("\n═══════════════════════════════════════════════════════════", "STEP")
    log("КРОК 2: SAFARI → TEMP-MAIL.ORG", "STEP")
    log("═══════════════════════════════════════════════════════════", "STEP")
    
    log("Чому Safari для temp-mail?", "INFO")
    log("✅ НЕ блокується на temp-mail.org", "SUCCESS")
    log("✅ Нативна підтримка macOS", "SUCCESS")
    log("✅ Швидкий доступ до листів", "SUCCESS")
    log("❌ Chrome БЛОКУЄТЬСЯ на temp-mail!", "ERROR")
    
    demo_safari_temp_mail(temp_email)
    time.sleep(2)
    
    # КРОК 3: Chrome + Proton
    log("\n═══════════════════════════════════════════════════════════", "STEP")
    log("КРОК 3: CHROME → PROTON.ME", "STEP")
    log("═══════════════════════════════════════════════════════════", "STEP")
    
    log("Чому Chrome для Proton?", "INFO")
    log("✅ НЕ блокується на proton.me", "SUCCESS")
    log("✅ Підтримує JavaScript автоматизацію", "SUCCESS")
    log("✅ Стабільна робота з формами", "SUCCESS")
    log("❌ Safari має обмеження з JavaScript", "WARNING")
    
    demo_chrome_proton(proton_email, password)
    time.sleep(2)
    
    # КРОК 4: Процес реєстрації
    log("\n═══════════════════════════════════════════════════════════", "STEP")
    log("КРОК 4: ПРОЦЕС РЕЄСТРАЦІЇ НА PROTON", "STEP")
    log("═══════════════════════════════════════════════════════════", "STEP")
    
    demo_registration_flow(proton_email, password)
    time.sleep(2)
    
    # КРОК 5: JavaScript автоматизація
    log("\n═══════════════════════════════════════════════════════════", "STEP")
    log("КРОК 5: JAVASCRIPT АВТОМАТИЗАЦІЯ", "STEP")
    log("═══════════════════════════════════════════════════════════", "STEP")
    
    log("Ключовий момент: dispatchEvent для валідації!", "WARNING")
    demo_javascript_automation()
    time.sleep(2)
    
    # КРОК 6: Підтвердження email
    log("\n═══════════════════════════════════════════════════════════", "STEP")
    log("КРОК 6: ПІДТВЕРДЖЕННЯ EMAIL ЧЕРЕЗ TEMP-MAIL", "STEP")
    log("═══════════════════════════════════════════════════════════", "STEP")
    
    log("Повернення до Safari для отримання листа", "INFO")
    demo_email_verification(temp_email)
    time.sleep(2)
    
    # ФІНАЛЬНИЙ РЕЗУЛЬТАТ
    log("\n═══════════════════════════════════════════════════════════", "STEP")
    log("РЕЗУЛЬТАТ: ДВА EMAIL СЕРВІСИ ПРАЦЮЮТЬ РАЗОМ", "STEP")
    log("═══════════════════════════════════════════════════════════", "STEP")
    
    print(f"\n{Colors.BOLD}📊 АРХІТЕКТУРА ДВОХ EMAIL СЕРВІСІВ:{Colors.ENDC}")
    print(f"{Colors.OKGREEN}┌─────────────────┐    ┌─────────────────┐{Colors.ENDC}")
    print(f"{Colors.OKGREEN}│     SAFARI      │    │     CHROME      │{Colors.ENDC}")
    print(f"{Colors.OKGREEN}│                 │    │                 │{Colors.ENDC}")
    print(f"{Colors.OKGREEN}│  temp-mail.org  │◄──►│   proton.me     │{Colors.ENDC}")
    print(f"{Colors.OKGREEN}│                 │    │                 │{Colors.ENDC}")
    print(f"{Colors.OKGREEN}│ (отримання)     │    │ (реєстрація)    │{Colors.ENDC}")
    print(f"{Colors.OKGREEN}└─────────────────┘    └─────────────────┘{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}🔄 ЦИКЛ ВЗАЄМОДІЇ:{Colors.ENDC}")
    print(f"{Colors.OKCYAN}1. Chrome реєструє {proton_email} на Proton{Colors.ENDC}")
    print(f"{Colors.OKCYAN}2. Proton надсилає лист на {temp_email}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}3. Safari отримує лист на temp-mail{Colors.ENDC}")
    print(f"{Colors.OKCYAN}4. Safari підтверджує реєстрацію{Colors.ENDC}")
    print(f"{Colors.OKCYAN}5. Proton акаунт активовано!{Colors.ENDC}")
    
    print(f"\n{Colors.BOLD}✅ ПЕРЕВАГИ ЦІЄЇ АРХІТЕКТУРИ:{Colors.ENDC}")
    print(f"{Colors.OKGREEN}• Немає блокування браузерів{Colors.ENDC}")
    print(f"{Colors.OKGREEN}• Розділення відповідальності{Colors.ENDC}")
    print(f"{Colors.OKGREEN}• Висока надійність{Colors.ENDC}")
    print(f"{Colors.OKGREEN}• Нативна підтримка macOS{Colors.ENDC}")
    
    log("\n🎉 ДЕМОНСТРАЦІЯ ЗАВЕРШЕНА!", "SUCCESS")
    log("Два email сервіси працюють в ідеальній синхронізації", "SUCCESS")

if __name__ == "__main__":
    main()
