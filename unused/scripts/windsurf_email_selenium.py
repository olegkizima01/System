#!/usr/bin/env python3
"""
🤖 WINDSURF EMAIL TEST - Selenium версія
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
    "Evelyn", "Abigail", "Emily", "Elizabeth", "Sofia", "Avery", "Ella",
    "Scarlett", "Victoria", "Madison", "Chloe", "Penelope", "Layla", "Riley",
    "Zoey", "Nora", "Lily", "Eleanor", "Hannah", "Lillian", "Addison",
    "William", "Benjamin", "Lucas", "Henry", "Alexander", "Mason", "Michael",
    "Ethan", "Daniel", "Jacob", "Logan", "Jackson", "Sebastian", "Aiden"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Young", "Allen", "King", "Wright",
    "Scott", "Torres", "Peterson", "Phillips", "Campbell", "Parker", "Evans",
    "Edwards", "Collins", "Reeves", "Stewart", "Morris", "Morales", "Murphy",
    "Cook", "Rogers", "Gutierrez", "Ortiz", "Morgan", "Peterson", "Cooper"
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
        f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 99)}",
    ]
    
    email_base = random.choice(formats)
    email = f"{email_base}@temp-mail.org"
    
    return email, first_name, last_name

def setup_driver():
    """Налаштування Chrome драйвера"""
    log("Налаштування Chrome браузера", "STEP")
    
    try:
        chrome_options = Options()
        # chrome_options.add_argument("--headless")  # Розкоментуйте для headless режиму
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        log("Chrome браузер налаштований", "SUCCESS")
        return driver
    except Exception as e:
        log(f"Помилка при налаштуванні браузера: {str(e)}", "ERROR")
        return None

def navigate_to_proton(driver):
    """Перейти на Proton Mail"""
    log("Перехід на Proton Mail", "STEP")
    
    try:
        driver.get("https://proton.me/mail")
        time.sleep(3)
        log("Proton Mail завантажено", "SUCCESS")
        return True
    except Exception as e:
        log(f"Помилка при завантаженні Proton: {str(e)}", "ERROR")
        return False

def click_create_account(driver):
    """Натиснути кнопку Create account"""
    log("Пошук кнопки 'Create account'", "STEP")
    
    try:
        wait = WebDriverWait(driver, 10)
        
        # Спробуємо різні селектори
        selectors = [
            (By.XPATH, "//button[contains(text(), 'Create account')]"),
            (By.XPATH, "//button[contains(text(), 'Create Account')]"),
            (By.XPATH, "//a[contains(text(), 'Create account')]"),
            (By.XPATH, "//a[contains(text(), 'Create Account')]"),
        ]
        
        for by, selector in selectors:
            try:
                element = wait.until(EC.element_to_be_clickable((by, selector)))
                element.click()
                time.sleep(2)
                log("Натиснуто 'Create account'", "SUCCESS")
                return True
            except:
                continue
        
        log("Кнопка 'Create account' не знайдена", "WARNING")
        return False
    except Exception as e:
        log(f"Помилка при пошуку кнопки: {str(e)}", "ERROR")
        return False

def fill_email_field(driver, email: str):
    """Заповнити поле email"""
    log(f"Заповнення email: {email}", "STEP")
    
    try:
        wait = WebDriverWait(driver, 10)
        
        # Спробуємо різні селектори для email поля
        selectors = [
            (By.CSS_SELECTOR, "input[type='email']"),
            (By.CSS_SELECTOR, "input[name='email']"),
            (By.XPATH, "//input[contains(@placeholder, 'email')]"),
            (By.XPATH, "//input[contains(@placeholder, 'Email')]"),
        ]
        
        for by, selector in selectors:
            try:
                element = wait.until(EC.presence_of_element_located((by, selector)))
                element.clear()
                element.send_keys(email)
                time.sleep(1)
                log(f"Email заповнено: {email}", "SUCCESS")
                return True
            except:
                continue
        
        log("Email поле не знайдено", "WARNING")
        return False
    except Exception as e:
        log(f"Помилка при заповненні email: {str(e)}", "ERROR")
        return False

def fill_password_field(driver, password: str):
    """Заповнити поле пароля"""
    log("Заповнення пароля", "STEP")
    
    try:
        wait = WebDriverWait(driver, 10)
        
        # Спробуємо різні селектори для пароля
        selectors = [
            (By.CSS_SELECTOR, "input[type='password']"),
            (By.CSS_SELECTOR, "input[name='password']"),
            (By.XPATH, "//input[contains(@placeholder, 'password')]"),
            (By.XPATH, "//input[contains(@placeholder, 'Password')]"),
        ]
        
        for by, selector in selectors:
            try:
                element = wait.until(EC.presence_of_element_located((by, selector)))
                element.clear()
                element.send_keys(password)
                time.sleep(1)
                log("Пароль заповнено", "SUCCESS")
                return True
            except:
                continue
        
        log("Поле пароля не знайдено", "WARNING")
        return False
    except Exception as e:
        log(f"Помилка при заповненні пароля: {str(e)}", "ERROR")
        return False

def click_next_button(driver):
    """Натиснути кнопку Next"""
    log("Пошук кнопки 'Next'", "STEP")
    
    try:
        wait = WebDriverWait(driver, 10)
        
        selectors = [
            (By.XPATH, "//button[contains(text(), 'Next')]"),
            (By.XPATH, "//button[contains(text(), 'next')]"),
            (By.CSS_SELECTOR, "button[type='submit']"),
        ]
        
        for by, selector in selectors:
            try:
                element = wait.until(EC.element_to_be_clickable((by, selector)))
                element.click()
                time.sleep(3)
                log("Натиснуто 'Next'", "SUCCESS")
                return True
            except:
                continue
        
        log("Кнопка 'Next' не знайдена", "WARNING")
        return False
    except Exception as e:
        log(f"Помилка при натисканні Next: {str(e)}", "ERROR")
        return False

def handle_captcha(driver):
    """Обробити капчу"""
    log("Перевірка наявності капчи", "STEP")
    
    try:
        # Чекати капчу
        time.sleep(2)
        
        captcha_elements = driver.find_elements(By.CSS_SELECTOR, "div[class*='captcha']")
        if captcha_elements:
            log("Капча знайдена - потребує ручного розв'язання", "WARNING")
            log("⏳ Чекаю 90 секунд на розв'язання капчи...", "INFO")
            time.sleep(90)
            log("Час для капчи закінчився", "INFO")
            return True
        
        log("Капча не знайдена", "INFO")
        return True
    except Exception as e:
        log(f"Помилка при обробці капчи: {str(e)}", "WARNING")
        return True

def wait_for_verification_email(driver, email: str, max_attempts: int = 30):
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
                email_items = driver.find_elements(By.CSS_SELECTOR, "div[class*='email-item']")
                
                for item in email_items:
                    text = item.text
                    if "Proton" in text or "proton" in text or "verify" in text.lower():
                        log(f"Лист від Proton знайдено: {text[:50]}...", "SUCCESS")
                        item.click()
                        time.sleep(2)
                        return True
            except:
                pass
            
            time.sleep(3)
        
        log("Лист від Proton не отримано за 90 секунд", "ERROR")
        return False
        
    except Exception as e:
        log(f"Помилка при очікуванні листа: {str(e)}", "ERROR")
        return False

def get_verification_link(driver):
    """Отримати посилання для підтвердження з листа"""
    log("Пошук посилання для підтвердження", "STEP")
    
    try:
        # Шукати посилання
        links = driver.find_elements(By.TAG_NAME, "a")
        
        for link in links:
            href = link.get_attribute("href")
            if href and ("confirm" in href.lower() or "verify" in href.lower()):
                log(f"Посилання для підтвердження знайдено", "SUCCESS")
                return href
        
        log("Посилання для підтвердження не знайдено", "WARNING")
        return None
    except Exception as e:
        log(f"Помилка при пошуку посилання: {str(e)}", "ERROR")
        return None

def create_backup_email(driver):
    """Створити резервну почту на temp-mail"""
    log("Створення резервної почти на temp-mail", "STEP")
    
    try:
        driver.get("https://temp-mail.org")
        time.sleep(2)
        
        # Отримати згенеровану почту
        email_input = driver.find_element(By.CSS_SELECTOR, "input[id*='email']")
        backup_email = email_input.get_attribute("value")
        
        if backup_email:
            log(f"Резервна почта створена: {backup_email}", "SUCCESS")
            return backup_email
        
        log("Резервна почта не створена", "ERROR")
        return None
    except Exception as e:
        log(f"Помилка при створенні резервної почти: {str(e)}", "ERROR")
        return None

def main():
    """Основна функція"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  🤖 WINDSURF EMAIL TEST - Selenium версія                ║")
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
        # Крок 3: Перейти на Proton
        log("\n═══════════════════════════════════════════════════════════", "STEP")
        log("КРОК 3: РЕЄСТРАЦІЯ НА PROTON.ME", "STEP")
        log("═══════════════════════════════════════════════════════════", "STEP")
        
        if not navigate_to_proton(driver):
            log("Не вдалося завантажити Proton", "ERROR")
            return
        
        time.sleep(2)
        
        # Натиснути Create account
        if not click_create_account(driver):
            log("Не вдалося натиснути Create account", "ERROR")
            return
        
        time.sleep(2)
        
        # Заповнити email
        if not fill_email_field(driver, email):
            log("Не вдалося заповнити email", "ERROR")
            return
        
        time.sleep(1)
        
        # Заповнити пароль
        if not fill_password_field(driver, password):
            log("Не вдалося заповнити пароль", "ERROR")
            return
        
        time.sleep(1)
        
        # Натиснути Next
        if not click_next_button(driver):
            log("Не вдалося натиснути Next", "ERROR")
            return
        
        time.sleep(3)
        
        # Обробити капчу
        log("\n═══════════════════════════════════════════════════════════", "STEP")
        log("КРОК 4: ОБРОБКА КАПЧИ", "STEP")
        log("═══════════════════════════════════════════════════════════", "STEP")
        
        handle_captcha(driver)
        
        time.sleep(2)
        
        # Крок 5: Очікування листа
        log("\n═══════════════════════════════════════════════════════════", "STEP")
        log("КРОК 5: ПІДТВЕРДЖЕННЯ EMAIL", "STEP")
        log("═══════════════════════════════════════════════════════════", "STEP")
        
        if not wait_for_verification_email(driver, email):
            log("Лист не отримано", "ERROR")
            return
        
        time.sleep(2)
        
        # Отримати посилання для підтвердження
        verify_link = get_verification_link(driver)
        if verify_link:
            log(f"Посилання: {verify_link[:80]}...", "INFO")
        
        time.sleep(2)
        
        # Крок 6: Створення резервної почти
        log("\n═══════════════════════════════════════════════════════════", "STEP")
        log("КРОК 6: СТВОРЕННЯ РЕЗЕРВНОЇ ПОЧТИ", "STEP")
        log("═══════════════════════════════════════════════════════════", "STEP")
        
        backup_email = create_backup_email(driver)
        if not backup_email:
            log("Резервна почта не створена", "ERROR")
            return
        
        # Фінальна інформація
        log("\n═══════════════════════════════════════════════════════════", "STEP")
        log("РЕЗУЛЬТАТИ ТЕСТУВАННЯ:", "STEP")
        log("═══════════════════════════════════════════════════════════", "STEP")
        
        log(f"Ім'я: {first_name}", "INFO")
        log(f"Прізвище: {last_name}", "INFO")
        log(f"Email: {email}", "INFO")
        log(f"Пароль: {password}", "INFO")
        log(f"Резервна почта: {backup_email}", "INFO")
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
