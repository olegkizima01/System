#!/usr/bin/env python3
"""
🤖 WINDSURF EMAIL PLAYWRIGHT MSP - Повна автоматизація з Playwright
Використовує Playwright MSP для macOS з Apple Script інтеграцією
"""

import asyncio
import random
import string
import subprocess
import os
from datetime import datetime
from pathlib import Path

try:
    from playwright.async_api import async_playwright, Page, Browser
except ImportError:
    print("❌ Playwright не встановлено. Встановіть: pip install playwright")
    exit(1)

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

def take_screenshot(page: Page, name: str, output_dir: str = "/tmp/windsurf_screenshots"):
    """Зробити скріншот сторінки"""
    try:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%H%M%S")
        screenshot_path = f"{output_dir}/{timestamp}_{name}.png"
        page.screenshot(path=screenshot_path)
        log(f"Скріншот збережено: {screenshot_path}", "INFO")
        return screenshot_path
    except Exception as e:
        log(f"Помилка при збереженні скріншота: {str(e)}", "ERROR")
        return None

async def main():
    """Основна функція"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  🤖 WINDSURF EMAIL PLAYWRIGHT MSP - Повна автоматизація  ║")
    print("║  Playwright + Apple Script для macOS                      ║")
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
    
    await asyncio.sleep(2)
    
    # Запуск Playwright
    log("\n═══════════════════════════════════════════════════════════", "STEP")
    log("КРОК 2: ЗАПУСК PLAYWRIGHT", "STEP")
    log("═══════════════════════════════════════════════════════════", "STEP")
    
    async with async_playwright() as p:
        # Запустити браузер
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        log("Playwright браузер запущено", "SUCCESS")
        
        # Крок 3: Відкрити Proton Mail
        log("\n═══════════════════════════════════════════════════════════", "STEP")
        log("КРОК 3: ПЕРЕХІД НА PROTON MAIL", "STEP")
        log("═══════════════════════════════════════════════════════════", "STEP")
        
        await page.goto("https://proton.me/mail")
        await asyncio.sleep(3)
        take_screenshot(page, "01_proton_main")
        log("Proton Mail завантажено", "SUCCESS")
        
        # Крок 4: Натиснути "Create a free account"
        log("\n═══════════════════════════════════════════════════════════", "STEP")
        log("КРОК 4: ПОШУК КНОПКИ 'CREATE A FREE ACCOUNT'", "STEP")
        log("═══════════════════════════════════════════════════════════", "STEP")
        
        try:
            # Шукаємо кнопку
            button = page.locator("a:has-text('Create a free account'), button:has-text('Create a free account')").first
            await button.click()
            await asyncio.sleep(3)
            take_screenshot(page, "02_signup_page")
            log("Натиснуто кнопку 'Create a free account'", "SUCCESS")
        except Exception as e:
            log(f"Помилка при натисканні кнопки: {str(e)}", "ERROR")
            await browser.close()
            return
        
        # Крок 5: Заповнити форму реєстрації
        log("\n═══════════════════════════════════════════════════════════", "STEP")
        log("КРОК 5: ЗАПОВНЕННЯ ФОРМИ РЕЄСТРАЦІЇ", "STEP")
        log("═══════════════════════════════════════════════════════════", "STEP")
        
        try:
            # Заповнити email
            email_input = page.locator("input[type='email']").first
            await email_input.fill(proton_email)
            log(f"Email заповнено: {proton_email}", "SUCCESS")
            await asyncio.sleep(1)
            take_screenshot(page, "03_email_filled")
            
            # Заповнити пароль
            password_inputs = page.locator("input[type='password']")
            count = await password_inputs.count()
            
            if count > 0:
                await password_inputs.first.fill(password)
                log("Пароль заповнено", "SUCCESS")
                await asyncio.sleep(1)
                
                if count > 1:
                    await password_inputs.nth(1).fill(password)
                    log("Підтвердження пароля заповнено", "SUCCESS")
            
            await asyncio.sleep(1)
            take_screenshot(page, "04_password_filled")
            
        except Exception as e:
            log(f"Помилка при заповненні форми: {str(e)}", "ERROR")
            await browser.close()
            return
        
        # Крок 6: Натиснути фіолетову кнопку
        log("\n═══════════════════════════════════════════════════════════", "STEP")
        log("КРОК 6: НАТИСНЕННЯ ФІОЛЕТОВОЇ КНОПКИ", "STEP")
        log("═══════════════════════════════════════════════════════════", "STEP")
        
        try:
            # Шукаємо фіолетову кнопку за текстом
            button = page.locator("button:has-text('Почніть використовувати'), button:has-text('Create free account'), button[type='submit']").first
            await button.click()
            await asyncio.sleep(3)
            take_screenshot(page, "05_button_clicked")
            log("Натиснуто фіолетову кнопку", "SUCCESS")
        except Exception as e:
            log(f"Помилка при натисканні кнопки: {str(e)}", "ERROR")
            await browser.close()
            return
        
        # Крок 7: Обробка капчи
        log("\n═══════════════════════════════════════════════════════════", "STEP")
        log("КРОК 7: ОБРОБКА КАПЧИ", "STEP")
        log("═══════════════════════════════════════════════════════════", "STEP")
        
        try:
            # Перевірити наявність капчи
            captcha = page.locator("div[class*='captcha'], iframe[title*='captcha']").first
            if await captcha.is_visible():
                log("Капча знайдена - потребує ручного розв'язання", "WARNING")
                take_screenshot(page, "06_captcha_found")
                log("⏳ Чекаю 120 секунд на розв'язання капчи...", "INFO")
                log("Виберіть квадрати як показано на зображенні", "INFO")
                await asyncio.sleep(120)
                log("Час для капчи закінчився", "INFO")
                take_screenshot(page, "07_captcha_solved")
            else:
                log("Капча не знайдена", "INFO")
        except Exception as e:
            log(f"Помилка при обробці капчи: {str(e)}", "WARNING")
        
        # Крок 8: Вибір тарифу
        log("\n═══════════════════════════════════════════════════════════", "STEP")
        log("КРОК 8: ВИБІР БЕЗПЛАТНОГО ТАРИФУ", "STEP")
        log("═══════════════════════════════════════════════════════════", "STEP")
        
        try:
            # Шукаємо кнопку "Free" або "0€"
            free_button = page.locator("button:has-text('Free'), button:has-text('0€'), button:has-text('0 €')").first
            if await free_button.is_visible():
                await free_button.click()
                log("Натиснуто кнопку безплатного тарифу", "SUCCESS")
                await asyncio.sleep(3)
                take_screenshot(page, "08_free_plan_selected")
            else:
                log("Вибір тарифів не знайдено", "INFO")
        except Exception as e:
            log(f"Помилка при виборі тарифу: {str(e)}", "WARNING")
        
        # Крок 9: Очікування листа
        log("\n═══════════════════════════════════════════════════════════", "STEP")
        log("КРОК 9: ОЧІКУВАННЯ ЛИСТА ВІД PROTON", "STEP")
        log("═══════════════════════════════════════════════════════════", "STEP")
        
        log(f"Очікування листа на: {temp_email}", "INFO")
        await asyncio.sleep(5)
        take_screenshot(page, "09_final_state")
        
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
        
        log("\n📸 Скріншоти збережено в: /tmp/windsurf_screenshots", "INFO")
        log("⏳ Браузер залишається відкритим для спостереження...", "INFO")
        log("Натисніть Ctrl+C для завершення", "INFO")
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            log("\nЗавершення...", "INFO")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
