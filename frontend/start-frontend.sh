#!/bin/bash

# Start Streamlit Frontend for Smart Month-End Close

echo "🚀 Starting Streamlit Frontend..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Creating from .env.example..."
    cp .env.example .env
    echo "✅ Created .env file. Please update with your configuration."
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Start Streamlit
echo ""
echo "✅ Starting Streamlit on http://localhost:8501"
echo "📊 Smart Month-End Enclosure Generator"
echo ""
echo "Press Ctrl+C to stop"
echo ""

streamlit run app.py --server.port 8501 --server.address 0.0.0.0
