#!/usr/bin/env python3
"""
Test script for MCP integration
"""

def test_function():
    """Test function with potential issues"""
    result = 0
    for i in range(10):
        result += i
    return result

def complex_function():
    """Complex function for testing"""
    data = {"key": "value"}
    return data

if __name__ == "__main__":
    print("Test script executed")
    print(f"Result: {test_function()}")
