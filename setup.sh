#!/bin/bash

# System Vision Full Setup Script (Trinity 2.2)
# Refactored for Clean Installation and Robust Environment Setup

set -e  # Exit immediately if a command exits with a non-zero status

echo "🚀 Starting System Vision Clean Setup..."

# Directory Check
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: This script must be run from the project root directory"
    exit 1
fi

# Configuration
REQUIRED_PYTHON="3.11.13"
VENV_DIR=".venv"

# Function: Clean Environment
clean_environment() {
    echo "🧹 Cleaning previous environment..."
    if [ -d "$VENV_DIR" ]; then
        echo "   Removing existing virtual environment ($VENV_DIR)..."
        rm -rf "$VENV_DIR"
    fi
    echo "   Removing cached files..."
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
}

# Function: Install/Verify Python
setup_python() {
    echo "🐍 Checking Python version..."
    
    if command -v pyenv &> /dev/null; then
        echo "   pyenv detected."
        if ! pyenv versions --bare | grep -x "$REQUIRED_PYTHON" &>/dev/null; then
            echo "   ⚠️  Python $REQUIRED_PYTHON not found in pyenv. Installing..."
            pyenv install "$REQUIRED_PYTHON"
        else
            echo "   ✅ Python $REQUIRED_PYTHON is available in pyenv."
        fi
        
        # Set local version
        pyenv local "$REQUIRED_PYTHON"
        echo "   ✅ Set local python version to $REQUIRED_PYTHON"
        
        PYTHON_CMD=$(pyenv which python)
    else
        echo "⚠️  pyenv not found. Checking system python..."
        if command -v python3.11 &> /dev/null; then
            PYTHON_CMD="python3.11"
        elif command -v python3 &> /dev/null; then
            # Check version
            VER=$(python3 --version 2>&1 | awk '{print $2}')
            if [[ "$VER" == "3.11"* ]]; then
                 PYTHON_CMD="python3"
            else
                 echo "❌ Python 3.11 is required. Found $VER. Please install Python 3.11 or pyenv."
                 exit 1
            fi
        else
             echo "❌ Python 3 not found."
             exit 1
        fi
    fi
    echo "   Using Python executable: $PYTHON_CMD"
}

# Function: Create Virtual Environment
create_venv() {
    echo "📦 Creating virtual environment..."
    "$PYTHON_CMD" -m venv "$VENV_DIR"
    
    # Analyze Activation for Installation
    source "$VENV_DIR/bin/activate"
    
    echo "   Upgrading pip, setuptools, and wheel..."
    pip install --upgrade pip setuptools wheel
}

# Function: Install Dependencies
install_dependencies() {
    echo "📥 Installing python dependencies..."
    pip install -r requirements.txt
    
    echo "   Verifying core installations..."
    python -c "import cv2; print('   ✅ OpenCV:', cv2.__version__)"
    # mcp SDK verification
    if python -c "import mcp" 2>/dev/null; then
        echo "   ✅ MCP SDK installed"
    else
        echo "   ❌ MCP SDK not found"
        exit 1
    fi
    python -c "import langchain; print('   ✅ LangChain:', langchain.__version__)"
}

# Function: Setup MCP (Node.js)
setup_mcp_servers() {
    echo "🔌 Setting up MCP Servers..."
    
    if command -v npm &> /dev/null; then
        echo "   ✅ npm found. Setting up client tools..."
        
        # Continue CLI
        if ! command -v cn &> /dev/null; then
            echo "   Installing @continuedev/cli globally (required for permissions)..."
            npm install -g @continuedev/cli
        else
            echo "   ✅ Continue CLI found."
        fi

        echo "   Installing MCP Servers globally..."
        npm install -g @upstash/context7-mcp @upstash/context7-docs-mcp @playwright/mcp @iflow-mcp/applescript-mcp @modelcontextprotocol/server-filesystem
        
        # Playwright
        echo "   Installing Playwright browsers..."
        npx playwright install chromium
    else
        echo "⚠️  npm not found. Node.js based MCP servers will not be available."
    fi
}

# Main Execution Flow
clean_environment
setup_python
create_venv
install_dependencies
setup_mcp_servers

echo ""
echo "🎉 Setup Complete!"
echo "   Virtual Environment created at: $VENV_DIR"
echo "   Entry point: ./cli.sh"
echo ""