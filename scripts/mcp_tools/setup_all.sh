#!/bin/bash

echo "🚀 Setting up all MCP servers and tools..."

# Install Node.js packages
echo "📦 Installing Node.js packages..."
npm install -g @playwright/mcp
npm install -g @iflow-mcp/applescript-mcp
# Install Model Context Protocol filesystem server (file-manager replacement)
npm install -g @modelcontextprotocol/server-filesystem@2025.8.21 || echo "⚠️  filesystem server install failed (continue)"

# Install Python packages
pip install chromadb sentence-transformers mcp-pyautogui-server

# Create tool examples directory
mkdir -p mcp_integration/core/tool_examples

# Create sample tool examples
cat > mcp_integration/core/tool_examples/browser_examples.json << 'EOF'
[
  {"tool": "browser_navigate", "description": "Navigate to URL", "category": "browser", "server": "playwright"},
  {"tool": "browser_click", "description": "Click element", "category": "browser", "server": "playwright"},
  {"tool": "browser_type", "description": "Type text", "category": "browser", "server": "playwright"},
  {"tool": "browser_screenshot", "description": "Take screenshot", "category": "browser", "server": "playwright"}
]
EOF

cat > mcp_integration/core/tool_examples/system_examples.json << 'EOF'
[
  {"tool": "run_shell", "description": "Execute shell command", "category": "system", "server": "local"},
  {"tool": "open_app", "description": "Open application", "category": "system", "server": "local"},
  {"tool": "run_applescript", "description": "Execute AppleScript", "category": "system", "server": "applescript"}
]
EOF

cat > mcp_integration/core/tool_examples/gui_examples.json << 'EOF'
[
  {"tool": "gui_click", "description": "Click GUI element", "category": "gui", "server": "pyautogui"},
  {"tool": "gui_type", "description": "Type text in GUI", "category": "gui", "server": "pyautogui"},
  {"tool": "gui_screenshot", "description": "Take GUI screenshot", "category": "gui", "server": "pyautogui"}
]
EOF

cat > mcp_integration/core/tool_examples/ai_examples.json << 'EOF'
[
  {"tool": "copilot_analyze", "description": "Analyze with Copilot LLM", "category": "ai", "server": "copilot"},
  {"tool": "openai_generate", "description": "Generate content with OpenAI", "category": "ai", "server": "openai"},
  {"tool": "gemini_query", "description": "Query Gemini LLM", "category": "ai", "server": "gemini"}
]
EOF

echo "✅ All MCP servers and tool examples are ready!"
