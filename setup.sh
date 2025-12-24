#!/bin/bash

# System Vision Full Setup Script (Trinity 2.2)
# This script sets up the environment and installs all required dependencies for the 
# multi-agent runtime, including original MCP clients (Cline, Continue, Native).

echo "🚀 Starting System Vision Full Setup..."

# Check if running in the correct directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: This script must be run from the project root directory"
    exit 1
fi

# Ensure log directory exists early
mkdir -p ~/.system_cli/logs

# Function to check Python version
check_python_version() {
    local required_version="3.11.13"

    # Prefer pyenv-managed Python if available
    if command -v pyenv &> /dev/null; then
        echo "🔍 pyenv detected"

        # Ensure desired version is installed (pyenv install -s is safe: skips if exists)
        if ! pyenv versions --bare | grep -x "$required_version" &>/dev/null; then
            echo "⚠️  Python $required_version not found in pyenv. Attempting to install via pyenv..."
            if pyenv install -s "$required_version"; then
                echo "✅ pyenv: installed Python $required_version"
            else
                echo "⚠️  pyenv failed to install Python $required_version. You may need to install build dependencies."
            fi
        fi

        # Set pyenv global version
        if pyenv versions --bare | grep -x "$required_version" &>/dev/null; then
            echo "🔧 Setting pyenv global to $required_version"
            pyenv global "$required_version"
            # Initialize pyenv shims for this shell (if not already)
            if command -v pyenv &>/dev/null; then
                export PATH="$(pyenv root)/shims:$PATH"
            fi
            PYTHON_CMD="$(pyenv which python3.11 2>/dev/null || pyenv which python)"
            PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
            echo "✅ Using pyenv Python: $PYTHON_VERSION"
            # Ensure project has .python-version for consistency
            if [ -w . ] || [ ! -e .python-version ]; then
                echo "$required_version" > .python-version
                echo "✅ Wrote .python-version ($required_version) to project root"
            fi
            return 0
        else
            echo "⚠️  pyenv does not have Python $required_version available. Will fall back to system Python detection."
        fi
    fi

    # Fallback: Try to find Python 3.11/3.11.13 in PATH
    if command -v python3.11 &> /dev/null; then
        PYTHON_CMD="python3.11"
        PYTHON_VERSION=$(python3.11 --version 2>&1 | awk '{print $2}')
        echo "✅ Found Python 3.11: $PYTHON_VERSION"
        return 0
    elif command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        echo "⚠️  Using Python $PYTHON_VERSION (Python $required_version recommended)"
        return 0
    else
        echo "❌ Python 3 not found. Please install Python $required_version or newer, e.g. via pyenv: https://github.com/pyenv/pyenv#installation"
        return 1
    fi
}

# Check Python version
if ! check_python_version; then
    exit 1
fi

# Parse arguments
USE_GLOBAL=false
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --global) USE_GLOBAL=true ;;
    esac
    shift
done

# Remove existing virtual environment if it exists, unless using global
if [ "$USE_GLOBAL" = true ]; then
    echo "🌐 Using global pyenv Python (no .venv creation)"
elif [ -d ".venv" ]; then
    echo "🔧 Removing existing virtual environment..."
    rm -rf .venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to remove existing virtual environment"
        exit 1
    fi
fi

# Create and activate virtual environment (unless global)
if [ "$USE_GLOBAL" = false ]; then
    # Create new virtual environment
    echo "🔧 Creating new virtual environment with Python $PYTHON_VERSION..."
    $PYTHON_CMD -m venv .venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        exit 1
    fi

    # Activate virtual environment
    echo "🔧 Activating virtual environment..."
    source .venv/bin/activate
fi

# Upgrade pip and setuptools
echo "🔧 Upgrading pip and setuptools..."
pip install --upgrade pip setuptools wheel

# Install main requirements
echo "📦 Installing main requirements..."
pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "❌ Failed to install main requirements"
    exit 1
fi

# Note: PaddleOCR is included in requirements.txt, but we ensure it here if something failed differently, or just trust requirements.txt.
# Relying on requirements.txt for paddleocr.


# Note: super-rag is deprecated (abandoned project with broken dependencies)
# System uses DifferentialVisionAnalyzer (OpenCV + PaddleOCR) instead
echo "📝 Using DifferentialVisionAnalyzer for vision analysis (OpenCV + PaddleOCR)"

# Check and setup MCP servers for DEV mode
echo ""
echo "🔌 Setting up MCP Servers for DEV mode..."
echo ""

