#!/bin/bash

# Stop No-Hitter Forecaster Production Services
echo "Stopping No-Hitter Forecaster services..."

# Stop scheduler if running
if [ -f logs/scheduler.pid ]; then
    SCHEDULER_PID=$(cat logs/scheduler.pid)
    echo "Stopping scheduler (PID: $SCHEDULER_PID)..."
    kill -9 $SCHEDULER_PID 2>/dev/null
    rm -f logs/scheduler.pid
    echo "✅ Scheduler stopped"
else
    echo "⚠️ Scheduler PID file not found"
fi

# Stop web app if running
if [ -f logs/webapp.pid ]; then
    WEBAPP_PID=$(cat logs/webapp.pid)
    echo "Stopping web app (PID: $WEBAPP_PID)..."
    kill -9 $WEBAPP_PID 2>/dev/null
    rm -f logs/webapp.pid
    echo "✅ Web app stopped"
else
    echo "⚠️ Web app PID file not found"
fi

# Also kill any remaining processes
echo "Cleaning up any remaining processes..."
pkill -f "main.py web" 2>/dev/null
pkill -f "main.py scheduler" 2>/dev/null

echo "🛑 No-Hitter Forecaster stopped"