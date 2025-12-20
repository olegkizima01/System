import sys
import os

try:
    import pyautogui
    from PIL import Image
    import io
    import base64

    print("PyAutoGUI version:", pyautogui.__version__)
    
    # Take a screenshot
    print("Taking screenshot with PyAutoGUI...")
    # On macOS, this might require permissions
    img = pyautogui.screenshot()
    print(f"Screenshot taken. Size: {img.size}")
    
    path = os.path.expanduser("~/pyautogui_test.png")
    img.save(path)
    print(f"✅ PyAutoGUI success. Saved to {path}")

except Exception as e:
    print(f"❌ PyAutoGUI failed: {e}")
    if "Permissions" in str(e) or "accessibility" in str(e).lower():
        print("This is likely a macOS permissions issue.")
