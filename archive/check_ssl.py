import requests
try:
    requests.get("https://google.com", timeout=5)
    print("✅ SSL/Requests working")
except Exception as e:
    print(f"❌ SSL Error: {e}")
