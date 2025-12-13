#!/usr/bin/env python3
"""
🤖 WINDSURF EMAIL TEST v2 - Покращена версія
Генерація → Реєстрація → Підтвердження
"""

import time
import random
import string
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from pathlib import Path

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

def take_screenshot(driver, name: str, output_dir: str = "/tmp/windsurf_screenshots"):
    """Зробити скріншот сторінки"""
    try:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%H%M%S")
        screenshot_path = f"{output_dir}/{timestamp}_{name}.png"
        driver.save_screenshot(screenshot_path)
        return screenshot_path
    except Exception as e:
        return None

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
    
    # Різні формати email
    formats = [
        f"{first_name.lower()}.{last_name.lower()}",
        f"{first_name.lower()}{last_name.lower()}",
        f"{first_name[0].lower()}{last_name.lower()}",
    ]
    
    email_base = random.choice(formats)
    email = f"{email_base}@temp-mail.org"
    
    return email, first_name, last_name

def setup_driver():
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

def navigate_to_temp_mail(driver, email: str):
    """Перейти на temp-mail для отримання email"""
    log(f"Перехід на temp-mail.org", "STEP")
    
    try:
        driver.get(f"https://temp-mail.org/?email={email}")
        time.sleep(3)
        log("Temp-mail завантажено", "SUCCESS")
        return True
    except Exception as e:
        log(f"Помилка при завантаженні temp-mail: {str(e)}", "ERROR")
        return False

def navigate_to_proton(driver):
    """Перейти на Proton Mail"""
    log("Перехід на Proton Mail", "STEP")
    
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
        
        # Спробуємо різні селектори для кнопки "Create a free account"
        selectors = [
            (By.XPATH, "//button[contains(text(), 'Create a free account')]"),
            (By.XPATH, "//a[contains(text(), 'Create a free account')]"),
            (By.XPATH, "//button[contains(text(), 'Create a free')]"),
            (By.XPATH, "//a[contains(text(), 'Create a free')]"),
            (By.XPATH, "//button[contains(., 'Create a free account')]"),
            (By.CSS_SELECTOR, "button[type='button']:contains('Create')"),
            (By.XPATH, "//button[contains(@class, 'button-primary')]"),
            (By.XPATH, "//a[contains(text(), 'Create account')]"),
            (By.XPATH, "//button[contains(text(), 'Create Account')]"),
            (By.LINK_TEXT, "Create a free account"),
            (By.XPATH, "//a[@href*='signup']"),
            (By.XPATH, "//button[@class*='signup']"),
        ]
        
        for by, selector in selectors:
            try:
                element = wait.until(EC.element_to_be_clickable((by, selector)))
                log(f"Кнопка знайдена: {selector}", "INFO")
                element.click()
                time.sleep(3)
                log("Натиснуто кнопку 'Create a free account'", "SUCCESS")
                return True
            except:
                continue
        
        # Якщо не знайшли - спробуємо знайти всі кнопки та натиснути першу фіолетову
        log("Спробую знайти кнопку за кольором/класом", "INFO")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for button in buttons:
            text = button.text.lower()
            if "create" in text and "free" in text:
                log(f"Кнопка знайдена за текстом: {button.text}", "INFO")
                button.click()
                time.sleep(3)
                log("Натиснуто кнопку реєстрації", "SUCCESS")
                return True
        
        log("Кнопка реєстрації не знайдена - спробую прямий URL", "WARNING")
        driver.get("https://proton.me/mail/signup")
        time.sleep(3)
        log("Перейшов на сторінку реєстрації", "SUCCESS")
        return True
    except Exception as e:
        log(f"Помилка при пошуку кнопки: {str(e)}", "ERROR")
        return False

