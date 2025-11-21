# 🐳 AI Sales Assistant - Docker Deployment Guide

## Overview

This guide provides complete instructions for containerizing and deploying the AI Sales Assistant using Docker and Docker Compose.

## 📋 Prerequisites

- **Docker Desktop** installed and running
- **Docker Compose** (included with Docker Desktop)
- **Git** (for cloning the repository)

## 🚀 Quick Start

### 1. Clone and Setup
```bash
git clone <your-repo-url>
cd ai-sales-assistant
```

### 2. Configure Environment
```bash
# Copy the environment template
cp .env.docker .env

# Edit .env with your actual values
# Required: GEMINI_API_KEY and SECRET_KEY
```

### 3. Build and Run
```bash
# Build the Docker image
docker-compose build

# Start the application
docker-compose up -d

# Check logs
docker-compose logs -f
```

### 4. Access the Application
- **Web Interface:** http://localhost:5050
- **Health Check:** http://localhost:5050/api/health

## 📁 Project Structure

```
ai-sales-assistant/
├── Dockerfile                    # Docker image definition
├── docker-compose.yml           # Docker Compose configuration
├── .dockerignore               # Files to exclude from Docker build
├── requirements.txt            # Python dependencies
├── app.py                      # Flask application
├── DataFile_students_OPTIMIZED.xlsx  # Community database
├── templates/                  # Jinja2 templates
├── static/                     # CSS and JavaScript files
└── uploads/                    # File upload directory (mounted)
```

## 🏗️ Docker Configuration

### Dockerfile Features

- **Base Image:** `python:3.11-slim` (lightweight Python image)
- **System Dependencies:** GCC, Curl for health checks
- **Security:** Non-root user for container execution
- **Health Checks:** Automatic health monitoring
- **Optimization:** Multi-stage build with proper caching

### Docker Compose Features

- **Volume Mounting:** Persistent storage for uploads and logs
- **Environment Variables:** Secure configuration management
- **Networking:** Isolated network for container communication
- **Health Checks:** Container health monitoring
- **Restart Policy:** Automatic restart on failure

## ⚙️ Environment Configuration

### Required Variables

```bash
# Flask Security
SECRET_KEY=your_random_secret_key_here

# AI Integration
GEMINI_API_KEY=your_gemini_api_key_here
```

### Optional Variables

```bash
# External API Access
API_KEY=your_api_key_here

# Google Sheets CRM
GOOGLE_SPREADSHEET_ID=your_sheet_id
GOOGLE_SERVICE_ACCOUNT_FILE=/path/to/service-account.json

# Email Notifications
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

## 🚀 Deployment Commands

### Development
```bash
# Build and run in foreground
docker-compose up --build

# Run with specific environment file
docker-compose --env-file .env.dev up
```

### Production
```bash
# Build for production
docker-compose -f docker-compose.yml up --build -d

# Scale the application
docker-compose up -d --scale ai-sales-assistant=3
```

### Management
```bash
# View logs
docker-compose logs -f ai-sales-assistant

# Stop the application
docker-compose down

# Remove containers and volumes
docker-compose down -v

# Update the application
docker-compose pull && docker-compose up -d
```

## 🔍 Monitoring and Troubleshooting

### Health Checks
```bash
# Check container health
docker-compose ps

# View health status
curl http://localhost:5050/api/health
```

### Logs and Debugging
```bash
# View application logs
docker-compose logs ai-sales-assistant

# View specific service logs
docker-compose logs -f ai-sales-assistant

# Enter container for debugging
docker-compose exec ai-sales-assistant bash
```

### Common Issues

#### 1. Port Already in Use
```bash
# Change the port in docker-compose.yml
ports:
  - "8080:5050"  # Change 8080 to available port
```

#### 2. Permission Issues
```bash
# Fix file permissions
sudo chown -R $USER:$USER uploads/
sudo chown -R $USER:$USER output/
```

#### 3. Memory Issues
```bash
# Add memory limits in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 1G
    reservations:
      memory: 512M
```

## 🔒 Security Best Practices

### 1. Environment Variables
- Never commit `.env` files to version control
- Use strong, random `SECRET_KEY`
- Rotate API keys regularly

### 2. File Permissions
- Run containers as non-root user
- Mount volumes with appropriate permissions
- Use read-only mounts where possible

### 3. Network Security
- Use internal networks for multi-container apps
- Expose only necessary ports
- Use firewall rules to restrict access

## 📊 Performance Optimization

### 1. Docker Image Optimization
```dockerfile
# Use multi-stage builds
FROM python:3.11-slim as builder
# Build dependencies

FROM python:3.11-slim as runtime
# Copy only runtime dependencies
```

### 2. Volume Management
```yaml
volumes:
  - uploads_data:/app/uploads:rw
  - ./logs:/app/logs:rw
  - ./DataFile_students_OPTIMIZED.xlsx:/app/DataFile_students_OPTIMIZED.xlsx:ro
```

### 3. Resource Limits
```yaml
deploy:
  resources:
    limits:
      cpus: '1.0'
      memory: 1G
    reservations:
      cpus: '0.5'
      memory: 512M
```

## 🔄 Updates and Maintenance

### Updating Dependencies
```bash
# Update Python dependencies
pip-tools compile requirements.in > requirements.txt

# Rebuild the image
docker-compose build --no-cache
```

### Database Updates
```bash
# Update Excel database
cp new_database.xlsx DataFile_students_OPTIMIZED.xlsx

# Restart the container
docker-compose restart
```

### Backup Strategy
```bash
# Backup volumes
docker run --rm -v ai-sales-assistant_uploads_data:/data -v $(pwd):/backup alpine tar czf /backup/uploads_backup.tar.gz -C /data .

# Backup configuration
cp .env .env.backup
```

## 🐛 Troubleshooting Guide

### Container Won't Start
```bash
# Check Docker logs
docker-compose logs

# Check container status
docker-compose ps

# Validate configuration
docker-compose config
```

### Application Errors
```bash
# Check application logs
docker-compose exec ai-sales-assistant tail -f app.log

# Test API endpoints
curl http://localhost:5050/api/health
```

### Performance Issues
```bash
# Monitor resource usage
docker stats

# Check container logs for warnings
docker-compose logs | grep -i warn
```

## 📞 Support

For issues with:
- **Docker:** Check Docker Desktop logs
- **Application:** Check application logs in container
- **Configuration:** Validate `.env` file syntax

## 🎯 Production Deployment Checklist

- [ ] Environment variables configured
- [ ] SSL/TLS certificates installed
- [ ] Database backups configured
- [ ] Monitoring and alerting set up
- [ ] Security scanning completed
- [ ] Load testing performed
- [ ] Rollback plan documented

---

**🎉 Your AI Sales Assistant is now containerized and ready for deployment!**
