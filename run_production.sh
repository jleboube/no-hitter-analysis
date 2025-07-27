#!/bin/bash

# No-Hitter Forecaster Production Runner
echo "Starting No-Hitter Forecaster in production mode..."

# Create logs directory
mkdir -p logs

# Start the scheduler in background
echo "Starting prediction scheduler..."
nohup python3 main.py scheduler > logs/scheduler.log 2>&1 &
SCHEDULER_PID=$!
echo "Scheduler started with PID: $SCHEDULER_PID"

# Wait a moment for scheduler to initialize
sleep 2

# Start the web application in background
echo "Starting web application..."
nohup python3 main.py web > logs/webapp.log 2>&1 &
WEBAPP_PID=$!
echo "Web app started with PID: $WEBAPP_PID"

# Save PIDs for easy stopping
echo $SCHEDULER_PID > logs/scheduler.pid
echo $WEBAPP_PID > logs/webapp.pid

echo "✅ No-Hitter Forecaster is now running in production!"
echo "📱 Web app: http://localhost:8501"
echo "📊 Scheduler: Running daily at 6 AM ET"
echo "📋 Logs: Check logs/ directory"
echo ""
echo "To stop:"
echo "  ./stop_production.sh"
echo "  or kill -9 $SCHEDULER_PID $WEBAPP_PID"