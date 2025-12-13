#!/usr/bin/env python3
"""
🤖 WINDSURF EMAIL FINAL - Правильна розділення браузерів
Chrome → Proton (реєстрація)
Safari → Temp-mail (отримання листів) - ТІЛЬКИ Safari!
"""

import time
import random
import string
import subprocess
import os
from datetime import datetime
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

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

# Реалістичні імена та прізвища
FIRST_NAMES = [
    "Alex", "James", "Michael", "David", "Robert", "John", "Emma", "Olivia", 
    "Sophia", "Isabella", "Ava", "Mia", "Charlotte", "Amelia", "Harper",
    "William", "Benjamin", "Lucas", "Henry", "Alexander", "Mason", "Ethan"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark"
]

def generate_realistic_email() -> tuple:
    """Генерація реалістичного email на основі імені та прізвища"""
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    
    # Email для temp-mail (отримання листів)
    temp_email_formats = [
        f"{first_name.lower()}.{last_name.lower()}",
        f"{first_name.lower()}{last_name.lower()}",
        f"{first_name[0].lower()}{last_name.lower()}",
    ]
    temp_email_base = random.choice(temp_email_formats)
    temp_email = f"{temp_email_base}@temp-mail.org"
    
    # Email для Proton (реєстрація) - унікальний на основі імені та прізвища
    proton_email_formats = [
        f"{first_name.lower()}.{last_name.lower()}",
        f"{first_name.lower()}{last_name.lower()}",
        f"{first_name[0].lower()}.{last_name.lower()}",
    ]
    proton_email_base = random.choice(proton_email_formats)
    proton_email = f"{proton_email_base}@proton.me"
    
    return temp_email, proton_email, first_name, last_name

def setup_chrome_driver():
    """Налаштування Chrome драйвера"""
    log("Налаштування Chrome браузера", "STEP")
    
    try:
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--start-maximized")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        log("Chrome браузер налаштований", "SUCCESS")
        return driver
    except Exception as e:
        log(f"Помилка при налаштуванні браузера: {str(e)}", "ERROR")
        return None

