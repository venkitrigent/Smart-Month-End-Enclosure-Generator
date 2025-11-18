#!/bin/bash

# Start Multi-Agent Month-End Close System
# This script starts all microservice agents

echo "🚀 Starting Smart Month-End Close Multi-Agent System..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Kill any existing processes on these ports
echo "🧹 Cleaning up existing processes..."
lsof -ti:8000,8001,8002,8003,8004,8005,8006 | xargs kill -9 2>/dev/null || true

# Create logs directory
mkdir -p logs

echo ""
echo "Starting agents..."
echo ""

# Start Classifier Agent (Port 8001)
echo "📋 Starting Classifier Agent on port 8001..."
cd agents/classifier
python main.py > ../../logs/classifier.log 2>&1 &
CLASSIFIER_PID=$!
cd ../..
sleep 2

# Start Extractor Agent (Port 8002)
echo "📊 Starting Extractor Agent on port 8002..."
cd agents/extractor
python main.py > ../../logs/extractor.log 2>&1 &
EXTRACTOR_PID=$!
cd ../..
sleep 2

# Start Checklist Agent (Port 8003)
echo "✅ Starting Checklist Agent on port 8003..."
cd agents/checklist
python main.py > ../../logs/checklist.log 2>&1 &
CHECKLIST_PID=$!
cd ../..
sleep 2

# Start Analytics Agent (Port 8004)
echo "📈 Starting Analytics Agent on port 8004..."
cd agents/analytics
python main.py > ../../logs/analytics.log 2>&1 &
ANALYTICS_PID=$!
cd ../..
sleep 2

# Start Chatbot Agent (Port 8005)
echo "💬 Starting Chatbot Agent on port 8005..."
cd agents/chatbot
python main.py > ../../logs/chatbot.log 2>&1 &
CHATBOT_PID=$!
cd ../..
sleep 2

# Start Report Composer Agent (Port 8006)
echo "📄 Starting Report Composer Agent on port 8006..."
cd agents/report
python main.py > ../../logs/report.log 2>&1 &
REPORT_PID=$!
cd ../..
sleep 2

# Start Orchestrator Agent (Port 8000)
echo "🎯 Starting Orchestrator Agent on port 8000..."
cd agents/orchestrator
python main.py > ../../logs/orchestrator.log 2>&1 &
ORCHESTRATOR_PID=$!
cd ../..
sleep 3

echo ""
echo "✅ All agents started successfully!"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "                    AGENT STATUS"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "🎯 Orchestrator Agent:    http://localhost:8000  (PID: $ORCHESTRATOR_PID)"
echo "📋 Classifier Agent:      http://localhost:8001  (PID: $CLASSIFIER_PID)"
echo "📊 Extractor Agent:       http://localhost:8002  (PID: $EXTRACTOR_PID)"
echo "✅ Checklist Agent:       http://localhost:8003  (PID: $CHECKLIST_PID)"
echo "📈 Analytics Agent:       http://localhost:8004  (PID: $ANALYTICS_PID)"
echo "💬 Chatbot Agent:         http://localhost:8005  (PID: $CHATBOT_PID)"
echo "📄 Report Composer Agent: http://localhost:8006  (PID: $REPORT_PID)"
echo ""
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "📝 Logs are available in the ./logs directory"
echo ""
echo "🌐 API Documentation:"
echo "   Orchestrator: http://localhost:8000/docs"
echo "   Each agent:   http://localhost:800X/docs (where X is agent port)"
echo ""
echo "🛑 To stop all agents, run: ./stop-multi-agent-system.sh"
echo ""
echo "💡 Testing the system:"
echo "   curl http://localhost:8000/health"
echo ""

# Save PIDs to file for cleanup
echo "$ORCHESTRATOR_PID $CLASSIFIER_PID $EXTRACTOR_PID $CHECKLIST_PID $ANALYTICS_PID $CHATBOT_PID $REPORT_PID" > .agent_pids

# Keep script running and show logs
echo "Press Ctrl+C to stop all agents..."
echo ""

# Trap Ctrl+C to cleanup
trap 'echo ""; echo "🛑 Stopping all agents..."; kill $ORCHESTRATOR_PID $CLASSIFIER_PID $EXTRACTOR_PID $CHECKLIST_PID $ANALYTICS_PID $CHATBOT_PID $REPORT_PID 2>/dev/null; rm -f .agent_pids; echo "✅ All agents stopped"; exit 0' INT

# Wait for all processes
wait
