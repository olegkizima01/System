import sys
import os
import re

# Add project root to sys.path
sys.path.append(os.getcwd())

from core.constants import SUCCESS_MARKERS, FAILURE_MARKERS, NEGATION_PATTERNS

def test_negation_logic():
    print("🧪 Testing Negation Logic...")
    
    # Mocking the logic from trinity.py
    def check_verdict(content, lang="en"):
        lower_content = content.lower()
        has_explicit_fail = any(f"[{m}]" in lower_content or m in lower_content for m in FAILURE_MARKERS)
        has_explicit_complete = any(f"[{m}]" in lower_content or m in lower_content for m in SUCCESS_MARKERS)
        
        if has_explicit_fail:
            return "failed"
            
        if has_explicit_complete:
            is_negated = False
            lang_negations = NEGATION_PATTERNS.get(lang, NEGATION_PATTERNS["en"])
            
            for kw in SUCCESS_MARKERS:
                if kw in lower_content:
                    for match in re.finditer(re.escape(kw), lower_content):
                        idx = match.start()
                        pre_text = lower_content[max(0, idx-25):idx]
                        if re.search(lang_negations, pre_text):
                            is_negated = True
                            break
                if is_negated: break
            
            return "success" if not is_negated else "failed"
            
        return "uncertain"

    test_cases = [
        # English
        ("The task is [VERIFIED]", "en", "success"),
        ("The task is NOT [VERIFIED]", "en", "failed"),
        ("I was unable to reach the [SUCCESS] state", "en", "failed"),
        ("The goal is [FAILED]", "en", "failed"),
        
        # Ukrainian
        ("Завдання [ВИКОНАНО]", "uk", "success"),
        ("Завдання НЕ [ВИКОНАНО]", "uk", "failed"),
        ("На жаль, робота не [ГОТОВА]", "uk", "failed"),
        ("Сталася [ПОМИЛКА]", "uk", "failed"),
        
        # Edge cases
        ("It is done, but not quite [VERIFIED] yet", "en", "failed"),
        ("I [CONFIRMED] that it failed", "en", "failed"), # [CONFIRMED] is success marker, but if it has negation before...
    ]
    
    passed = 0
    for content, lang, expected in test_cases:
        actual = check_verdict(content, lang)
        if actual == expected:
            print(f"✅ PASSED: '{content}' ({lang}) -> {actual}")
            passed += 1
        else:
            print(f"❌ FAILED: '{content}' ({lang}) -> Expected {expected}, got {actual}")
            
    print(f"\n📊 Result: {passed}/{len(test_cases)} passed.")
    return passed == len(test_cases)

if __name__ == "__main__":
    test_negation_logic()
