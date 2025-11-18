#!/bin/bash

# Stop Multi-Agent Month-End Close System

echo "🛑 Stopping Smart Month-End Close Multi-Agent System..."
echo ""

# Read PIDs from file if it exists
if [ -f ".agent_pids" ]; then
    PIDS=$(cat .agent_pids)
    echo "Stopping agents with PIDs: $PIDS"
    kill $PIDS 2>/dev/null
    rm -f .agent_pids
fi

# Also kill by port
echo "Cleaning up processes on ports 8000-8006..."
lsof -ti:8000,8001,8002,8003,8004,8005,8006 | xargs kill -9 2>/dev/null || true

echo ""
echo "✅ All agents stopped successfully!"
echo ""