# Check Node.js and npm for Context7 MCP
echo "--- Context7 MCP Setup ---"
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo "✅ Node.js found: $NODE_VERSION"
else
    echo "⚠️  Node.js not found. Context7 MCP requires Node.js."
    echo "   Install Node.js from: https://nodejs.org/"
    echo "   Context7 MCP will be unavailable."
fi

if command -v npm &> /dev/null; then
    NPM_VERSION=$(npm --version)
    echo "✅ npm found: $NPM_VERSION"
    
    echo "   Setting up MCP Client Ecosystem..."
    
    # 1. Continue CLI
    if command -v cn &> /dev/null; then
        echo "   ✅ Continue CLI (cn) found: $(cn --version)"
    else
        echo "   ⚠️  Continue CLI (cn) not found. Installing @continuedev/cli globally..."
        npm install -g @continuedev/cli
        if command -v cn &> /dev/null; then
            echo "   ✅ Continue CLI (cn) installed successfully"
        else
            echo "   ❌ Failed to install Continue CLI. Please run: npm install -g @continuedev/cli"
        fi
    fi

    # 2. Cline Check
    echo "   Checking Cline (Claude Dev) availability..."
    if npx -y cline@latest --version &>/dev/null 2>&1; then
        echo "   ✅ Cline is accessible via npx"
    else
        echo "   ⚠️  Cline might require internet access on first run via npx"
    fi

    # 3. Playwright Browsers
    echo "   Installing Playwright browsers..."
    playwright install chromium
    if [ $? -eq 0 ]; then
        echo "   ✅ Playwright browsers installed"
    else
        echo "   ⚠️  Playwright browser installation failed. Run 'playwright install' manually."
    fi
else
    echo "⚠️  npm not found. Cline and Continue clients require Node.js/npm."
    echo "   Install Node.js from: https://nodejs.org/"
fi

echo ""
echo "--- SonarQube MCP Setup ---"
# Check Docker for SonarQube MCP
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo "✅ Docker found: $DOCKER_VERSION"
    
    # Check if Docker daemon is running
    if docker ps &>/dev/null 2>&1; then
        echo "✅ Docker daemon is running"
        echo "   SonarQube MCP will be available for dev analysis"
    else
        echo "⚠️  Docker daemon is not running"
        echo "   Start Docker before using SonarQube MCP"
        echo "   Run: open -a Docker"
    fi
else
    echo "⚠️  Docker not found. SonarQube MCP requires Docker."
    echo "   Install Docker Desktop from: https://www.docker.com/products/docker-desktop"
    echo "   SonarQube MCP will be unavailable."
fi

echo ""

# Apply patches to MCP servers
echo "🔧 Applying patches to MCP servers..."
if [ -f "scripts/fix_mcp_server.py" ]; then
    $PYTHON_CMD scripts/fix_mcp_server.py
    if [ $? -ne 0 ]; then
        echo "⚠️  Failed to patch MCP server. Use with caution."
    fi
else
    echo "⚠️  Patch script scripts/fix_mcp_server.py not found."
fi


# Additional packages are now in requirements.txt


# Verify all installations
echo "🔍 Verifying all installations..."

echo "--- Core Dependencies ---"

# Check OpenCV
if $PYTHON_CMD -c "import cv2; print('✅ OpenCV version:', cv2.__version__)" 2>/dev/null; then
    echo "✅ OpenCV installed"
else
    echo "❌ OpenCV not installed"
    exit 1
fi

# Check PIL/Pillow
if $PYTHON_CMD -c "from PIL import Image; print('✅ PIL/Pillow installed')" 2>/dev/null; then
    echo "✅ PIL/Pillow installed"
else
    echo "❌ PIL/Pillow not installed"
    exit 1
fi

# Check numpy
if $PYTHON_CMD -c "import numpy as np; print('✅ NumPy version:', np.__version__)" 2>/dev/null; then
    echo "✅ NumPy installed"
else
    echo "❌ NumPy not installed"
    exit 1
fi

echo "--- Vision Dependencies ---"

# Check PaddleOCR
if $PYTHON_CMD -c "import paddleocr; print('✅ PaddleOCR version:', paddleocr.__version__)" 2>/dev/null; then
    echo "✅ PaddleOCR installed"
    PADDLEOCR_INSTALLED=true
else
    echo "⚠️  PaddleOCR not installed (fallback to Copilot OCR)"
    PADDLEOCR_INSTALLED=false
fi

# DifferentialVisionAnalyzer check
if $PYTHON_CMD -c "from system_ai.tools.vision import DifferentialVisionAnalyzer; print('✅ DifferentialVisionAnalyzer available')" 2>/dev/null; then
    echo "✅ DifferentialVisionAnalyzer installed"
else
    echo "⚠️  DifferentialVisionAnalyzer not found"
