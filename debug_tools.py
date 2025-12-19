import sys
import os
import asyncio

# Add current directory to path so we can import core
sys.path.append(os.getcwd())

from core.mcp import MCPToolRegistry

def main():
    print("Initializing MCPToolRegistry...")
    registry = MCPToolRegistry()
    
    print("\nListing all registered tools:")
    # list_tools() involves async connection in background threads/loops within the ExternalMCPProvider
    # but the method itself is synchronous (waiting on futures).
    tools_list = registry.list_tools()
    print(tools_list)
    
    print("\n--- Check Complete ---")
    
    # Check for offline providers
    if "[Provider Offline]" in tools_list:
        print("WARNING: Some providers are offline!")
    else:
        print("SUCCESS: All providers seem online.")

if __name__ == "__main__":
    main()
