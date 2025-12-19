
import os
import sys
import argparse

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


def load_env():
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    if os.path.exists(env_path):
        print(f"Loading env from {env_path}")
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip()
    else:
        print("No .env file found in project root.")

load_env()

try:
    from system_ai.tools.vision import analyze_with_copilot, load_image_png_b64
    from system_ai.tools.screenshot import take_screenshot
except ImportError as e:
    print(f"ImportError: {e}")
    print("Ensure you are running this from the project root or correct environment.")
    import sys
    sys.exit(1)

def test_vision():
    print("Taking screenshot...")
    res = take_screenshot()
    if res.get("status") != "success":
        print(f"Screenshot failed: {res}")
        return

    path = res.get("path")
    print(f"Screenshot saved to: {path}")
    
    # Check if resizing logic works (by calling the function manually)
    print("Testing image loading/resizing...")
    b64 = load_image_png_b64(path)
    if b64:
        print(f"Image loaded successfully. Base64 length: {len(b64)}")
    else:
        print("Failed to load image.")
        return

    # Check actual API call
    print("Testing analyze_with_copilot (Actual API call)...")
    # Using a simple prompt
    result = analyze_with_copilot(path, prompt="Is this a computer screen? Answer only 'Yes' or 'No'.")
    
    print("\n--- Result ---")
    print(result)
    
    if result.get("status") == "success":
        print("\nSUCCESS: Vision tool worked without 413 error.")
    else:
        if "413" in str(result):
             print("\nFAILURE: Still getting 413 error.")
        else:
             print(f"\nFAILURE: Other error: {result.get('error')}")

if __name__ == "__main__":
    test_vision()
