#!/usr/bin/env python3
"""
🧪 ТЕСТ: Вибір тарифу на Proton Mail
Швидкий тест для перевірки вибору безплатного тарифу
"""

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

def test_plan_selection():
    """Тестування вибору тарифу"""
    print("🚀 Запуск тесту вибору тарифу на Proton Mail")
    
    # Налаштування браузера
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # Перейти на сторінку реєстрації Proton
        print("📍 Перехід на сторінку реєстрації...")
        driver.get("https://proton.me/mail/signup")
        time.sleep(5)
        
        # Пошук радіо-кнопок
        print("\n🔍 Пошук радіо-кнопок для вибору тарифу...")
        radio_buttons = driver.find_elements(By.CSS_SELECTOR, "input[type='radio']")
        
        if radio_buttons:
            print(f"✅ Знайдено {len(radio_buttons)} радіо-кнопок")
            
            # Показати інформацію про кожну радіо-кнопку
            for i, radio in enumerate(radio_buttons):
                parent = radio.find_element(By.XPATH, "..")
                print(f"\n📌 Радіо-кнопка #{i+1}:")
                print(f"   ID: {radio.get_attribute('id')}")
                print(f"   Name: {radio.get_attribute('name')}")
                print(f"   Value: {radio.get_attribute('value')}")
                print(f"   Checked: {radio.is_selected()}")
                print(f"   Parent text: {parent.text[:100]}...")
            
            # Вибрати ПЕРШУ радіо-кнопку
            print(f"\n🎯 Вибір ПЕРШОЇ радіо-кнопки (безплатний тариф)...")
            try:
                driver.execute_script("arguments[0].scrollIntoView(true);", radio_buttons[0])
                time.sleep(1)
                radio_buttons[0].click()
                print("✅ ПЕРША радіо-кнопка вибрана!")
                time.sleep(2)
                
                # Перевірити чи вибрана
                if radio_buttons[0].is_selected():
                    print("✅ Підтверджено: ПЕРША радіо-кнопка активна")
                else:
                    print("⚠️ Попередження: ПЕРША радіо-кнопка не активна")
                    
            except Exception as e:
                print(f"❌ Помилка при виборі: {str(e)}")
                print("🔄 Спроба через JavaScript...")
                driver.execute_script("arguments[0].checked = true;", radio_buttons[0])
                driver.execute_script("arguments[0].click();", radio_buttons[0])
                print("✅ Вибрано через JavaScript")
        else:
            print("❌ Радіо-кнопки не знайдено")
            
            # Спробувати знайти картки тарифів
            print("\n🔍 Пошук карток тарифів...")
            plan_cards = driver.find_elements(By.CSS_SELECTOR, "div[class*='plan'], div[class*='card']")
            print(f"Знайдено {len(plan_cards)} карток")
            
            for i, card in enumerate(plan_cards):
                print(f"\n📌 Картка #{i+1}:")
                print(f"   Text: {card.text[:100]}...")
        
        # Чекати для спостереження
        print("\n⏳ Браузер залишиться відкритим 30 секунд для спостереження...")
        time.sleep(30)
        
    finally:
        driver.quit()
        print("\n✅ Тест завершено")

if __name__ == "__main__":
    test_plan_selection()
