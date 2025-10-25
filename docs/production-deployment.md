# 🚀 Production Deployment Guide

**Руководство по развертыванию AI систем в production среде**

---

## 📋 Быстрый старт

### Локальный запуск

```bash
# 1. Клонирование репозитория
git clone https://github.com/FUYOH666/ScanovichAI.git scanovich-ai-portfolio
cd scanovich-ai-portfolio

# 2. Создание виртуального окружения
python3.12 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# 3. Установка зависимостей
pip install -r requirements.txt

# 4. Запуск AI сервиса
python src/ai_service_example.py

# 5. Проверка работоспособности
curl http://localhost:8000/health
```

### Docker запуск

```bash
# Сборка и запуск всех сервисов
docker-compose up -d

# Проверка логов
docker-compose logs ai-service

# Проверка здоровья
curl http://localhost:8000/health

# Доступ к мониторингу
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
```

---

## 🏗️ Архитектура развертывания

### **Компоненты системы**

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AI Service    │    │   Prometheus    │    │    Grafana      │
│   Port: 8000    │    │   Port: 9090    │    │   Port: 3000    │
│                 │    │                 │    │                 │
│ - FastAPI       │    │ - Metrics       │    │ - Dashboards    │
│ - Model Serving │    │ - Monitoring    │    │ - Visualization │
│ - Health Checks │    │ - Alerting      │    │ - Reports       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Watchtower    │
                    │ - Auto Updates  │
                    │ - Container Mgmt│
                    └─────────────────┘
```

### **Масштабирование**

#### **Горизонтальное масштабирование**
```yaml
# docker-compose.scale.yml
version: '3.8'

services:
  ai-service:
    # ... базовая конфигурация
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 4G
          cpus: '2.0'
        reservations:
          memory: 2G
          cpus: '1.0'
```

#### **Load Balancing**
```nginx
# nginx.conf
upstream ai_services {
    server ai-service-1:8000;
    server ai-service-2:8000;
    server ai-service-3:8000;
}

