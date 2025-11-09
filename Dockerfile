# 🐳 ASR-4.5 Production Container
#
# Production-ready Docker образ для ASR Call Quality Analyzer
# Использует uv для детерминированной установки зависимостей из uv.lock

# Stage 1: Build dependencies
FROM python:3.12-slim as builder

# Установка системных зависимостей для сборки
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Установка uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.cargo/bin:/root/.local/bin:$PATH"

# Создание рабочей директории
WORKDIR /build

# Копирование файлов зависимостей (для кеширования слоя)
COPY pyproject.toml uv.lock uv.toml ./

# Установка зависимостей в изолированное окружение
RUN uv sync --frozen --no-dev

# Stage 2: Runtime
FROM python:3.12-slim

# Метаданные образа
LABEL maintainer="ScanovichAI <contact@scanovich.ai>"
LABEL version="4.5.0"
LABEL description="ASR-4.5 Production System - Call Quality Analyzer"

# Установка минимальных системных зависимостей для runtime
RUN apt-get update && apt-get install -y \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Создание непривилегированного пользователя
RUN useradd --create-home --shell /bin/bash asruser
USER asruser
WORKDIR /home/asruser/app

# Копирование установленных зависимостей из builder stage
COPY --from=builder --chown=asruser:asruser /build/.venv /home/asruser/app/.venv

# Копирование кода приложения
COPY --chown=asruser:asruser src/ ./src/
COPY --chown=asruser:asruser main.py ./
COPY --chown=asruser:asruser pyproject.toml ./
COPY --chown=asruser:asruser uv.toml ./

# Создание необходимых директорий
RUN mkdir -p logs input output metadata archive analytics quality_analysis quarantine

# Переменные окружения
ENV PATH="/home/asruser/app/.venv/bin:$PATH"
ENV PYTHONPATH="/home/asruser/app"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check (для CLI приложения проверяем доступность модуля)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import src.config_validation; print('OK')" || exit 1

# По умолчанию запускаем health check
CMD ["python", "main.py", "health"]
