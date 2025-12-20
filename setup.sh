#!/bin/bash

# System Vision Full Setup Script
# This script sets up Python 3.12 environment and installs all required dependencies

echo "🚀 Starting System Vision Full Setup..."

# Check if running in the correct directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: This script must be run from the project root directory"
    exit 1
fi

# Function to check Python version
check_python_version() {
    local required_version="3.12"
    local python_cmd="python3.12"
    
    # Try to find Python 3.12
    if command -v python3.12 &> /dev/null; then
        PYTHON_CMD="python3.12"
        PYTHON_VERSION=$(python3.12 --version 2>&1 | awk '{print $2}')
        echo "✅ Found Python 3.12: $PYTHON_VERSION"
        return 0
    elif command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        echo "⚠️  Using Python $PYTHON_VERSION (Python 3.12 recommended)"
        return 0
    else
        echo "❌ Python 3 not found. Please install Python 3.12 or later."
        return 1
    fi
}

# Check Python version
if ! check_python_version; then
    exit 1
fi

# Remove existing virtual environment if it exists
if [ -d ".venv" ]; then
    echo "🔧 Removing existing virtual environment..."
    rm -rf .venv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to remove existing virtual environment"
        exit 1
    fi
fi

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

# Install PaddleOCR for OCR functionality
echo "📦 Installing PaddleOCR for OCR..."
pip install paddleocr paddlepaddle

if [ $? -ne 0 ]; then
    echo "⚠️  PaddleOCR installation failed. OCR will use fallback methods."
else
    echo "✅ PaddleOCR installed successfully"
fi

# Install super-rag for advanced vision features
echo "📦 Attempting to install super-rag for advanced vision features..."
pip install git+https://github.com/superagent-ai/super-rag.git

if [ $? -ne 0 ]; then
    echo "⚠️  super-rag repository not found or unavailable."
    echo "   The system will use OpenCV-based vision analysis."
    echo "   Advanced features will be unavailable, but core functionality works."
else
    echo "✅ super-rag installed successfully"
fi

# Install additional useful packages
echo "📦 Installing additional useful packages..."
pip install python-dotenv rich typer

# Verify all installations
echo "🔍 Verifying all installations..."

echo "--- Core Dependencies ---"

# Check OpenCV
if python -c "import cv2; print('✅ OpenCV version:', cv2.__version__)" 2>/dev/null; then
    echo "✅ OpenCV installed"
else
    echo "❌ OpenCV not installed"
    exit 1
fi

# Check PIL/Pillow
if python -c "from PIL import Image; print('✅ PIL/Pillow installed')" 2>/dev/null; then
    echo "✅ PIL/Pillow installed"
else
    echo "❌ PIL/Pillow not installed"
    exit 1
fi

# Check numpy
if python -c "import numpy as np; print('✅ NumPy version:', np.__version__)" 2>/dev/null; then
    echo "✅ NumPy installed"
else
    echo "❌ NumPy not installed"
    exit 1
fi

echo "--- Vision Dependencies ---"

# Check PaddleOCR
if python -c "import paddleocr; print('✅ PaddleOCR version:', paddleocr.__version__)" 2>/dev/null; then
    echo "✅ PaddleOCR installed"
else
    echo "⚠️  PaddleOCR not installed (fallback to Copilot OCR)"
fi

# Check super-rag
if python -c "import super_rag; print('✅ super-rag installed')" 2>/dev/null; then
    echo "✅ super-rag installed"
else
    echo "⚠️  super-rag not installed (using OpenCV fallback)"
fi

echo "--- LLM Dependencies ---"

# Check langchain
if python -c "import langchain; print('✅ LangChain version:', langchain.__version__)" 2>/dev/null; then
    echo "✅ LangChain installed"
else
    echo "❌ LangChain not installed"
    exit 1
fi

# Check langchain-core
if python -c "import langchain_core; print('✅ LangChain Core installed')" 2>/dev/null; then
    echo "✅ LangChain Core installed"
else
    echo "❌ LangChain Core not installed"
    exit 1
fi

echo "--- System Dependencies ---"

# Check python-dotenv
if python -c "import dotenv; print('✅ python-dotenv installed')" 2>/dev/null; then
    echo "✅ python-dotenv installed"
else
    echo "❌ python-dotenv not installed"
    exit 1
fi

# Check rich
if python -c "import rich; print('✅ Rich installed')" 2>/dev/null; then
    echo "✅ Rich installed"
else
    echo "⚠️  Rich not installed (optional for better UI)"
fi

# Check typer
if python -c "import typer; print('✅ Typer installed')" 2>/dev/null; then
    echo "✅ Typer installed"
else
    echo "⚠️  Typer not installed (optional for CLI)"
fi

echo ""
echo "🎉 System Vision Full Setup completed successfully!"
echo ""
echo "📋 Installation Summary:"
echo "  • Python version: $PYTHON_VERSION"
echo "  • Virtual environment: .venv (created)"
echo "  • Core dependencies: ✅ Installed"
echo "  • Vision dependencies: ✅ Installed (with fallbacks)"
echo "  • LLM dependencies: ✅ Installed"
echo "  • System dependencies: ✅ Installed"
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
echo "📝 System is ready for:"
echo "  • Vision analysis with OpenCV"
echo "  • OCR with PaddleOCR (or Copilot fallback)"
echo "  • Advanced vision with super-rag (if installed)"
echo "  • Full LLM integration"
echo "  • All agent operations (Atlas, Tetyana, Grisha)"