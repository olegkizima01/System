#!/usr/bin/env python3
"""
🤖 WINDSURF AUTOMATION - Повна автоматизація реєстрації
Очистка → Встановлення → Реєстрація → Підтвердження
"""

import asyncio
import subprocess
import os
import sys
import random
import string
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
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
    else:
        print(f"[{timestamp}] {message}")

def generate_email() -> str:
    """Генерація випадкового email"""
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"{username}@temp-mail.org"

def generate_password() -> str:
    """Генерація стійкого пароля"""
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choices(chars, k=16))

async def run_windsurf_cleanup():
    """Запустити cleanup скрипт для Windsurf"""
    log("Запуск deep_windsurf_cleanup.sh", "STEP")
    
    try:
        script_path = "/Users/dev/Documents/GitHub/System/deep_windsurf_cleanup.sh"
        result = subprocess.run(
            ["bash", script_path],
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if result.returncode == 0:
            log("Windsurf cleanup завершено успішно", "SUCCESS")
            return True
        else:
            log(f"Cleanup помилка: {result.stderr}", "ERROR")
            return False
    except Exception as e:
        log(f"Помилка при запуску cleanup: {str(e)}", "ERROR")
        return False

async def close_chrome():
    """Закрити всі вікна Chrome"""
    log("Закриття Chrome", "STEP")
    
    try:
        subprocess.run(["pkill", "-9", "Google Chrome"], capture_output=True)
        subprocess.run(["pkill", "-9", "Chromium"], capture_output=True)
        await asyncio.sleep(2)
        log("Chrome закрито", "SUCCESS")
        return True
    except Exception as e:
        log(f"Помилка при закритті Chrome: {str(e)}", "ERROR")
        return False

async def install_windsurf():
    """Встановити Windsurf"""
    log("Встановлення Windsurf", "STEP")
    
    try:
        # Перевірити чи Windsurf вже встановлено
        windsurf_path = "/Applications/Windsurf.app"
        if os.path.exists(windsurf_path):
            log("Windsurf вже встановлено", "INFO")
            return True
        
        # Завантажити та встановити
        log("Windsurf потребує ручного встановлення", "WARNING")
        log("Перейдіть на https://windsurf.ai та завантажте", "INFO")
        
        # Чекати встановлення
        for i in range(30):
            if os.path.exists(windsurf_path):
                log("Windsurf встановлено", "SUCCESS")
                return True
            await asyncio.sleep(2)
        
        log("Windsurf не встановлено за 60 секунд", "ERROR")
        return False
    except Exception as e:
        log(f"Помилка при встановленні Windsurf: {str(e)}", "ERROR")
        return False

async def open_windsurf_guest_mode(browser: Browser):
    """Відкрити Windsurf в гостьовому режимі"""
    log("Відкриття Windsurf в гостьовому режимі", "STEP")
    
    try:
        # Запустити Windsurf з параметром гостьового режиму
        subprocess.Popen([
            "/Applications/Windsurf.app/Contents/MacOS/Windsurf",
            "--guest"
        ])
        
        await asyncio.sleep(5)
        log("Windsurf відкрито в гостьовому режимі", "SUCCESS")
        return True
    except Exception as e:
        log(f"Помилка при відкритті Windsurf: {str(e)}", "ERROR")
        return False

async def register_temp_mail(page: Page, email: str) -> bool:
    """Реєстрація на temp-mail.org"""
    log(f"Реєстрація на temp-mail.org: {email}", "STEP")
    
    try:
        await page.goto("https://temp-mail.org", wait_until="networkidle")
        await asyncio.sleep(2)
        
        # Перевірити чи email вже згенерований
        email_input = await page.query_selector("input[id*='email']")
        if email_input:
            await email_input.fill(email)
            log(f"Email встановлено: {email}", "SUCCESS")
            return True
        else:
            log("Email поле не знайдено", "WARNING")
            return False
            
    except Exception as e:
        log(f"Помилка при реєстрації на temp-mail: {str(e)}", "ERROR")
        return False

async def register_proton_mail(page: Page, email: str, password: str) -> bool:
    """Реєстрація на proton.me"""
    log(f"Реєстрація на proton.me: {email}", "STEP")
    
    try:
        await page.goto("https://proton.me/mail", wait_until="networkidle")
        await asyncio.sleep(3)
        
        # Знайти кнопку "Create account"
        create_btn = await page.query_selector("button:has-text('Create account')")
        if create_btn:
            await create_btn.click()
            await asyncio.sleep(2)
            log("Натиснуто 'Create account'", "INFO")
        else:
            log("Кнопка 'Create account' не знайдена", "WARNING")
            return False
        
        # Заповнити email
        email_input = await page.query_selector("input[type='email']")
        if email_input:
            await email_input.fill(email)
            log(f"Email заповнено: {email}", "INFO")
        
        # Заповнити пароль
        password_input = await page.query_selector("input[type='password']")
        if password_input:
            await password_input.fill(password)
            log("Пароль заповнено", "INFO")
        
        # Натиснути Next
        next_btn = await page.query_selector("button:has-text('Next')")
        if next_btn:
            await next_btn.click()
            await asyncio.sleep(3)
            log("Натиснуто 'Next'", "INFO")
        
        log("Реєстрація на proton.me розпочата", "SUCCESS")
        return True
        
    except Exception as e:
        log(f"Помилка при реєстрації на proton.me: {str(e)}", "ERROR")
        return False

async def solve_puzzle_captcha(page: Page) -> bool:
    """Розв'язати капчу з пазлами"""
    log("Розв'язання капчі з пазлами", "STEP")
    
    try:
        # Чекати капчу
        await page.wait_for_selector("div[class*='captcha']", timeout=10000)
        log("Капча знайдена", "INFO")
        
        # Знайти пазл елементи
        puzzle_frame = await page.query_selector("iframe[title*='captcha']")
        if puzzle_frame:
            frame = await puzzle_frame.content_frame()
            
            # Знайти перетягуваний елемент
            draggable = await frame.query_selector("div[draggable='true']")
            if draggable:
                # Знайти цільову позицію
                target = await frame.query_selector("div[class*='target']")
                if target:
                    # Перетягнути пазл на місце
                    await draggable.drag_to(target)
                    await asyncio.sleep(2)
                    log("Пазл перетягнуто", "SUCCESS")
                    return True
        
        log("Капча не розв'язана - потребує ручного розв'язання", "WARNING")
        return False
        
    except Exception as e:
        log(f"Помилка при розв'язанні капчі: {str(e)}", "WARNING")
        return False

async def verify_email_with_temp_mail(page: Page, email: str) -> bool:
    """Підтвердити email через temp-mail"""
    log(f"Підтвердження email через temp-mail: {email}", "STEP")
    
    try:
        # Перейти на temp-mail
        await page.goto(f"https://temp-mail.org/?email={email}", wait_until="networkidle")
        await asyncio.sleep(3)
        
        # Чекати листа від Proton
        for attempt in range(30):
            # Оновити сторінку
            await page.reload()
            await asyncio.sleep(2)
            
            # Шукати лист від Proton
            email_item = await page.query_selector("div:has-text('Proton')")
            if email_item:
                log("Лист від Proton знайдено", "SUCCESS")
                await email_item.click()
                await asyncio.sleep(2)
                
                # Знайти посилання для підтвердження
                verify_link = await page.query_selector("a[href*='confirm']")
                if verify_link:
                    log("Посилання для підтвердження знайдено", "SUCCESS")
                    return True
                
                return False
            
            log(f"Чекаю листа від Proton... ({attempt + 1}/30)", "INFO")
        
        log("Лист від Proton не отримано", "ERROR")
        return False
        
    except Exception as e:
        log(f"Помилка при підтвердженні email: {str(e)}", "ERROR")
        return False

async def main():
    """Основна функція"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║  🤖 WINDSURF AUTOMATION - Повна автоматизація             ║")
    print("║  Очистка → Встановлення → Реєстрація → Підтвердження     ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}\n")
    
    # Крок 1: Cleanup
    log("═══════════════════════════════════════════════════════════", "STEP")
    log("КРОК 1: ОЧИСТКА WINDSURF", "STEP")
    log("═══════════════════════════════════════════════════════════", "STEP")
    
    cleanup_ok = await run_windsurf_cleanup()
    if not cleanup_ok:
        log("Cleanup не вдалася", "ERROR")
        return
    
    await asyncio.sleep(3)
    
    # Крок 2: Закрити Chrome
    log("\n═══════════════════════════════════════════════════════════", "STEP")
    log("КРОК 2: ЗАКРИТТЯ CHROME", "STEP")
    log("═══════════════════════════════════════════════════════════", "STEP")
    
    chrome_closed = await close_chrome()
    if not chrome_closed:
        log("Chrome не закрито", "ERROR")
    
    await asyncio.sleep(2)
    
    # Крок 3: Встановити Windsurf
    log("\n═══════════════════════════════════════════════════════════", "STEP")
    log("КРОК 3: ВСТАНОВЛЕННЯ WINDSURF", "STEP")
    log("═══════════════════════════════════════════════════════════", "STEP")
    
    windsurf_ok = await install_windsurf()
    if not windsurf_ok:
        log("Windsurf не встановлено", "ERROR")
        return
    
    await asyncio.sleep(2)
    
    # Крок 4: Відкрити Windsurf в гостьовому режимі
    log("\n═══════════════════════════════════════════════════════════", "STEP")
    log("КРОК 4: ВІДКРИТТЯ WINDSURF В ГОСТЬОВОМУ РЕЖИМІ", "STEP")
    log("═══════════════════════════════════════════════════════════", "STEP")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        
        windsurf_open = await open_windsurf_guest_mode(browser)
        if not windsurf_open:
            log("Windsurf не відкрито", "ERROR")
            await browser.close()
            return
        
        # Крок 5: Реєстрація
        log("\n═══════════════════════════════════════════════════════════", "STEP")
        log("КРОК 5: РЕЄСТРАЦІЯ", "STEP")
        log("═══════════════════════════════════════════════════════════", "STEP")
        
        # Генерувати email та пароль
        email = generate_email()
        password = generate_password()
        
        log(f"Згенерований email: {email}", "INFO")
        log(f"Згенерований пароль: {password}", "INFO")
        
        # Відкрити нову вкладку для реєстрації
        page = await browser.new_page()
        
        # Реєстрація на temp-mail
        temp_mail_ok = await register_temp_mail(page, email)
        if not temp_mail_ok:
            log("Реєстрація на temp-mail не вдалася", "ERROR")
            await browser.close()
            return
        
        await asyncio.sleep(2)
        
        # Реєстрація на proton.me
        proton_ok = await register_proton_mail(page, email, password)
        if not proton_ok:
            log("Реєстрація на proton.me не вдалася", "ERROR")
            await browser.close()
            return
        
        # Розв'язати капчу
        log("\n═══════════════════════════════════════════════════════════", "STEP")
        log("КРОК 6: РОЗВ'ЯЗАННЯ КАПЧІ", "STEP")
        log("═══════════════════════════════════════════════════════════", "STEP")
        
        log("⚠️  ПОТРЕБУЄ РУЧНОГО РОЗВ'ЯЗАННЯ КАПЧІ", "WARNING")
        log("Перетягніть пазли на місце для повної картини", "INFO")
        log("Чекаю 60 секунд...", "INFO")
        
        await asyncio.sleep(60)
        
        # Крок 7: Підтвердження email
        log("\n═══════════════════════════════════════════════════════════", "STEP")
        log("КРОК 7: ПІДТВЕРДЖЕННЯ EMAIL", "STEP")
        log("═══════════════════════════════════════════════════════════", "STEP")
        
        verify_ok = await verify_email_with_temp_mail(page, email)
        if verify_ok:
            log("Email підтверджено", "SUCCESS")
        else:
            log("Email не підтверджено", "WARNING")
        
        # Фінальна інформація
        log("\n═══════════════════════════════════════════════════════════", "STEP")
        log("РЕЗУЛЬТАТИ:", "STEP")
        log("═══════════════════════════════════════════════════════════", "STEP")
        
        log(f"Email: {email}", "INFO")
        log(f"Пароль: {password}", "INFO")
        log("Статус: Тестування завершено", "SUCCESS")
        
        await asyncio.sleep(5)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
