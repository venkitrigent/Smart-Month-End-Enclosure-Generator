#!/bin/bash

# Script to check virtual environment setup

echo "🔍 Checking Virtual Environment Setup"
echo ""

cd adk-orchestrator

# Check if .venv exists
if [ -d ".venv" ]; then
    echo "✅ Virtual environment exists at: $(pwd)/.venv"
    echo ""
    
    # Show Python version in venv
    echo "🐍 Python version in venv:"
    .venv/bin/python --version
    echo ""
    
    # Show installed packages
    echo "📦 Installed packages (first 10):"
    .venv/bin/pip list | head -n 12
    echo ""
    
    # Show venv activation command
    echo "💡 To manually activate this venv:"
    echo "   source adk-orchestrator/.venv/bin/activate"
    echo ""
    echo "💡 To deactivate:"
    echo "   deactivate"
    
else
    echo "❌ Virtual environment not found"
    echo "Run 'cd adk-orchestrator && uv sync' to create it"
fi