server {
    listen 80;
    location / {
        proxy_pass http://ai_services;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 🔧 Конфигурация

### **Environment Variables**

```bash
# .env.example
# AI Service Configuration
ENVIRONMENT=production
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000

# Model Configuration
MODEL_PATH=/app/models
MODEL_VERSION=latest
GPU_ENABLED=true

# Data Configuration
DATA_PATH=/app/data
BATCH_SIZE=1000
MAX_FEATURES=1000

# Security
SECRET_KEY=your-secret-key-here
ENCRYPTION_KEY=your-encryption-key-here

# External Services (optional)
TELEGRAM_TOKEN=your-telegram-bot-token
GOOGLE_SHEETS_ID=your-google-sheets-id
REDIS_URL=redis://redis:6379
DATABASE_URL=postgresql://postgres:5432/ai_db

# Monitoring
PROMETHEUS_ENABLED=true
SENTRY_DSN=your-sentry-dsn
```

### **Конфигурация мониторинга**

#### **Prometheus**
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'ai-service'
    static_configs:
      - targets: ['ai-service:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
```

#### **Grafana Dashboards**
```json
{
  "dashboard": {
    "title": "AI Service Performance",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(requests_total[5m])",
            "legendFormat": "{{method}} {{endpoint}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ]
  }
}
```

---

## 📊 Мониторинг и метрики

### **Ключевые метрики**

#### **Performance Metrics**
- `ai_requests_total` - общее количество запросов
- `ai_inference_seconds` - время инференса модели
- `ai_active_models` - количество активных моделей
- `ai_model_accuracy` - точность модели

#### **System Metrics**
- CPU usage (%)
- Memory usage (GB)
- GPU utilization (%)
- Disk I/O (MB/s)
- Network I/O (MB/s)

#### **Business Metrics**
- Requests per minute
- Error rate (%)
- Average response time (ms)
- Throughput (predictions/hour)

### **Алерт-рулы**

```yaml
# Alert rules
groups:
  - name: ai_service
    rules:
      - alert: HighErrorRate
        expr: rate(errors_total[5m]) / rate(requests_total[5m]) > 0.05
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"

      - alert: SlowResponse
        expr: histogram_quantile(0.95, rate(request_duration_seconds_bucket[5m])) > 5
        for: 1m
        labels:
          severity: warning
        annotations:
          summary: "Slow response time detected"
```

---

## 🔒 Безопасность

### **Network Security**
```yaml
# Firewall rules
services:
  ai-service:
    # ... конфигурация сервиса
    networks:
      - ai-network
    # Блокировка внешнего доступа к базе данных
    # Доступ только через API Gateway

  postgres:
    networks:
      - db-network
    # Изоляция базы данных в отдельной сети
```

### **Data Protection**
```python
# Encryption at rest
from cryptography.fernet import Fernet

class DataSecurity:
    def __init__(self, key: str):
        self.cipher = Fernet(key)

    def encrypt_data(self, data: dict) -> str:
        return self.cipher.encrypt(json.dumps(data).encode()).decode()

    def decrypt_data(self, encrypted_data: str) -> dict:
        return json.loads(self.cipher.decrypt(encrypted_data.encode()).decode())
```

### **Access Control**
```python
# JWT Authentication
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=["HS256"])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

---

## 🚀 Оптимизация производительности

### **GPU Optimization**
```python
# CUDA optimization
import torch

def optimize_for_gpu():
    if torch.cuda.is_available():
        # Включение CUDA optimizations
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.benchmark = True
        torch.backends.cudnn.enabled = True

        # Оптимизация памяти
        torch.cuda.empty_cache()

        logger.info(f"GPU optimization enabled: {torch.cuda.get_device_name()}")
    else:
        logger.warning("GPU not available, running on CPU")
```

### **Model Optimization**
```python
# Model quantization and optimization
def optimize_model(model, optimization_level: str = "medium"):
    if optimization_level == "high":
        # Dynamic quantization
        model = torch.quantization.quantize_dynamic(
            model, {torch.nn.Linear}, dtype=torch.qint8
        )
    elif optimization_level == "medium":
        # Half precision (FP16)
        model = model.half()
    # "low" - no optimization

    return model
```

### **Caching Strategy**
```python
# Multi-level caching
from functools import lru_cache
import redis.asyncio as redis

class CacheManager:
    def __init__(self, redis_url: str = None):
        self.redis_client = redis.from_url(redis_url) if redis_url else None
        self.memory_cache = {}

    @lru_cache(maxsize=1000)
    async def get_cached_result(self, key: str) -> Optional[dict]:
        # 1. Check memory cache
        if key in self.memory_cache:
            return self.memory_cache[key]

        # 2. Check Redis cache
        if self.redis_client:
            cached_data = await self.redis_client.get(f"ai_cache:{key}")
            if cached_data:
                return json.loads(cached_data.decode())

        return None

    async def set_cached_result(self, key: str, value: dict, ttl: int = 3600):
        # Set in memory cache
        self.memory_cache[key] = value

        # Set in Redis cache
        if self.redis_client:
            await self.redis_client.setex(
                f"ai_cache:{key}",
                ttl,
                json.dumps(value)
            )
```

---

## 🧪 Тестирование

### **Load Testing**
```bash
# Использование locust для нагрузочного тестирования
pip install locust

# locustfile.py
from locust import HttpUser, task

class AIPredictionUser(HttpUser):
    @task
    def predict(self):
        self.client.post("/predict", json={
            "data": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            "model_version": "latest"
        })

# Запуск теста
locust -f locustfile.py --host http://localhost:8000
```

### **Integration Testing**
```python
# pytest integration tests
import pytest
from httpx import AsyncClient

@pytest.mark.integration
async def test_ai_service_integration():
    async with AsyncClient(app=app, base_url="http://localhost:8000") as client:
        # Test health endpoint
        health_response = await client.get("/health")
        assert health_response.status_code == 200

        # Test prediction endpoint
        predict_response = await client.post("/predict", json={
            "data": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
        })
        assert predict_response.status_code == 200
        assert "prediction" in predict_response.json()
```

---

## 📋 Чек-лист развертывания

### **Pre-deployment**
- [ ] Code review completed
- [ ] All tests passing
- [ ] Security audit completed
- [ ] Documentation updated
- [ ] Environment variables configured
- [ ] Backup strategy defined
- [ ] Rollback plan prepared

### **Deployment**
- [ ] Database migrations applied
- [ ] Models loaded and tested
- [ ] Health checks passing
- [ ] Monitoring configured
- [ ] Load balancer configured
- [ ] SSL certificates installed
- [ ] Firewall rules applied

### **Post-deployment**
- [ ] Functional testing completed
- [ ] Performance testing completed
- [ ] Monitoring dashboards verified
- [ ] Alert rules tested
- [ ] Documentation accessible
- [ ] Team training completed
- [ ] Support procedures documented

---

## 🆘 Troubleshooting

### **Common Issues**

#### **High Memory Usage**
```bash
# Check memory usage
docker stats ai-service

# Check for memory leaks
python -c "
import torch
print(f'GPU memory: {torch.cuda.memory_allocated()/1024**3:.2f}GB')
torch.cuda.empty_cache()
"
```

#### **Slow Inference**
```bash
# Profile inference time
python -c "
import time
import requests

start = time.time()
response = requests.post('http://localhost:8000/predict', json={'data': [...]})
end = time.time()

print(f'Inference time: {end-start:.3f}s')
"
```

#### **Model Loading Errors**
```bash
# Check model files
ls -la models/

# Test model loading
python -c "
from src.ai_service_example import SimpleModelManager
import asyncio

async def test():
    manager = SimpleModelManager('/app/models')
    await manager.load_model()
    print('Model loaded successfully')

asyncio.run(test())
"
```

### **Emergency Procedures**

#### **Service Restart**
```bash
# Docker restart
docker-compose restart ai-service

# Systemd restart (если используется)
sudo systemctl restart ai-service

# Manual restart
pkill -f "python.*ai_service" && python src/ai_service_example.py
```

#### **Data Recovery**
```bash
# Database backup
pg_dump -h localhost -U ai_user ai_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Model backup
cp -r models/ models_backup_$(date +%Y%m%d_%H%M%S)/

# Log collection
docker-compose logs ai-service > logs/ai_service_$(date +%Y%m%d_%H%M%S).log
```

---

## 📞 Поддержка

### **Контакты**
📧 **Email:** iamfuyoh@gmail.com
💬 **Telegram:** [@ScanovichAI](https://t.me/ScanovichAI)
🌐 **Website:** [scanovich.ai](https://scanovich.ai/)

### **Документация**
- 📚 [API Documentation](http://localhost:8000/docs)
- 🔧 [Architecture Guide](docs/architecture-guide.md)
- 🚀 [Deployment Guide](docs/production-deployment.md)

---

**© 2025 ScanovichAI | Production Deployment Guide**

*Это руководство основано на опыте развертывания AI систем в реальных production средах.*
