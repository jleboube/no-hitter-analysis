# Cloud Deployment Options

## Heroku (Easy)
```bash
# Install Heroku CLI, then:
heroku create no-hitter-forecaster
heroku config:set OPENWEATHER_API_KEY=your_key_here
git push heroku main
```

Add `Procfile`:
```
web: python3 main.py web
scheduler: python3 main.py scheduler
```

Enable both dynos in Heroku dashboard.

## Railway (Simple)
1. Connect GitHub repo to Railway
2. Set OPENWEATHER_API_KEY environment variable
3. Deploy automatically

## DigitalOcean App Platform
```yaml
# .do/app.yaml
name: no-hitter-forecaster
services:
- name: web
  source_dir: /
  github:
    repo: your-username/no-hitter-analysis
    branch: main
  run_command: python3 main.py web
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  http_port: 8501
  
- name: scheduler
  source_dir: /
  github:
    repo: your-username/no-hitter-analysis
    branch: main
  run_command: python3 main.py scheduler
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
```

## AWS/GCP/Azure
Use container services with the provided Dockerfile.
```

## 📋 **Quick Start Guide**

Choose your preferred option:

### **Local Background Process:**
```bash
# Start services
./run_production.sh

# Stop services  
./stop_production.sh
```

### **Docker (Recommended):**
```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### **Linux Systemd:**
```bash
# Copy service files
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload

# Enable and start services
sudo systemctl enable no-hitter-webapp no-hitter-scheduler
sudo systemctl start no-hitter-webapp no-hitter-scheduler

# Check status
sudo systemctl status no-hitter-webapp
```

## 🔍 **Monitoring & Logs**

All options provide logging:
- **Local**: `logs/webapp.log` and `logs/scheduler.log`
- **Docker**: `docker-compose logs`
- **Systemd**: `journalctl -u no-hitter-webapp -f`

## ✅ **Benefits of Each Approach:**

- **Background Process**: Simple, good for testing
- **Docker**: Portable, isolated, easy to deploy anywhere
- **Systemd**: Robust for Linux servers, auto-restart
- **Cloud**: Managed infrastructure, scalable

**Recommendation**: Start with Docker for development, then deploy to cloud for production!