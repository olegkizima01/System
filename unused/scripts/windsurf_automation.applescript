#!/usr/bin/osascript

-- 🤖 WINDSURF EMAIL AUTOMATION - Apple Script для macOS
-- Повна автоматизація реєстрації на Proton Mail

-- Генерація випадкових даних
set firstName to (choose from list {"Alex", "James", "Michael", "David", "Robert", "John", "Emma", "Olivia", "Sophia", "Benjamin", "Lucas", "Henry"} with prompt "Виберіть ім'я:" default items {"Alex"})
set firstName to item 1 of firstName

set lastName to (choose from list {"Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Martinez", "Wilson", "Anderson", "Thomas"} with prompt "Виберіть прізвище:" default items {"Smith"})
set lastName to item 1 of lastName

-- Створення email
set protonEmail to (firstName & "." & lastName) as string
set protonEmail to do shell script "echo " & quoted form of protonEmail & " | tr '[:upper:]' '[:lower:]'"
set protonEmail to protonEmail & "@proton.me"

set tempEmail to (firstName & lastName) as string
set tempEmail to do shell script "echo " & quoted form of tempEmail & " | tr '[:upper:]' '[:lower:]'"
set tempEmail to tempEmail & "@temp-mail.org"

set userPassword to "Qwas@000"

-- Показати згенеровані дані
display dialog "Згенеровані дані:" & return & return & "Ім'я: " & firstName & return & "Прізвище: " & lastName & return & "Email Proton: " & protonEmail & return & "Email Temp-mail: " & tempEmail & return & "Пароль: " & userPassword buttons {"Продовжити", "Скасувати"} default button "Продовжити"

-- КРОК 1: Відкрити Safari з temp-mail
display notification "Відкриття temp-mail у Safari..." with title "Windsurf Automation"

tell application "Safari"
	activate
	open location "https://temp-mail.org/?email=" & tempEmail
	delay 3
end tell

display notification "Safari відкрито з temp-mail" with title "Windsurf Automation"

-- КРОК 2: Відкрити Chrome з Proton Mail
display notification "Відкриття Proton Mail у Chrome..." with title "Windsurf Automation"

tell application "Google Chrome"
	activate
	open location "https://proton.me/mail"
	delay 5
end tell

-- КРОК 3: Натиснути "Create a free account"
display notification "Шукаю кнопку 'Create a free account'..." with title "Windsurf Automation"
delay 3

tell application "Google Chrome"
	activate
	-- Виконати JavaScript для натискання кнопки
	tell active tab of window 1
		execute javascript "
			var buttons = document.querySelectorAll('a, button');
			for (var i = 0; i < buttons.length; i++) {
				if (buttons[i].textContent.includes('Create a free account') || 
				    buttons[i].textContent.includes('Create Account')) {
					buttons[i].click();
					break;
				}
			}
		"
	end tell
	delay 5
end tell

display notification "Кнопка натиснута. Заповнення форми..." with title "Windsurf Automation"

-- КРОК 4: Заповнити форму
tell application "Google Chrome"
	activate
	delay 2
	
	tell active tab of window 1
		-- Заповнити email
		execute javascript "
			var emailInput = document.querySelector('input[type=\"email\"]');
			if (emailInput) {
				emailInput.value = '" & protonEmail & "';
				emailInput.dispatchEvent(new Event('input', { bubbles: true }));
				emailInput.dispatchEvent(new Event('change', { bubbles: true }));
			}
		"
		delay 1
		
		-- Заповнити пароль
		execute javascript "
			var passwordInputs = document.querySelectorAll('input[type=\"password\"]');
			if (passwordInputs.length > 0) {
				passwordInputs[0].value = '" & userPassword & "';
				passwordInputs[0].dispatchEvent(new Event('input', { bubbles: true }));
				passwordInputs[0].dispatchEvent(new Event('change', { bubbles: true }));
			}
			if (passwordInputs.length > 1) {
				passwordInputs[1].value = '" & userPassword & "';
				passwordInputs[1].dispatchEvent(new Event('input', { bubbles: true }));
				passwordInputs[1].dispatchEvent(new Event('change', { bubbles: true }));
			}
		"
		delay 1
		
		-- Натиснути кнопку submit
		execute javascript "
			var buttons = document.querySelectorAll('button');
			for (var i = 0; i < buttons.length; i++) {
				var text = buttons[i].textContent.toLowerCase();
				if (text.includes('почніть') || 
				    text.includes('create') || 
				    text.includes('next') || 
				    text.includes('continue')) {
					buttons[i].click();
					break;
				}
			}
		"
	end tell
end tell

display notification "Форма заповнена. Очікування капчі..." with title "Windsurf Automation"

-- КРОК 5: Повідомлення про капчу
delay 5
display dialog "Розв'яжіть капчу вручну (виберіть квадрати)" & return & return & "Натисніть OK після розв'язання капчи" buttons {"OK"} default button "OK"

-- КРОК 6: Вибір безплатного тарифу
display notification "Вибір безплатного тарифу..." with title "Windsurf Automation"
delay 3

tell application "Google Chrome"
	activate
	tell active tab of window 1
		execute javascript "
			var buttons = document.querySelectorAll('button');
			for (var i = 0; i < buttons.length; i++) {
				var text = buttons[i].textContent.toLowerCase();
				if (text.includes('free') && (text.includes('0') || text.includes('безкошт'))) {
					buttons[i].click();
					break;
				}
			}
		"
	end tell
end tell

delay 3

-- ФІНАЛЬНА ІНФОРМАЦІЯ
display dialog "Автоматизація завершена!" & return & return & "Ім'я: " & firstName & return & "Прізвище: " & lastName & return & "Email Proton: " & protonEmail & return & "Email Temp-mail: " & tempEmail & return & "Пароль: " & userPassword & return & return & "Safari: перевіряйте листи від Proton" & return & "Chrome: завершіть реєстрацію" buttons {"OK"} default button "OK"

display notification "Автоматизація завершена!" with title "Windsurf Automation"