def open_safari_temp_mail(temp_email: str):
    """Відкрити temp-mail у Safari через Apple Script"""
    log(f"Відкриття temp-mail у Safari: {temp_email}", "STEP")
    
    try:
        # Apple Script для відкриття Safari з temp-mail
        apple_script = f"""
        tell application "Safari"
            activate
            open location "https://temp-mail.org/?email={temp_email}"
        end tell
        """
        
        process = subprocess.Popen(
            ["osascript", "-e", apple_script],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        stdout, stderr = process.communicate()
        
        if process.returncode == 0:
            log("Safari відкрито з temp-mail", "SUCCESS")
            time.sleep(3)
            return True
        else:
            log(f"Помилка при відкритті Safari: {stderr.decode()}", "ERROR")
            return False
    except Exception as e:
        log(f"Помилка при виконанні Apple Script: {str(e)}", "ERROR")
        return False

def navigate_to_proton(driver):
    """Перейти на Proton Mail (ТІЛЬКИ Chrome)"""
    log("Перехід на Proton Mail (Chrome)", "STEP")
    
    try:
        driver.get("https://proton.me/mail")
        time.sleep(5)
        log("Proton Mail завантажено", "SUCCESS")
        return True
    except Exception as e:
        log(f"Помилка при завантаженні Proton: {str(e)}", "ERROR")
        return False

def find_and_click_signup(driver):
    """Знайти та натиснути кнопку реєстрації"""
    log("Пошук кнопки 'Create a free account'", "STEP")
    
    try:
        wait = WebDriverWait(driver, 15)
        
        selectors = [
            (By.XPATH, "//button[contains(text(), 'Create a free account')]"),
            (By.XPATH, "//a[contains(text(), 'Create a free account')]"),
            (By.XPATH, "//button[contains(text(), 'Create a free')]"),
            (By.XPATH, "//a[contains(text(), 'Create a free')]"),
            (By.LINK_TEXT, "Create a free account"),
        ]
        
        for by, selector in selectors:
            try:
                element = wait.until(EC.element_to_be_clickable((by, selector)))
                log(f"Кнопка знайдена", "INFO")
                element.click()
                time.sleep(3)
                log("Натиснуто кнопку 'Create a free account'", "SUCCESS")
                return True
            except:
                continue
        
        log("Кнопка реєстрації не знайдена - спробую прямий URL", "WARNING")
        driver.get("https://proton.me/mail/signup")
        time.sleep(3)
        log("Перейшов на сторінку реєстрації", "SUCCESS")
        return True
    except Exception as e:
        log(f"Помилка при пошуку кнопки: {str(e)}", "ERROR")
        return False

def fill_signup_form(driver, proton_email: str, password: str):
    """Заповнити форму реєстрації"""
    log("Заповнення форми реєстрації", "STEP")
    
    try:
        time.sleep(2)
        
        # Заповнити Email для Proton
        log(f"Пошук поля Email", "INFO")
        email_selectors = [
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.CSS_SELECTOR, "input[placeholder*='email']"),
            (By.CSS_SELECTOR, "input[placeholder*='Email']"),
            (By.CSS_SELECTOR, "input[name='email']"),
        ]
        
        for by, selector in email_selectors:
            try:
                email_input = driver.find_element(by, selector)
                email_input.clear()
                email_input.send_keys(proton_email)
                log(f"Email заповнено: {proton_email}", "SUCCESS")
                break
            except:
                continue
        
        time.sleep(1)
        
        # Заповнити пароль
        log("Пошук поля пароля", "INFO")
        password_inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='password']")
        if password_inputs:
            password_inputs[0].clear()
            password_inputs[0].send_keys(password)
            log("Пароль заповнено", "SUCCESS")
            
            if len(password_inputs) > 1:
                password_inputs[1].clear()
                password_inputs[1].send_keys(password)
                log("Підтвердження пароля заповнено", "SUCCESS")
        
        time.sleep(1)
        
        # Натиснути фіолетову кнопку внизу
        log("Пошук фіолетової кнопки внизу форми", "INFO")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        
        # Спробуємо знайти кнопку за текстом (українська мова)
        for button in buttons:
            text = button.text.strip().lower()
            
            if any(keyword in text for keyword in [
                "почніть використовувати", "почніть", "використовувати",
                "create free account", "create account", "розпочнімо", "розпочнимо",
                "next", "continue", "sign up", "signup", "далі", "продовжити",
                "почати", "почнемо", "почнімо"
            ]):
                log(f"Кнопка знайдена: '{text}'", "INFO")
                driver.execute_script("arguments[0].scrollIntoView(true);", button)
                time.sleep(1)
                button.click()
                log(f"Натиснуто кнопку", "SUCCESS")
                time.sleep(3)
                return True
        
        # Спробуємо за класом - шукаємо останню фіолетову кнопку
        log("Спробую знайти фіолетову кнопку за класом", "INFO")
        purple_buttons = []
        for button in buttons:
            class_attr = button.get_attribute("class").lower()
            if "primary" in class_attr or "purple" in class_attr or "button-primary" in class_attr:
                text = button.text.strip()
                if text:
                    purple_buttons.append(button)
        
        # Натиснути останню фіолетову кнопку (вона внизу)
        if purple_buttons:
            last_button = purple_buttons[-1]
            text = last_button.text.strip()
            log(f"Фіолетова кнопка знайдена: '{text}'", "INFO")
            driver.execute_script("arguments[0].scrollIntoView(true);", last_button)
            time.sleep(1)
            last_button.click()
            log(f"Натиснуто фіолетову кнопку", "SUCCESS")
            time.sleep(3)
            return True
        
        log("Кнопка для продовження не знайдена", "WARNING")
        return False
    except Exception as e:
        log(f"Помилка при заповненні форми: {str(e)}", "ERROR")
        return False

def select_free_plan(driver):
    """Вибрати безплатний тариф (0 євро)"""
    log("Перевірка наявності вибору тарифів", "STEP")
    
    try:
        time.sleep(2)
        
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for button in buttons:
            text = button.text.lower()
            if "free" in text and "0" in text:
                log(f"Безплатний тариф знайдено", "INFO")
                button.click()
                log("Натиснуто кнопку безплатного тарифу", "SUCCESS")
                time.sleep(3)
                return True
        
        log("Вибір тарифів не знайдено", "INFO")
        return True
    except Exception as e:
        log(f"Помилка при виборі тарифу: {str(e)}", "WARNING")
        return True

def handle_captcha_manual(driver):
    """Обробити капчу вручну"""
    log("Перевірка наявності капчи", "STEP")
    
    try:
        time.sleep(2)
        
        captcha_elements = driver.find_elements(By.CSS_SELECTOR, "div[class*='captcha'], iframe[title*='captcha']")
        if captcha_elements:
            log("Капча знайдена - потребує ручного розв'язання", "WARNING")
            log("⏳ Чекаю 120 секунд на розв'язання капчи...", "INFO")
            log("Виберіть квадрати як показано на зображенні", "INFO")
            time.sleep(120)
            log("Час для капчи закінчився", "INFO")
            return True
        
        log("Капча не знайдена", "INFO")
        return True
    except Exception as e:
        log(f"Помилка при обробці капчи: {str(e)}", "WARNING")
        return True

