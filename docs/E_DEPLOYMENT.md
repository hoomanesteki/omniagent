# OmniAgent Deployment Guide
## Production Deployment Instructions

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Local Development](#local-development)
3. [Docker Deployment](#docker-deployment)
4. [Cloud Deployment](#cloud-deployment)
5. [Configuration](#configuration)
6. [Monitoring](#monitoring)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Prerequisites

- Python 3.8+
- pip
- Git

### Fastest Setup

```bash
# Clone repository
git clone https://github.com/yourusername/omniagent.git
cd omniagent

# Install dependencies
pip install -r requirements.txt

# Run
streamlit run app.py
```

---

## Local Development

### Step 1: Environment Setup

```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
nano .env
```

```bash
# .env contents
GROQ_API_KEY=gsk_your_key_here
LLM_MODEL=llama-3.3-70b-versatile
```

### Step 3: Run Application

```bash
# Development mode
streamlit run app.py

# With custom port
streamlit run app.py --server.port 8080

# With specific address
streamlit run app.py --server.address 0.0.0.0
```

### Development Tools

```bash
# Install dev dependencies
pip install pytest pytest-cov black flake8

# Run tests
pytest

# Format code
black .

# Lint code
flake8 .
```

---

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create non-root user
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Run application
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
```

### Build and Run

```bash
# Build image
docker build -t omniagent:latest .

# Run container
docker run -d \
    --name omniagent \
    -p 8501:8501 \
    -e GROQ_API_KEY=your_key_here \
    omniagent:latest

# View logs
docker logs -f omniagent

# Stop container
docker stop omniagent
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  omniagent:
    build: .
    container_name: omniagent
    ports:
      - "8501:8501"
    environment:
      - GROQ_API_KEY=${GROQ_API_KEY}
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8501/_stcore/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

```bash
# Start with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

---

## Cloud Deployment

### Streamlit Cloud

1. **Push to GitHub**
```bash
git add .
git commit -m "Prepare for deployment"
git push origin main
```

2. **Configure Streamlit Cloud**
   - Go to https://share.streamlit.io
   - Connect GitHub repository
   - Set secrets in dashboard:
     - `GROQ_API_KEY`: Your API key

3. **Deploy**
   - Click "Deploy"
   - Wait for build to complete

### AWS (EC2)

```bash
# Connect to EC2
ssh -i key.pem ec2-user@your-instance.amazonaws.com

# Install dependencies
sudo yum update -y
sudo yum install python3 python3-pip git -y

# Clone and setup
git clone https://github.com/yourusername/omniagent.git
cd omniagent
pip3 install -r requirements.txt

# Set environment variable
export GROQ_API_KEY=your_key_here

# Run with nohup
nohup streamlit run app.py --server.port 8501 --server.address 0.0.0.0 &
```

### AWS (ECS/Fargate)

```json
// task-definition.json
{
  "family": "omniagent",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "containerDefinitions": [
    {
      "name": "omniagent",
      "image": "your-ecr-repo/omniagent:latest",
      "portMappings": [
        {
          "containerPort": 8501,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "GROQ_API_KEY",
          "value": "your_key_here"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/omniagent",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

### Google Cloud Run

```bash
# Build and push to GCR
gcloud builds submit --tag gcr.io/PROJECT_ID/omniagent

# Deploy to Cloud Run
gcloud run deploy omniagent \
    --image gcr.io/PROJECT_ID/omniagent \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars GROQ_API_KEY=your_key_here
```

### Azure Container Instances

```bash
# Create resource group
az group create --name omniagent-rg --location eastus

# Create container
az container create \
    --resource-group omniagent-rg \
    --name omniagent \
    --image your-registry/omniagent:latest \
    --dns-name-label omniagent \
    --ports 8501 \
    --environment-variables GROQ_API_KEY=your_key_here
```

### Heroku

```bash
# Create Procfile
echo "web: streamlit run app.py --server.port \$PORT --server.address 0.0.0.0" > Procfile

# Create app
heroku create omniagent-app

# Set config
heroku config:set GROQ_API_KEY=your_key_here

# Deploy
git push heroku main
```

---

## Configuration

### Streamlit Config

```toml
# .streamlit/config.toml

[server]
port = 8501
address = "0.0.0.0"
headless = true
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#667eea"
backgroundColor = "#0e1117"
secondaryBackgroundColor = "#262730"
textColor = "#fafafa"
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GROQ_API_KEY` | Groq API key | Required |
| `LLM_MODEL` | Model name | llama-3.3-70b-versatile |
| `PORT` | Server port | 8501 |

---

## Monitoring

### Health Check Endpoint

```bash
# Check health
curl http://localhost:8501/_stcore/health
```

### Logging

```python
# Add to app.py for production logging
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('omniagent.log'),
        logging.StreamHandler()
    ]
)
```

### Prometheus Metrics (Optional)

```python
# Add prometheus metrics
from prometheus_client import Counter, Histogram, start_http_server

REQUESTS = Counter('omniagent_requests_total', 'Total requests')
LATENCY = Histogram('omniagent_request_latency_seconds', 'Request latency')

# Start metrics server
start_http_server(9090)
```

---

## Troubleshooting

### Common Issues

#### Port Already in Use

```bash
# Find process using port
lsof -i :8501

# Kill process
kill -9 <PID>
```

#### Memory Issues

```bash
# Increase memory limit
streamlit run app.py --server.maxUploadSize 200
```

#### SSL Certificate Errors

```bash
# Install certificates
pip install certifi
export SSL_CERT_FILE=$(python -c "import certifi; print(certifi.where())")
```

#### Module Not Found

```bash
# Reinstall dependencies
pip install --force-reinstall -r requirements.txt
```

### Debug Mode

```bash
# Run with debug logging
STREAMLIT_LOG_LEVEL=debug streamlit run app.py
```

### Container Debugging

```bash
# Shell into container
docker exec -it omniagent /bin/bash

# View container logs
docker logs omniagent --tail 100

# Check container health
docker inspect omniagent | grep -A 10 Health
```

---

## Production Checklist

### Pre-Deployment

- [ ] Tests passing
- [ ] Dependencies updated
- [ ] Security scan completed
- [ ] Environment variables configured
- [ ] Secrets secured

### Deployment

- [ ] Health check passing
- [ ] Logs accessible
- [ ] SSL/TLS configured
- [ ] Backup configured
- [ ] Monitoring enabled

### Post-Deployment

- [ ] Smoke tests passed
- [ ] Performance acceptable
- [ ] Alerts configured
- [ ] Documentation updated

---

*Last updated: 2026-01-01*