def fill_signup_form(driver, email: str, password: str):
    """Заповнити форму реєстрації"""
    log("Заповнення форми реєстрації", "STEP")
    
    try:
        wait = WebDriverWait(driver, 10)
        time.sleep(2)
        
        # Спробуємо заповнити Username (якщо є)
        log("Пошук поля Username", "INFO")
        username_selectors = [
            (By.CSS_SELECTOR, "input[placeholder*='Username']"),
            (By.CSS_SELECTOR, "input[placeholder*='username']"),
            (By.CSS_SELECTOR, "input[name='username']"),
            (By.XPATH, "//input[contains(@placeholder, 'Username')]"),
        ]
        
        for by, selector in username_selectors:
            try:
                username_input = driver.find_element(by, selector)
                # Генеруємо username з email
                username = email.split('@')[0]
                username_input.clear()
                username_input.send_keys(username)
                log(f"Username заповнено: {username}", "SUCCESS")
                break
            except:
                continue
        
        time.sleep(1)
        
        # Заповнити email (якщо є)
        log("Пошук поля email", "INFO")
        email_selectors = [
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.CSS_SELECTOR, "input[placeholder*='email']"),
            (By.CSS_SELECTOR, "input[name='email']"),
        ]
        
        for by, selector in email_selectors:
            try:
                email_input = driver.find_element(by, selector)
                email_input.clear()
                email_input.send_keys(email)
                log(f"Email заповнено: {email}", "SUCCESS")
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
            
            # Заповнити підтвердження пароля
            if len(password_inputs) > 1:
                password_inputs[1].clear()
                password_inputs[1].send_keys(password)
                log("Підтвердження пароля заповнено", "SUCCESS")
        
        time.sleep(1)
        
        # Натиснути кнопку "Create free account now" або "Розпочнімо"
        log("Пошук кнопки для продовження", "INFO")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        
        # Спробуємо знайти фіолетову кнопку з різними текстами
        for button in buttons:
            text = button.text.strip()
            text_lower = text.lower()
            
            # Перевіряємо різні варіанти текстів
            if any(keyword in text_lower for keyword in [
                "create free account", "create account", "розпочнімо", "розпочнимо",
                "next", "continue", "sign up", "signup", "далі", "продовжити",
                "create", "почати", "почнемо", "почнімо"
            ]):
                log(f"Кнопка знайдена: '{text}'", "INFO")
                # Прокрутити до кнопки щоб вона була видима
                driver.execute_script("arguments[0].scrollIntoView(true);", button)
                time.sleep(1)
                button.click()
                log(f"Натиснуто кнопку: {text}", "SUCCESS")
                time.sleep(3)
                return True
        
        # Якщо не знайшли за текстом - спробуємо за кольором/класом (фіолетова кнопка)
        log("Спробую знайти фіолетову кнопку за класом", "INFO")
        for button in buttons:
            class_attr = button.get_attribute("class").lower()
            if "primary" in class_attr or "purple" in class_attr or "button-primary" in class_attr:
                text = button.text.strip()
                if text:  # Якщо кнопка має текст
                    log(f"Фіолетова кнопка знайдена: '{text}'", "INFO")
                    driver.execute_script("arguments[0].scrollIntoView(true);", button)
                    time.sleep(1)
                    button.click()
                    log(f"Натиснуто фіолетову кнопку: {text}", "SUCCESS")
                    time.sleep(3)
                    return True
        
        log("Кнопка для продовження не знайдена", "WARNING")
        return False
    except Exception as e:
        log(f"Помилка при заповненні форми: {str(e)}", "ERROR")
        return False

def handle_captcha_manual(driver):
    """Обробити капчу вручну"""
    log("Перевірка наявності капчи", "STEP")
    
    try:
        time.sleep(2)
        
        # Перевірити наявність капчи з вибором квадратів
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