def main():
    """Основна функція"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  🤖 WINDSURF EMAIL FINAL - Правильна розділення           ║")
    print("║  Chrome → Proton | Safari → Temp-mail (ТІЛЬКИ!)           ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}\n")
    
    # Генерація даних
    log("═══════════════════════════════════════════════════════════", "STEP")
    log("КРОК 1: ГЕНЕРАЦІЯ РЕАЛІСТИЧНИХ ДАНИХ", "STEP")
    log("═══════════════════════════════════════════════════════════", "STEP")
    
    temp_email, proton_email, first_name, last_name = generate_realistic_email()
    password = "Qwas@000"
    
    log(f"Ім'я: {first_name}", "INPUT")
    log(f"Прізвище: {last_name}", "INPUT")
    log(f"Email Proton: {proton_email}", "INPUT")
    log(f"Email Temp-mail: {temp_email}", "INPUT")
    log(f"Пароль: {password}", "INPUT")
    
    time.sleep(2)
    
    # Крок 2: Відкрити temp-mail у Safari (ПЕРЕД Chrome!)
    log("\n═══════════════════════════════════════════════════════════", "STEP")
    log("КРОК 2: ВІДКРИТТЯ TEMP-MAIL У SAFARI", "STEP")
    log("═══════════════════════════════════════════════════════════", "STEP")
    
    if not open_safari_temp_mail(temp_email):
        log("Не вдалося відкрити Safari", "ERROR")
        return
    
    time.sleep(2)
    
    # Крок 3: Запуск Chrome браузера
    log("\n═══════════════════════════════════════════════════════════", "STEP")
    log("КРОК 3: ЗАПУСК CHROME БРАУЗЕРА", "STEP")
    log("═══════════════════════════════════════════════════════════", "STEP")
    
    driver = setup_chrome_driver()
    if not driver:
        log("Браузер не запущено", "ERROR")
        return
    
    try:
        # Крок 4: Перейти на Proton
        log("\n═══════════════════════════════════════════════════════════", "STEP")
        log("КРОК 4: РЕЄСТРАЦІЯ НА PROTON.ME (CHROME)", "STEP")
        log("═══════════════════════════════════════════════════════════", "STEP")
        
        if not navigate_to_proton(driver):
            log("Не вдалося завантажити Proton", "ERROR")
            return
        
        time.sleep(2)
        
        # Натиснути Create account
        if not find_and_click_signup(driver):
            log("Не вдалося натиснути Create account", "ERROR")
            return
        
        time.sleep(2)
        
        # Заповнити форму з Proton email
        if not fill_signup_form(driver, proton_email, password):
            log("Не вдалося заповнити форму", "ERROR")
            return
        
        time.sleep(3)
        
        # Обробити капчу
        log("\n═══════════════════════════════════════════════════════════", "STEP")
        log("КРОК 5: ОБРОБКА КАПЧИ", "STEP")
        log("═══════════════════════════════════════════════════════════", "STEP")
        
        handle_captcha_manual(driver)
        
        time.sleep(2)
        
        # Вибір тарифу
        log("\n═══════════════════════════════════════════════════════════", "STEP")
        log("КРОК 5.5: ВИБІР БЕЗПЛАТНОГО ТАРИФУ", "STEP")
        log("═══════════════════════════════════════════════════════════", "STEP")
        
        select_free_plan(driver)
        
        time.sleep(2)
        
        # Крок 6: Перевірити Safari
        log("\n═══════════════════════════════════════════════════════════", "STEP")
        log("КРОК 6: ПЕРЕВІРКА ЛИСТІВ У SAFARI", "STEP")
        log("═══════════════════════════════════════════════════════════", "STEP")
        
        log("⏳ Чекаю листа від Proton на temp-mail...", "INFO")
        log("Перевіряйте Safari для отримання листа", "INFO")
        time.sleep(30)
        
        # Фінальна інформація
        log("\n═══════════════════════════════════════════════════════════", "STEP")
        log("РЕЗУЛЬТАТИ ТЕСТУВАННЯ:", "STEP")
        log("═══════════════════════════════════════════════════════════", "STEP")
        
        log(f"Ім'я: {first_name}", "INFO")
        log(f"Прізвище: {last_name}", "INFO")
        log(f"Email Proton: {proton_email}", "INFO")
        log(f"Email Temp-mail: {temp_email}", "INFO")
        log(f"Пароль: {password}", "INFO")
        log(f"Статус: Тестування завершено ✅", "SUCCESS")
        
        log("\n⏳ Браузери залишаються відкритими для спостереження...", "INFO")
        log("Натисніть Ctrl+C для завершення", "INFO")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            log("\nЗавершення...", "INFO")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