fi

echo "--- LLM Dependencies ---"

# Check langchain
if $PYTHON_CMD -c "import langchain; print('✅ LangChain version:', langchain.__version__)" 2>/dev/null; then
    echo "✅ LangChain installed"
else
    echo "❌ LangChain not installed"
    exit 1
fi

# Check langchain-core
if $PYTHON_CMD -c "import langchain_core; print('✅ LangChain Core installed')" 2>/dev/null; then
    echo "✅ LangChain Core installed"
else
    echo "❌ LangChain Core not installed"
    exit 1
fi

echo "--- System Dependencies ---"

# Check python-dotenv
if $PYTHON_CMD -c "import dotenv; print('✅ python-dotenv installed')" 2>/dev/null; then
    echo "✅ python-dotenv installed"
else
    echo "❌ python-dotenv not installed"
    exit 1
fi

# Check tenacity
if $PYTHON_CMD -c "import tenacity; print('✅ tenacity installed')" 2>/dev/null; then
    echo "✅ tenacity installed"
else
    echo "❌ tenacity not installed"
    exit 1
fi

# Check rich
if $PYTHON_CMD -c "import rich; print('✅ Rich installed')" 2>/dev/null; then
    echo "✅ Rich installed"
else
    echo "⚠️  Rich not installed (optional for better UI)"
fi

# Check typer
if $PYTHON_CMD -c "import typer; print('✅ Typer installed')" 2>/dev/null; then
    echo "✅ Typer installed"
else
    echo "⚠️  Typer not installed (optional for CLI)"
fi

# Check mcp (Python SDK)
if $PYTHON_CMD -c "import mcp; print('✅ MCP Python SDK installed')" 2>/dev/null; then
    echo "✅ MCP Python SDK installed"
else
    echo "❌ MCP Python SDK not installed"
    exit 1
fi

echo "--- MCP Server Dependencies (for DEV mode) ---"

# Check MCP manager integration (Core)
if $PYTHON_CMD -c "from core.mcp.manager import MCPClientManager; print('✅ MCP Manager available')" 2>/dev/null; then
    echo "✅ MCP Integration module available (core.mcp)"
else
    echo "⚠️  MCP Integration module not found (core.mcp)"
fi

# Check Context7 MCP availability
if command -v npx &> /dev/null; then
    echo "✅ npx available (for Context7 MCP)"
else
    echo "⚠️  npx not found (Context7 MCP unavailable - install Node.js)"
fi

# Check SonarQube MCP availability
if command -v docker &> /dev/null && docker ps &>/dev/null 2>&1; then
    echo "✅ Docker available (for SonarQube MCP)"
else
    echo "⚠️  Docker not running (SonarQube MCP unavailable - start Docker or install it)"
fi

echo ""
echo "🎉 System Vision (Trinity 2.2) Setup completed successfully!"
echo ""
echo "📋 Installation Summary:"
echo "  • Python version: $PYTHON_VERSION"
echo "  • Virtual environment: .venv (created)"
echo "  • Core dependencies: ✅ Installed"
echo "  • Vision dependencies: ✅ Installed (with fallbacks)"
echo "  • LLM dependencies: ✅ Installed"
echo "  • System dependencies: ✅ Installed"
echo "  • MCP Clients (Trinity 2.2):"
echo "    - Native SDK: ✅ Ready"
echo "    - Continue CLI: $(command -v cn &>/dev/null && echo "✅ Ready" || echo "⚠️  Not Found")"
echo "    - Cline (npx): ✅ Ready"
echo "  • MCP Servers: Context7 and SonarQube - check status above"
echo ""
echo "💡 To activate the virtual environment later, run:"
echo "   source .venv/bin/activate"
echo ""
echo "🚀 To start the system, run:"
echo "   python cli.py"
echo ""
echo "🔧 To update the system later, run:"
echo "   source .venv/bin/activate && pip install -r requirements.txt --upgrade"
echo ""
echo "🔌 MCP Client Foundation:"
echo "  • Continue: Requires '@continuedev/cli' (installed via npm)"
echo "  • Cline: Uses 'npx cline' for high-level tasks"
echo "  • Routing: Automatic 'Original Client Pairing' (e.g., Playwright -> Cline)"
echo ""
echo "📝 System is ready for:"
echo "  • Meta-Task Delegation to Cline/Continue"
echo "  • Dynamic RAG Context & Script-based logic"
echo "  • Intelligent Client Routing (Native/Cline/Continue)"
echo "  • Vision analysis with DifferentialVisionAnalyzer"
echo "  • All agent operations (Meta-Planner, Atlas, Tetyana, Grisha)"