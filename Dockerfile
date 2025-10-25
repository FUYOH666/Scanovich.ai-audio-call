# 🐳 ScanovichAI Portfolio - AI Service Container
#
# Production-ready Docker образ для AI сервисов
# Демонстрирует лучшие практики контейнеризации AI приложений

FROM python:3.12-slim

# Метаданные образа
LABEL maintainer="ScanovichAI <contact@scanovich.ai>"
LABEL version="1.0.0"
LABEL description="ScanovichAI Portfolio - AI Service Container"

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Создание непривилегированного пользователя
RUN useradd --create-home --shell /bin/bash aiuser
USER aiuser
WORKDIR /home/aiuser/app

# Установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Копирование кода приложения
COPY --chown=aiuser:aiuser src/ ./src/
COPY --chown=aiuser:aiuser docs/ ./docs/
COPY --chown=aiuser:aiuser README.md .
COPY --chown=aiuser:aiuser pyproject.toml .

# Создание необходимых директорий
RUN mkdir -p logs data models temp

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# Переменные окружения
ENV PYTHONPATH="/home/aiuser/app"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Порт приложения
EXPOSE 8000

# Запуск приложения
CMD ["python", "src/ai_service_example.py"]
