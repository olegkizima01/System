import sys
import os
import asyncio

# Add current directory to path so we can import core
sys.path.append(os.getcwd())

from core.mcp import MCPToolRegistry

def main():
    print("Initializing MCPToolRegistry...")
    registry = MCPToolRegistry()
    
    print("\nGetting ALL tool definitions (Local + External)...")
    try:
        defs = registry.get_all_tool_definitions()
        print(f"Total tools found: {len(defs)}")
        
        external_found = False
        for d in defs:
            name = d['name']
            if name.startswith("playwright.") or name.startswith("pyautogui."):
                print(f"✅ Found external tool: {name}")
                external_found = True
        
        if external_found:
            print("\nSUCCESS: External tools are now correctly exposed for binding!")
        else:
            print("\nFAILURE: No external tools found in definitions.")
            
    except Exception as e:
        print(f"\nERROR: {e}")

if __name__ == "__main__":
    main()
