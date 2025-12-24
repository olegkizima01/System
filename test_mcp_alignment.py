
import json
import os
import sys

# Add project root to sys.path
sys.path.append(os.getcwd())

from core.mcp_registry import MCPToolRegistry

def test_mapping():
    reg = MCPToolRegistry()
    
    # Test browser_type_text mapping
    args_type = {
        "selector": "textarea[name='q']",
        "text": "Inception movie",
        "press_enter": True
    }
    mcp_args_type = reg._adapt_browser_type(args_type)
    print("\nAdapted browser_type_text args:")
    print(json.dumps(mcp_args_type, indent=2))
    
    assert mcp_args_type["ref"] == "css=textarea[name='q']"
    assert mcp_args_type["text"] == "Inception movie"
    assert mcp_args_type["submit"] == True

    # Test browser_click_element mapping
    args_click = {
        "selector": "//button[@type='submit']"
    }
    mcp_args_click = reg._adapt_browser_click(args_click)
    print("\nAdapted browser_click_element args:")
    print(json.dumps(mcp_args_click, indent=2))
    
    assert mcp_args_click["ref"] == "xpath=//button[@type='submit']"
    assert "element" in mcp_args_click

    print("\n✅ Mapping test passed!")

if __name__ == "__main__":
    test_mapping()
