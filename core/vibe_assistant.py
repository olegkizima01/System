"""
Vibe CLI Assistant - Human-in-the-loop intervention system for Trinity Runtime.

This module handles communication between Trinity agents and human operators
when automatic resolution fails or critical issues are detected.
"""

from typing import Dict, Any, Optional, List
import json
import os
from datetime import datetime

class VibeCLIAssistant:
    """
    Vibe CLI Assistant handles human intervention requests from Trinity agents.
    
    Responsibilities:
    - Display pause messages to users
    - Collect user input for resolution
    - Provide context about current issues
    - Maintain intervention history
    """
    
    def __init__(self, name: str = "Doctor Vibe"):
        self.name = name
        self.intervention_history: List[Dict[str, Any]] = []
        self.current_pause_context: Optional[Dict[str, Any]] = None
    
    def handle_pause_request(self, pause_context: Dict[str, Any]) -> None:
        """
        Handle a pause request from Trinity agents.
        
        Args:
            pause_context: Context about why the pause was requested
        """
        self.current_pause_context = pause_context
        
        # Add to intervention history
        intervention_record = {
            "timestamp": datetime.now().isoformat(),
            "reason": pause_context.get("reason", "unknown"),
            "message": pause_context.get("message", ""),
            "status": "active"
        }
        self.intervention_history.append(intervention_record)
        
        # Display message to user
        self._display_pause_message(pause_context)
    
    def _display_pause_message(self, pause_context: Dict[str, Any]) -> None:
        """Display pause message to the user."""
        print("\n" + "="*60)
        print(f"🚨 {self.name}: ВИКОНАННЯ ЗАВДАННЯ ПРИПИНЕНО")
        print("="*60)
        print(f"Причина: {pause_context.get('reason', 'невідома')}")
        print(f"Повідомлення: {pause_context.get('message', 'немає повідомлення')}")
        
        if pause_context.get('suggested_action'):
            print(f"Рекомендовані дії: {pause_context.get('suggested_action')}")
        
        if pause_context.get('issues'):
            print("\n🔍 Виявлені критичні помилки:")
            for i, issue in enumerate(pause_context['issues'], 1):
                print(f"  {i}. {issue['type']} в {issue['file']}:{issue.get('line', '?')}")
                print(f"     Серйозність: {issue['severity']}")
                print(f"     Повідомлення: {issue['message'][:80]}...")
        
        print("\n💡 Doctor Vibe рекомендує:")
        print("   - Перевірте виявлені помилки")
        print("   - Виправте проблеми в коді або конфігурації")
        print("   - Переконайтеся, що всі залежності встановлено")
        print("   - Використовуйте /continue після виправлення")
        
        print("\n📝 Доступні команди:")
        print("   - /continue  - Продовжити виконання після виправлення")
        print("   - /cancel    - Скасувати поточне завдання")
        print("   - /help      - Показати додаткову інформацію")
        print("="*60 + "\n")
    
    def handle_user_command(self, command: str) -> Dict[str, Any]:
        """
        Handle user commands during pause state.
        
        Args:
            command: User input command
            
        Returns:
            Dict with action result
        """
        command = command.strip().lower()
        
        if command == "/continue":
            return self._handle_continue_command()
        elif command == "/cancel":
            return self._handle_cancel_command()
        elif command == "/help":
            return self._handle_help_command()
        else:
            return {
                "action": "invalid",
                "message": f"Невідома команда: {command}. Будь ласка, використовуйте /continue, /cancel або /help"
            }
    
    def _handle_continue_command(self) -> Dict[str, Any]:
        """Handle continue command from user."""
        if not self.current_pause_context:
            return {
                "action": "error",
                "message": "Немає активної паузи для продовження"
            }
        
        # Update intervention history
        for record in self.intervention_history:
            if record["status"] == "active":
                record["status"] = "resolved"
                record["resolved_at"] = datetime.now().isoformat()
                record["resolution"] = "user_continue"
                break
        
        # Clear current pause context
        pause_context = self.current_pause_context
        self.current_pause_context = None
        
        return {
            "action": "resume",
            "message": f"{self.name}: Продовження виконання після виправлення проблем",
            "original_context": pause_context
        }
    
    def _handle_cancel_command(self) -> Dict[str, Any]:
        """Handle cancel command from user."""
        if not self.current_pause_context:
            return {
                "action": "error",
                "message": "Немає активної паузи для скасування"
            }
        
        # Update intervention history
        for record in self.intervention_history:
            if record["status"] == "active":
                record["status"] = "cancelled"
                record["resolved_at"] = datetime.now().isoformat()
                record["resolution"] = "user_cancel"
                break
        
        # Clear current pause context
        pause_context = self.current_pause_context
        self.current_pause_context = None
        
        return {
            "action": "cancel",
            "message": f"{self.name}: Завдання скасовано користувачем",
            "original_context": pause_context
        }
    
    def _handle_help_command(self) -> Dict[str, Any]:
        """Handle help command from user."""
        help_message = f"""
📖 {self.name} - Довідка по командам:

🟢 /continue  - Продовжити виконання завдання після виправлення проблем
🔴 /cancel    - Скасувати поточне завдання
💡 /help      - Показати цю довідку

💻 Поради по виправленню помилок:
1. Перевірте виявлені критичні помилки
2. Виправте проблеми в коді або конфігурації
3. Переконайтеся, що всі залежності встановлено
4. Перевірте права доступу до файлів
5. Використовуйте /continue після виправлення

🎨 Рекомендована тема: hacker-vibe
   Використовуйте ./cli.sh --theme hacker-vibe для найкращого досвіду!
"""
        
        print(help_message)
        
        return {
            "action": "help_shown",
            "message": "Довідка показана користувачу"
        }
    
    def get_intervention_history(self) -> List[Dict[str, Any]]:
        """Get the history of interventions."""
        return self.intervention_history
    
    def get_current_pause_status(self) -> Optional[Dict[str, Any]]:
        """Get the current pause status."""
        return self.current_pause_context
    
    def clear_pause_state(self) -> None:
        """Clear the current pause state."""
        self.current_pause_context = None