from typing import Any, Dict, Optional, List
import os
import threading
from datetime import datetime
from core.self_healing import IssueSeverity
from core.trinity.state import TrinityState
from core.constants import MESSAGES

class TrinitySelfHealingMixin:
    """Mixin for TrinityRuntime containing self-healing integration logic."""

    def _initialize_self_healing(self) -> None:
        """Initialize the self-healing module."""
        try:
            from core.self_healing import CodeSelfHealer
            self.self_healer = CodeSelfHealer(on_stream=getattr(self, 'on_stream', None))
            self.self_healer.integrate_with_trinity(self)
            
            # Start background monitoring
            self.self_healing_thread = self.self_healer.start_background_monitoring(interval=60.0)
            
            # Connect Vibe Assistant to Self-Healer for auto-repair
            if hasattr(self, 'vibe_assistant'):
                self.vibe_assistant.set_self_healer(
                    self.self_healer,
                    on_repair_complete=self._on_auto_repair_complete
                )
            
            if hasattr(self, 'verbose') and self.verbose:
                self.logger.info("Self-healing module initialized and monitoring started")
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f"Failed to initialize self-healing: {e}")
            self.self_healing_enabled = False
    
    def _on_auto_repair_complete(self, result: dict) -> None:
        """Callback when Doctor Vibe auto-repair completes."""
        if result.get("success"):
            if hasattr(self, 'logger'):
                self.logger.info(f"Auto-repair successful: {result.get('repairs_successful', 0)} fixes applied")
        else:
            if hasattr(self, 'logger'):
                self.logger.warning(f"Auto-repair failed: {result.get('message', 'unknown')}")

    def get_self_healing_status(self) -> Optional[Dict[str, Any]]:
        """Get the current status of the self-healing module."""
        if not getattr(self, 'self_healing_enabled', False) or not getattr(self, 'self_healer', None):
            return None
        return self.self_healer.get_status()
    
    def trigger_self_healing_scan(self) -> Optional[List[Dict[str, Any]]]:
        """Trigger an immediate scan for issues."""
        if not getattr(self, 'self_healing_enabled', False) or not getattr(self, 'self_healer', None):
            return None
        issues = self.self_healer.trigger_immediate_scan()
        return [issue.to_dict() for issue in issues]

    def _check_critical_issues(self) -> Optional[Dict[str, Any]]:
        self_healing_enabled = getattr(self, 'self_healing_enabled', False)
        self_healer = getattr(self, 'self_healer', None)
        if not (self_healing_enabled and self_healer):
            return None
        issues = self_healer.detected_issues
        critical = [i for i in issues if i.severity in {IssueSeverity.CRITICAL, IssueSeverity.HIGH}]
        if not critical:
            return None
            
        return {
            "reason": "critical_issues_detected",
            "issues": [i.to_dict() for i in critical[:5]],
            "message": f"Doctor Vibe: Виявлено {len(critical)} критичних помилок. Атлас призупинив виконання.",
            "timestamp": datetime.now().isoformat(),
            "suggested_action": "Будь ласка, виправте помилки. Атлас автоматично продовжить після /continue",
            "atlas_status": "paused_waiting_for_human",
            "auto_resume_available": True
        }

    def _check_background_dev_mode(self, state: TrinityState) -> Optional[Dict[str, Any]]:
        if state.get("task_type") != "DEV" or not state.get("is_dev"):
            return None
        self_healing_enabled = getattr(self, 'self_healing_enabled', False)
        self_healer = getattr(self, 'self_healer', None)
        if not (self_healing_enabled and self_healer):
            return None
        unresolved = [i for i in self.self_healer.detected_issues if i.severity in {IssueSeverity.MEDIUM, IssueSeverity.HIGH}]
        if len(unresolved) <= 2:
            return None
            
        lang = getattr(self, 'preferred_language', 'en')
        lang = lang if lang in MESSAGES else "en"
        return {
            "reason": "background_error_correction_needed",
            "issues": [i.to_dict() for i in unresolved[:3]],
            "message": f"Doctor Vibe: Detected {len(unresolved)} background errors." if lang != "uk" else f"Doctor Vibe: Виявлено {len(unresolved)} помилок в фоновому режимі.",
            "timestamp": datetime.now().isoformat(),
            "suggested_action": "Errors fixed automatically." if lang != "uk" else "Помилки виправляються автоматично.",
            "atlas_status": "running_with_background_fixes",
            "auto_resume_available": False,
            "background_mode": True
        }
