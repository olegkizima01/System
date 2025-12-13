#!/usr/bin/env python3
"""
🤖 WINDSURF EMAIL TEST - Тестування реєстрації та підтвердження почти
Генерація реалістичних даних → Реєстрація → Підтвердження
"""

import asyncio
import os
import sys
import random
from datetime import datetime
from playwright.async_api import async_playwright, Page, expect
import time

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
    UNDERLINE = '\033[4m'

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

async def navigate_to_proton(page: Page):
    """Перейти на Proton Mail"""
    log("Перехід на Proton Mail", "STEP")
    
    try:
        await page.goto("https://proton.me/mail", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(3)
        log("Proton Mail завантажено", "SUCCESS")
        return True
    except Exception as e:
        log(f"Помилка при завантаженні Proton: {str(e)}", "ERROR")
        return False

async def click_create_account(page: Page) -> bool:
    """Натиснути кнопку Create account"""
    log("Пошук кнопки 'Create account'", "STEP")
    
    try:
        # Спробуємо різні селектори
        selectors = [
            "button:has-text('Create account')",
            "button:has-text('Create Account')",
            "a:has-text('Create account')",
            "a:has-text('Create Account')",
            "[data-testid='create-account-button']",
        ]
        
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    await element.click()
                    await asyncio.sleep(2)
                    log("Натиснуто 'Create account'", "SUCCESS")
                    return True
            except:
                continue
        
        log("Кнопка 'Create account' не знайдена", "WARNING")
        return False
    except Exception as e:
        log(f"Помилка при пошуку кнопки: {str(e)}", "ERROR")
        return False

async def fill_email_field(page: Page, email: str) -> bool:
    """Заповнити поле email"""
    log(f"Заповнення email: {email}", "STEP")
    
    try:
        # Спробуємо різні селектори для email поля
        selectors = [
            "input[type='email']",
            "input[name='email']",
            "input[placeholder*='email' i]",
            "input[placeholder*='Email' i]",
        ]
        
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    await element.fill(email)
                    await asyncio.sleep(1)
                    log(f"Email заповнено: {email}", "SUCCESS")
                    return True
            except:
                continue
        
        log("Email поле не знайдено", "WARNING")
        return False
    except Exception as e:
        log(f"Помилка при заповненні email: {str(e)}", "ERROR")
        return False

async def fill_password_field(page: Page, password: str) -> bool:
    """Заповнити поле пароля"""
    log(f"Заповнення пароля", "STEP")
    
    try:
        # Спробуємо різні селектори для пароля
        selectors = [
            "input[type='password']",
            "input[name='password']",
            "input[placeholder*='password' i]",
            "input[placeholder*='Password' i]",
        ]
        
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    await element.fill(password)
                    await asyncio.sleep(1)
                    log("Пароль заповнено", "SUCCESS")
                    return True
            except:
                continue
        
        log("Поле пароля не знайдено", "WARNING")
        return False
    except Exception as e:
        log(f"Помилка при заповненні пароля: {str(e)}", "ERROR")
        return False

async def click_next_button(page: Page) -> bool:
    """Натиснути кнопку Next"""
    log("Пошук кнопки 'Next'", "STEP")
    
    try:
        selectors = [
            "button:has-text('Next')",
            "button:has-text('next')",
            "[data-testid='next-button']",
            "button[type='submit']",
        ]
        
        for selector in selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    await element.click()
                    await asyncio.sleep(3)
                    log("Натиснуто 'Next'", "SUCCESS")
                    return True
            except:
                continue
        
        log("Кнопка 'Next' не знайдена", "WARNING")
        return False
    except Exception as e:
        log(f"Помилка при натисканні Next: {str(e)}", "ERROR")
        return False

async def handle_captcha(page: Page) -> bool:
    """Обробити капчу"""
    log("Перевірка наявності капчи", "STEP")
    
    try:
        # Чекати капчу
        captcha_selectors = [
            "div[class*='captcha']",
            "iframe[title*='captcha']",
            "div[class*='puzzle']",
        ]
        
        for selector in captcha_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    log("Капча знайдена - потребує ручного розв'язання", "WARNING")
                    log("⏳ Чекаю 90 секунд на розв'язання капчи...", "INFO")
                    await asyncio.sleep(90)
                    log("Час для капчи закінчився", "INFO")
                    return True
            except:
                continue
        
        log("Капча не знайдена", "INFO")
        return True
    except Exception as e:
        log(f"Помилка при обробці капчи: {str(e)}", "WARNING")
        return True

async def wait_for_verification_email(page: Page, email: str, max_attempts: int = 30) -> bool:
    """Чекати листа для підтвердження на temp-mail"""
    log(f"Очікування листа для підтвердження на: {email}", "STEP")
    
    try:
        # Перейти на temp-mail
        await page.goto(f"https://temp-mail.org/?email={email}", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(2)
        
        for attempt in range(max_attempts):
            log(f"Спроба {attempt + 1}/{max_attempts}: Перевірка листів...", "INFO")
            
            # Оновити сторінку
            await page.reload()
            await asyncio.sleep(2)
            
            # Шукати лист від Proton
            email_items = await page.query_selector_all("div[class*='email-item']")
            
            if email_items:
                for item in email_items:
                    text = await item.text_content()
                    if "Proton" in text or "proton" in text or "verify" in text.lower():
                        log(f"Лист від Proton знайдено: {text[:50]}...", "SUCCESS")
                        await item.click()
                        await asyncio.sleep(2)
                        return True
            
            await asyncio.sleep(3)
        
        log("Лист від Proton не отримано за 90 секунд", "ERROR")
        return False
        
    except Exception as e:
        log(f"Помилка при очікуванні листа: {str(e)}", "ERROR")
        return False

async def get_verification_link(page: Page) -> str:
    """Отримати посилання для підтвердження з листа"""
    log("Пошук посилання для підтвердження", "STEP")
    
    try:
        # Шукати посилання
        links = await page.query_selector_all("a")
        
        for link in links:
            href = await link.get_attribute("href")
            if href and ("confirm" in href.lower() or "verify" in href.lower()):
                log(f"Посилання для підтвердження знайдено", "SUCCESS")
                return href
        
        log("Посилання для підтвердження не знайдено", "WARNING")
        return None
    except Exception as e:
        log(f"Помилка при пошуку посилання: {str(e)}", "ERROR")
        return None

async def create_backup_email(page: Page) -> str:
    """Створити резервну почту на temp-mail"""
    log("Створення резервної почти на temp-mail", "STEP")
    
    try:
        await page.goto("https://temp-mail.org", wait_until="networkidle", timeout=30000)
        await asyncio.sleep(2)
        
        # Отримати згенеровану почту
        email_display = await page.query_selector("input[id*='email']")
        if email_display:
            backup_email = await email_display.input_value()
            log(f"Резервна почта створена: {backup_email}", "SUCCESS")
            return backup_email
        
        log("Резервна почта не створена", "ERROR")
        return None
    except Exception as e:
        log(f"Помилка при створенні резервної почти: {str(e)}", "ERROR")
        return None

async def main():
    """Основна функція"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  🤖 WINDSURF EMAIL TEST - Тестування реєстрації          ║")
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
    
    await asyncio.sleep(2)
    
    # Запуск браузера
    log("\n═══════════════════════════════════════════════════════════", "STEP")
    log("КРОК 2: ЗАПУСК БРАУЗЕРА", "STEP")
    log("═══════════════════════════════════════════════════════════", "STEP")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        # Крок 3: Перейти на Proton
        log("\n═══════════════════════════════════════════════════════════", "STEP")
        log("КРОК 3: РЕЄСТРАЦІЯ НА PROTON.ME", "STEP")
        log("═══════════════════════════════════════════════════════════", "STEP")
        
        proton_ok = await navigate_to_proton(page)
        if not proton_ok:
            log("Не вдалося завантажити Proton", "ERROR")
            await browser.close()
            return
        
        await asyncio.sleep(2)
        
        # Натиснути Create account
        create_ok = await click_create_account(page)
        if not create_ok:
            log("Не вдалося натиснути Create account", "ERROR")
            await browser.close()
            return
        
        await asyncio.sleep(2)
        
        # Заповнити email
        email_ok = await fill_email_field(page, email)
        if not email_ok:
            log("Не вдалося заповнити email", "ERROR")
            await browser.close()
            return
        
        await asyncio.sleep(1)
        
        # Заповнити пароль
        password_ok = await fill_password_field(page, password)
        if not password_ok:
            log("Не вдалося заповнити пароль", "ERROR")
            await browser.close()
            return
        
        await asyncio.sleep(1)
        
        # Натиснути Next
        next_ok = await click_next_button(page)
        if not next_ok:
            log("Не вдалося натиснути Next", "ERROR")
            await browser.close()
            return
        
        await asyncio.sleep(3)
        
        # Обробити капчу
        log("\n═══════════════════════════════════════════════════════════", "STEP")
        log("КРОК 4: ОБРОБКА КАПЧИ", "STEP")
        log("═══════════════════════════════════════════════════════════", "STEP")
        
        captcha_ok = await handle_captcha(page)
        
        await asyncio.sleep(2)
        
        # Крок 5: Очікування листа
        log("\n═══════════════════════════════════════════════════════════", "STEP")
        log("КРОК 5: ПІДТВЕРДЖЕННЯ EMAIL", "STEP")
        log("═══════════════════════════════════════════════════════════", "STEP")
        
        email_received = await wait_for_verification_email(page, email)
        if not email_received:
            log("Лист не отримано", "ERROR")
            await browser.close()
            return
        
        await asyncio.sleep(2)
        
        # Отримати посилання для підтвердження
        verify_link = await get_verification_link(page)
        if verify_link:
            log(f"Посилання: {verify_link[:80]}...", "INFO")
        
        await asyncio.sleep(2)
        
        # Крок 6: Створення резервної почти
        log("\n═══════════════════════════════════════════════════════════", "STEP")
        log("КРОК 6: СТВОРЕННЯ РЕЗЕРВНОЇ ПОЧТИ", "STEP")
        log("═══════════════════════════════════════════════════════════", "STEP")
        
        backup_email = await create_backup_email(page)
        if not backup_email:
            log("Резервна почта не створена", "ERROR")
            await browser.close()
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
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            log("\nЗавершення...", "INFO")
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
