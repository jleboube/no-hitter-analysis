# Deployment Checklist

## Quick Deploy (Recommended)

### Option 1: Docker (Easiest)
```bash
git clone <repository>
cd no-hitter-analysis
docker-compose up -d
```
✅ **No permission issues** - Docker handles everything

### Option 2: Systemd (Linux Servers)
```bash
git clone <repository>
cd no-hitter-analysis
sudo ./setup_systemd.sh
```
✅ **Automated setup** - Script handles permissions

## Manual Deployment Steps

If you need to deploy manually, follow these steps in order:

### 1. Prerequisites
```bash
# Install Python dependencies
pip3 install -r requirements.txt

# Install system dependencies (if needed)
sudo apt update
sudo apt install python3-pip python3-venv
```

### 2. **CRITICAL: Set up directories and permissions**
```bash
# Create directories
mkdir -p data logs

# Set proper ownership (replace 'joe' with your username)
sudo chown -R $USER:$USER data logs

# Set proper permissions
chmod 755 data logs
```

### 3. Initialize data
```bash
python3 main.py update
```

### 4. Test permissions
```bash
# This should work without errors
python3 main.py status
python3 main.py force-update
```

### 5. Deploy services
Choose one:

**Systemd:**
```bash
sudo ./setup_systemd.sh
```

**Manual:**
```bash
python3 main.py web &
python3 main.py scheduler &
```

## Common Issues & Solutions

### Permission Denied Error
```
touch: cannot touch 'data/test.json': Permission denied
```

**Solution:**
```bash
sudo chown -R $USER:$USER data/ logs/
chmod 755 data/ logs/
```

### Systemd Service Won't Start
```
status=200/CHDIR
```

**Solution:**
```bash
# Fix working directory in service files
sudo sed -i 's|WorkingDirectory=.*|WorkingDirectory=$(pwd)|g' /etc/systemd/system/no-hitter-*.service
sudo systemctl daemon-reload
sudo systemctl restart no-hitter-webapp no-hitter-scheduler
```

### MLB API Not Working
The app has fallback systems:
1. MLB Stats API (primary)
2. MySportsFeeds API (backup)
3. Simulated data (final fallback)

Check logs for API errors:
```bash
sudo journalctl -u no-hitter-scheduler -f
```

## Verification

After deployment, verify everything works:

```bash
# Check services
sudo systemctl status no-hitter-webapp no-hitter-scheduler

# Check predictions
python3 main.py status

# Check web access
curl http://localhost:8501

# Check logs
tail -f logs/scheduler.log
```

## Production Notes

- **Data persistence**: The `data/` directory contains predictions and cache
- **Logs location**: Check `logs/` directory for troubleshooting
- **Port**: Web app runs on port 8501 by default
- **Schedule**: Predictions auto-generate at 6:00 AM during MLB season
- **Updates**: Use `python3 main.py force-update` to manually refresh predictions