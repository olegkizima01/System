#!/usr/bin/env python3
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from mcp_integration.prompt_engine import prompt_engine
from mcp_integration.core.mcp_client_manager import get_mcp_client_manager

def test_prompt_engine():
    print("Testing MCP Prompt Engine Initialization...")
    if not prompt_engine.prompts_collection:
        print("❌ Prompts collection not initialized.")
        return

    print("✅ Prompt Engine Initialized.")
    
    # Test retrieval
    query = "extract patterns from text"
    print(f"\nQuerying prompts for: '{query}'")
    prompts = prompt_engine.get_relevant_prompts(query)
    
    if prompts:
        print(f"✅ Found {len(prompts)} relevant prompts.")
        for p in prompts:
            print(f"   - [{p['score']:.2f}] {p['source']}: {p['metadata'].get('pattern', 'unknown')}")
    else:
        print("⚠️ No prompts found (Did you run ingestion?).")

    # Test Integration with Client Manager (Mock)
    print("\nTesting Context Injection...")
    context = prompt_engine.construct_context(query)
    if context:
        print(f"✅ Context constructed ({len(context)} chars).")
        print("--- Context Preview ---")
        print(context[:200] + "...")
    else:
        print("⚠️ No context constructed.")

if __name__ == "__main__":
    test_prompt_engine()
