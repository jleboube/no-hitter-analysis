#!/bin/bash

echo "🔄 Restarting No-Hitter Forecaster services..."

# Restart both services
sudo systemctl restart no-hitter-webapp no-hitter-scheduler

# Wait a moment
sleep 2

# Check status
echo ""
echo "📊 Service Status:"
echo "=================="
sudo systemctl status no-hitter-webapp --no-pager -l | head -10
echo ""
sudo systemctl status no-hitter-scheduler --no-pager -l | head -10

echo ""
echo "✅ Services restarted!"
echo "🌐 Web app: http://localhost:8501"