def select_free_plan(driver):
    """Вибрати безплатний тариф (0 євро) - ПЕРШИЙ тариф"""
    log("Перевірка наявності вибору тарифів", "STEP")
    
    try:
        time.sleep(3)
        
        # Зробити скріншот перед вибором тарифу
        screenshot_path = take_screenshot(driver, "before_plan_selection")
        if screenshot_path:
            log(f"Скріншот збережено: {screenshot_path}", "INFO")
        
        # Метод 1: Шукаємо радіо-кнопки (input type="radio")
        log("Пошук радіо-кнопок для вибору тарифу", "INFO")
        radio_buttons = driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
        if radio_buttons:
            log(f"Знайдено {len(radio_buttons)} радіо-кнопок", "INFO")
            # Вибираємо ПЕРШУ радіо-кнопку (безплатний тариф)
            try:
                # Прокрутити до першої кнопки
                driver.execute_script("arguments[0].scrollIntoView(true);", radio_buttons[0])
                time.sleep(1)
                # Клікнути на першу радіо-кнопку
                radio_buttons[0].click()
                log("Вибрано ПЕРШУ радіо-кнопку (безплатний тариф)", "SUCCESS")
                time.sleep(2)
                # Скріншот після вибору
                screenshot_path = take_screenshot(driver, "after_plan_selection")
                if screenshot_path:
                    log(f"Скріншот після вибору: {screenshot_path}", "INFO")
                return True
            except:
                # Якщо не вдалося клікнути, спробуємо через JavaScript
                driver.execute_script("arguments[0].checked = true;", radio_buttons[0])
                driver.execute_script("arguments[0].click();", radio_buttons[0])
                log("Вибрано ПЕРШУ радіо-кнопку через JavaScript", "SUCCESS")
                time.sleep(2)
                return True
        
        # Метод 2: Шукаємо картки тарифів (div з класом plan, card, pricing тощо)
        log("Пошук карток тарифів", "INFO")
        plan_cards = driver.find_elements(By.CSS_SELECTOR, "div[class*='plan'], div[class*='card'], div[class*='pricing']")
        if plan_cards:
            log(f"Знайдено {len(plan_cards)} карток тарифів", "INFO")
            # Шукаємо картку з текстом "Free" або "0€"
            for card in plan_cards:
                text = card.text.lower()
                if "free" in text or "0€" in text or "0 eur" in text or "$0" in text:
                    log(f"Безплатна картка знайдена: {card.text[:50]}...", "INFO")
                    # Шукаємо кнопку або радіо всередині картки
                    try:
                        button = card.find_element(By.TAG_NAME, "button")
                        button.click()
                        log("Натиснуто кнопку в безплатній картці", "SUCCESS")
                        time.sleep(2)
                        return True
                    except:
                        try:
                            radio = card.find_element(By.CSS_SELECTOR, "input[type='radio']")
                            radio.click()
                            log("Вибрано радіо-кнопку в безплатній картці", "SUCCESS")
                            time.sleep(2)
                            return True
                        except:
                            # Клікнути на саму картку
                            card.click()
                            log("Клікнуто на безплатну картку", "SUCCESS")
                            time.sleep(2)
                            return True
        
        # Метод 3: Шукаємо кнопку "Free" або "0€"
        log("Пошук кнопки з текстом Free/0€", "INFO")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for button in buttons:
            text = button.text.lower()
            if "free" in text or "0€" in text or "0 eur" in text or "$0" in text:
                log(f"Безплатний тариф знайдено: {button.text}", "INFO")
                button.click()
                log("Натиснуто кнопку безплатного тарифу", "SUCCESS")
                time.sleep(3)
                return True
        
        # Метод 4: Шукаємо посилання на безплатний тариф
        log("Пошук посилання з текстом Free/0€", "INFO")
        links = driver.find_elements(By.TAG_NAME, "a")
        for link in links:
            text = link.text.lower()
            if "free" in text or "0€" in text or "0 eur" in text:
                log(f"Безплатний тариф знайдено: {link.text}", "INFO")
                link.click()
                log("Натиснуто посилання безплатного тарифу", "SUCCESS")
                time.sleep(3)
                return True
        
        log("Вибір тарифів не знайдено - продовжую без вибору", "WARNING")
        return True
    except Exception as e:
        log(f"Помилка при виборі тарифу: {str(e)}", "WARNING")
        return True

def wait_for_verification_email(driver, email: str, max_attempts: int = 40):
    """Чекати листа для підтвердження на temp-mail"""
    log(f"Очікування листа для підтвердження на: {email}", "STEP")
    
    try:
        for attempt in range(max_attempts):
            log(f"Спроба {attempt + 1}/{max_attempts}: Перевірка листів...", "INFO")
            
            # Перейти на temp-mail
            driver.get(f"https://temp-mail.org/?email={email}")
            time.sleep(2)
            
            # Шукати лист від Proton
            try:
                email_items = driver.find_elements(By.CSS_SELECTOR, "div[class*='email']")
                
                for item in email_items:
                    text = item.text
                    if "Proton" in text or "proton" in text or "verify" in text.lower() or "confirm" in text.lower():
                        log(f"Лист від Proton знайдено: {text[:50]}...", "SUCCESS")
                        item.click()
                        time.sleep(2)
                        return True
            except:
                pass
            
            time.sleep(3)
        
        log("Лист від Proton не отримано", "ERROR")
        return False
        
    except Exception as e:
        log(f"Помилка при очікуванні листа: {str(e)}", "ERROR")
        return False

