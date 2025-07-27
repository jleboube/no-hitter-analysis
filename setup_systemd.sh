#!/bin/bash

# Setup systemd services for No-Hitter Forecaster
echo "Setting up No-Hitter Forecaster systemd services..."

# Check if running from correct directory
if [ ! -f "main.py" ]; then
    echo "❌ Error: Please run this script from the no-hitter-analysis directory"
    exit 1
fi

# Get current directory
CURRENT_DIR=$(pwd)
echo "📁 Current directory: $CURRENT_DIR"

# Check if systemd files exist
if [ ! -d "systemd" ]; then
    echo "❌ Error: systemd directory not found"
    exit 1
fi

# Copy service files to systemd directory
echo "📋 Copying service files to /etc/systemd/system/..."
sudo cp systemd/*.service /etc/systemd/system/

# Reload systemd daemon
echo "🔄 Reloading systemd daemon..."
sudo systemctl daemon-reload

# Enable services
echo "⚡ Enabling services..."
sudo systemctl enable no-hitter-webapp no-hitter-scheduler

# Check if Python dependencies are installed
echo "🐍 Checking Python dependencies..."
if ! python3 -c "import streamlit" 2>/dev/null; then
    echo "⚠️  Warning: Python dependencies not found. Installing..."
    pip3 install -r requirements.txt
fi

# Create and set permissions for data directories
echo "📁 Setting up data directories..."
mkdir -p data logs
chown -R $USER:$USER data logs
chmod 755 data logs
chmod 644 data/* 2>/dev/null || true
chmod 644 logs/* 2>/dev/null || true

# Initialize data if needed
echo "📊 Initializing data..."
python3 main.py update

# Start services
echo "🚀 Starting services..."
sudo systemctl start no-hitter-webapp no-hitter-scheduler

# Check status
echo ""
echo "📊 Service Status:"
echo "=================="
sudo systemctl status no-hitter-webapp --no-pager -l
echo ""
sudo systemctl status no-hitter-scheduler --no-pager -l

echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 Web app should be available at: http://localhost:8501"
echo "⏰ Scheduler will run daily predictions at 6 AM ET"
echo ""
echo "📋 Useful commands:"
echo "  sudo systemctl status no-hitter-webapp     # Check web app status"
echo "  sudo systemctl status no-hitter-scheduler  # Check scheduler status"
echo "  sudo systemctl restart no-hitter-webapp    # Restart web app"
echo "  sudo systemctl restart no-hitter-scheduler # Restart scheduler"
echo "  sudo journalctl -u no-hitter-webapp -f     # View web app logs"
echo "  sudo journalctl -u no-hitter-scheduler -f  # View scheduler logs"
echo "  sudo systemctl stop no-hitter-*            # Stop all services"