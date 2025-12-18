from typing import List, Dict, Any, Optional
import json
import logging

class AdaptiveVerifier:
    """
    Handles the 'Smart Plan Optimization' and 'Dynamic Granularity' logic.
    """
    
    def __init__(self, llm):
        self.llm = llm
        self.logger = logging.getLogger("system_cli.verifier")

    def optimize_plan(self, raw_plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyzes a raw execution plan using LLM to insert 'VERIFY' steps dynamically.
        Ensures mandatory verification after critical steps.
        """
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.messages import SystemMessage, HumanMessage
        import json
        import re

        VERIFIER_PROMPT = """Ти — Grisha, агент безпеки та верифікації.
Твоє завдання: Проаналізувати план дій та ОБОВ'ЯЗКОВО вставити кроки перевірки (VERIFY) після кожного критичного кроку.

ОБОВ'ЯЗКОВІ VERIFY після:
1. Файлових операцій (create, modify, delete) — перевіри, що файл існує/змінено
2. Shell-команд (особливо rm, git, sudo) — перевіри return code та результат
3. GUI-дій (натискання кнопок, введення) — перевіри скріншот або результат
4. Код-змін (git commits, рефакторинг) — перевіри git diff та статус

Формат VERIFY кроку:
{{"type": "verify", "description": "Перевірити, що [результат дії]"}}

Вхідний план:
{plan_json}

Поверни повний оновлений JSON список кроків (оригінальні кроки + вставлені VERIFY кроки).
"""

        content = ""
        
        try:
            plan_json = json.dumps(raw_plan, ensure_ascii=False)
            prompt = ChatPromptTemplate.from_messages([
                SystemMessage(content=VERIFIER_PROMPT.format(plan_json=plan_json)),
                HumanMessage(content="Оптимізуй план, додавши ОБОВ'ЯЗКОВІ перевірки після критичних кроків.")
            ])
            
            response = self.llm.invoke(prompt.format_messages())
            content = response.content
            
            # Simple JSON cleanup
            content = content.replace("```json", "").replace("```", "").strip()
            
            # Extract JSON list [ ... ]
            import re
            match = re.search(r"\[.*\]", content, re.DOTALL)
            if match:
                content = match.group(0)
                
            optimized = json.loads(content)
            
            # Safety checks
            if not isinstance(optimized, list):
                raise ValueError("Optimized plan is not a list")
                
            # If the optimizer removed steps or returned empty (and raw wasn't), treat as failure
            if len(optimized) < len(raw_plan):
                 self.logger.warning(f"[Verifier] Optimization reduced step count ({len(raw_plan)} -> {len(optimized)}). Use raw plan fallback.")
                 raise ValueError("Optimized plan unexpectedly shorter than raw plan")

            # Fallback: if LLM didn't add verify steps, add them manually for critical steps
            enhanced = self._ensure_verify_steps(optimized)
            self.logger.debug(
                f"[Verifier] Plan optimized: {len(raw_plan)} → {len(enhanced)} steps (added {len(enhanced) - len(raw_plan)} verify steps)"
            )
            return enhanced
                
        except Exception as e:
            self.logger.warning(f"[Verifier] LLM JSON parsing/optimization error: {e}")
            self.logger.debug(f"[Verifier] Raw response: {content[:200]}...")
            # Fallback: ensure verify steps manually
            enhanced = self._ensure_verify_steps(raw_plan)
            self.logger.debug(
                f"[Verifier] Plan fallback: {len(raw_plan)} → {len(enhanced)} steps (added {len(enhanced) - len(raw_plan)} verify steps)"
            )
            return enhanced
    
    def _ensure_verify_steps(self, plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Fallback: manually ensure verify steps ONLY after high-risk actions.
        """
        # Reduced set of truly critical keywords to avoid plan bloat
        critical_keywords = [
            "create", "delete", "remove", "git", "commit", "push", "pull",
            "shell", "run", "execute", "sudo"
        ]
        
        enhanced_plan = []
        for step in plan:
            enhanced_plan.append(step)
            
            step_type = step.get("type", "execute").lower()
            description = step.get("description", "").lower()
            
            # Don't add verify if it's already a verify step or similar
            if step_type != "execute":
                continue
                
            is_critical = any(kw in description for kw in critical_keywords)
            
            # Only add verify if it's NOT already followed by one
            if is_critical and plan.index(step) + 1 < len(plan):
                next_step = plan[plan.index(step) + 1]
                if next_step.get("type") == "verify":
                    continue

            if is_critical:
                verify_step = {
                    "type": "verify",
                    "description": f"Перевірити результат: {step.get('description', 'дії')}"
                }
                enhanced_plan.append(verify_step)
        
        return enhanced_plan

    def get_diff_strategy(self, current_image_path: str, previous_image_path: str) -> float:
        """
        Calculates a 'diff score' (0.0 to 1.0) between two images to determine significant change.
        Returns 0.0 (identical) to 1.0 (completely different).
        Uses local Pillow-based optimization to save LLM tokens.
        """
        if not current_image_path or not previous_image_path:
            return 1.0 # Force check if missing images
            
        try:
            from PIL import Image, ImageChops
            import math
            import operator
            from functools import reduce

            img1 = Image.open(current_image_path).convert('RGB')
            img2 = Image.open(previous_image_path).convert('RGB')

            # Ensure same size for comparison
            if img1.size != img2.size:
                img2 = img2.resize(img1.size)

            # 1. Fast Histogram Difference
            h1 = img1.histogram()
            h2 = img2.histogram()
            
            # RMS (Root Mean Square) difference of histograms
            diff = math.sqrt(reduce(operator.add,
                map(lambda a,b: (a-b)**2, h1, h2))/len(h1))
            
            # Normalize reasonably (assuming max diff is fairly large)
            # This is a heuristic. A score > 0.05 usually means visibility changed.
            # We map it to 0-1 range roughly.
            normalized_score = min(diff / 1000.0, 1.0)
            
            return normalized_score

        except Exception as e:
            # If local diff fails, assume change (safety fallback)
            self.logger.warning(f"[Verifier] Diff calculation error: {e}")
            return 1.0 

    def replan_on_failure(self, failed_step: Dict[str, Any], context: str) -> List[Dict[str, Any]]:
        """
        Generates a high-granularity recovery plan for a failed step.
        """
        # This would invoke the LLM (Atlas) to 'zoom in' on the problem
        # For now, return a retry stub
        return [
            {"type": "diagnose", "description": f"Check why {failed_step['description']} failed"},
            {"type": "retry", "description": f"Retry {failed_step['description']} with explicit dwell time"},
            {"type": "verify", "method": "visual", "description": "Verify retry success"}
        ]