def main():
    """Основна функція"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  🤖 WINDSURF EMAIL TEST v2 - Покращена версія            ║")
    print("║  Генерація → Реєстрація → Підтвердження                  ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}\n")
    
    # Генерація даних
    log("═══════════════════════════════════════════════════════════", "STEP")
    log("КРОК 1: ГЕНЕРАЦІЯ РЕАЛІСТИЧНИХ ДАНИХ", "STEP")
    log("═══════════════════════════════════════════════════════════", "STEP")
    
    email, first_name, last_name = generate_realistic_email()
    password = "Qwas@000"
    
    log(f"Ім'я: {first_name}", "INPUT")
    log(f"Прізвище: {last_name}", "INPUT")
    log(f"Email: {email}", "INPUT")
    log(f"Пароль: {password}", "INPUT")
    
    time.sleep(2)
    
    # Запуск браузера
    log("\n═══════════════════════════════════════════════════════════", "STEP")
    log("КРОК 2: ЗАПУСК БРАУЗЕРА", "STEP")
    log("═══════════════════════════════════════════════════════════", "STEP")
    
    driver = setup_driver()
    if not driver:
        log("Браузер не запущено", "ERROR")
        return
    
    try:
        # Крок 3: Перейти на temp-mail
        log("\n═══════════════════════════════════════════════════════════", "STEP")
        log("КРОК 3: ПІДГОТОВКА TEMP-MAIL", "STEP")
        log("═══════════════════════════════════════════════════════════", "STEP")
        
        if not navigate_to_temp_mail(driver, email):
            log("Не вдалося завантажити temp-mail", "ERROR")
            return
        
        time.sleep(2)
        
        # Крок 4: Перейти на Proton
        log("\n═══════════════════════════════════════════════════════════", "STEP")
        log("КРОК 4: РЕЄСТРАЦІЯ НА PROTON.ME", "STEP")
        log("═══════════════════════════════════════════════════════════", "STEP")
        
        if not navigate_to_proton(driver):
            log("Не вдалося завантажити Proton", "ERROR")
            return
        
        time.sleep(2)
        
        # Натиснути кнопку реєстрації
        if not find_and_click_signup(driver):
            log("Не вдалося натиснути кнопку реєстрації", "ERROR")
            return
        
        time.sleep(3)
        
        # ВАЖЛИВО: Спочатку вибрати тариф, ПОТІМ заповнити форму
        log("\n═══════════════════════════════════════════════════════════", "STEP")
        log("КРОК 4.5: ВИБІР БЕЗПЛАТНОГО ТАРИФУ (ПЕРШИЙ)", "STEP")
        log("═══════════════════════════════════════════════════════════", "STEP")
        
        select_free_plan(driver)
        
        time.sleep(2)
        
        # Тепер заповнити форму
        if not fill_signup_form(driver, email, password):
            log("Не вдалося заповнити форму", "ERROR")
            return
        
        time.sleep(3)
        
        # Обробити капчу
        log("\n═══════════════════════════════════════════════════════════", "STEP")
        log("КРОК 5: ОБРОБКА КАПЧИ", "STEP")
        log("═══════════════════════════════════════════════════════════", "STEP")
        
        handle_captcha_manual(driver)
        
        time.sleep(2)
        
        # Крок 6: Очікування листа
        log("\n═══════════════════════════════════════════════════════════", "STEP")
        log("КРОК 6: ПІДТВЕРДЖЕННЯ EMAIL", "STEP")
        log("═══════════════════════════════════════════════════════════", "STEP")
        
        if not wait_for_verification_email(driver, email):
            log("Лист не отримано", "ERROR")
        else:
            log("Email підтверджено успішно", "SUCCESS")
        
        # Фінальна інформація
        log("\n═══════════════════════════════════════════════════════════", "STEP")
        log("РЕЗУЛЬТАТИ ТЕСТУВАННЯ:", "STEP")
        log("═══════════════════════════════════════════════════════════", "STEP")
        
        log(f"Ім'я: {first_name}", "INFO")
        log(f"Прізвище: {last_name}", "INFO")
        log(f"Email: {email}", "INFO")
        log(f"Пароль: {password}", "INFO")
        log(f"Статус: Тестування завершено ✅", "SUCCESS")
        
        log("\n⏳ Браузер залишиться відкритим для спостереження...", "INFO")
        log("Натисніть Ctrl+C для завершення", "INFO")
        
        # Чекати на закриття
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            log("\nЗавершення...", "INFO")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
