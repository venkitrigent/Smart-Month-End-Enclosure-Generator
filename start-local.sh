#!/bin/bash

# Quick start script for local development
# Run this to start the ADK agent locally

set -e

echo "🚀 Starting Smart Month-End Close Agent Locally"
echo ""

# Check if we're in the right directory
if [ ! -d "adk-orchestrator" ]; then
    echo "❌ Error: adk-orchestrator directory not found"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    echo "✅ uv installed"
    echo ""
fi

# Navigate to adk-orchestrator
cd adk-orchestrator

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your GCP project ID"
    echo "   Run: nano .env"
    echo "   Or: code .env"
    echo ""
    read -p "Press Enter after you've updated .env file..."
fi

# Check if gcloud is authenticated
echo "🔐 Checking Google Cloud authentication..."
if ! gcloud auth application-default print-access-token &> /dev/null; then
    echo "⚠️  Not authenticated. Running authentication..."
    gcloud auth application-default login
fi

PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    echo "⚠️  No GCP project set"
    read -p "Enter your GCP Project ID: " PROJECT_ID
    gcloud config set project $PROJECT_ID
fi

echo "✅ Using project: $PROJECT_ID"
echo ""

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable aiplatform.googleapis.com --quiet 2>/dev/null || true
echo "✅ APIs enabled"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
uv sync
echo "✅ Dependencies installed"
echo ""

# Start the server
echo "🎉 Starting ADK agent server..."
echo ""
echo "📍 Access points:"
echo "   Web UI:  http://localhost:8080/web"
echo "   API Docs: http://localhost:8080/docs"
echo "   Health:   http://localhost:8080/health"
echo ""
echo "Press CTRL+C to stop the server"
echo ""

uv run uvicorn server:app --host 0.0.0.0 --port 8080 --reload
