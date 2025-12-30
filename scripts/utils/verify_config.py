from core.config import settings
import sys

try:
    print(f"Loading settings...")
    print(f"App: {settings.app_name}")
    print(f"Logging Level: {settings.logging.level}")
    print(f"MCP Mode: {settings.mcp.mode}")
    print(f"Playwright Enabled: {settings.mcp.servers['playwright'].enabled}")
    print("✅ Configuration loaded successfully")
except Exception as e:
    print(f"❌ Verification failed: {e}")
    sys.exit(1)
