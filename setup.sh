#!/bin/bash

# Atlas Setup Script
# Version: 2.5.0
# Description: Sets up the global environment for Atlas/Trinity Runtime.

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Atlas Setup (Trinity 2.5) ===${NC}"

# Check for Python 3.11+
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 is not installed.${NC}"
    exit 1
fi

# Check for Node.js and NPM
if ! command -v npm &> /dev/null; then
    echo -e "${RED}Error: npm is not installed. Please install Node.js.${NC}"
    exit 1
fi

# Check for uv (Python package manager)
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}Installing uv (fast python package installer)...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source "$HOME/.cargo/env" || true
fi

echo -e "${GREEN}✓ System dependencies checked${NC}"

# 1. Global MCP Tools Installation
echo -e "${BLUE}--- Installing Global MCP Servers ---${NC}"

# Playwright
if ! npm list -g @modelcontextprotocol/server-playwright &> /dev/null; then
    echo -e "Installing Playwright Server..."
    npm install -g @modelcontextprotocol/server-playwright
else
    echo -e "${GREEN}✓ Playwright Server installed${NC}"
fi

# Filesystem
if ! npm list -g @modelcontextprotocol/server-filesystem &> /dev/null; then
    echo -e "Installing Filesystem Server..."
    npm install -g @modelcontextprotocol/server-filesystem
else
    echo -e "${GREEN}✓ Filesystem Server installed${NC}"
fi

# Context7 - Assuming it's an mcp package or handled via uvx dynamically, 
# but if there's a global package, install it.
# If context7 is strictly uvx, we skip global npm install for it.

# 2. Python Environment Setup
echo -e "${BLUE}--- Setting up Python Environment ---${NC}"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv .venv --python 3.11
else
    echo "Virtual environment exists."
fi

echo "Installing Python dependencies..."
# Use uv pip install directly into the environment
uv pip install -r requirements.txt

# 3. Validation
echo -e "${BLUE}--- Validating Setup ---${NC}"

source .venv/bin/activate
# Check imports
python3 -c "import pydantic; import yaml; print('✓ Pydantic & PyYAML available')"

echo -e "${BLUE}=== Setup Complete ===${NC}"
echo -e "Run: ${GREEN}./cli.sh${NC} to start Atlas."