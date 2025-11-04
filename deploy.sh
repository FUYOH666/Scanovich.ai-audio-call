#!/bin/bash
# Безопасный деплой скрипт для ASR-4.5
# Author: Aleksandr Mordvinov
# Date: 2025-11-04

set -e  # Прерывать выполнение при ошибке

echo "🚀 ASR-4.5 Deployment Script"
echo "============================"

# Проверка наличия Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не найден. Установите Python 3.12"
    exit 1
fi

# Проверка версии Python
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
if [[ "$(printf '%s\n' "3.12" "$PYTHON_VERSION" | sort -V | head -n1)" != "3.12" ]]; then
    echo "❌ Требуется Python 3.12. Текущая версия: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION найден"

# Проверка наличия uv
if ! command -v uv &> /dev/null; then
    echo "📦 Установка uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
fi

UV_VERSION=$(uv --version 2>/dev/null || echo "not found")
echo "✅ uv найден: $UV_VERSION"

# Синхронизация зависимостей через uv
echo "📦 Синхронизация зависимостей через uv..."
uv sync

# Проверка наличия uv.lock
if [ ! -f "uv.lock" ]; then
    echo "❌ ОШИБКА: uv.lock не найден после uv sync"
    exit 1
fi

echo "✅ Зависимости установлены из uv.lock"

# Создание необходимых директорий
echo "📁 Создание рабочих директорий..."
mkdir -p input output metadata archive logs analytics quality_analysis/{individual,aggregated,reports} credentials

# Создание файлов конфигурации из шаблонов
if [ ! -f "config.yaml" ]; then
    echo "⚙️ Создание config.yaml из шаблона..."
    cp config.example.yaml config.yaml
    echo "✅ config.yaml создан. ОТРЕДАКТИРУЙТЕ ЕГО под ваш бизнес!"
else
    echo "✅ config.yaml уже существует"
fi

# Проверка наличия .env.example
if [ -f ".env.example" ] && [ ! -f ".env" ]; then
    echo "🔐 Создание .env файла из шаблона..."
    cp .env.example .env
    echo "✅ .env создан. ЗАПОЛНИТЕ ЕГО реальными секретами!"
elif [ ! -f ".env" ]; then
    echo "⚠️ .env.example не найден, .env не создан"
fi

# Проверка безопасности (что конфиденциальные файлы не отслеживаются git)
echo "🔒 Проверка безопасности репозитория..."
CONFIDENTIAL_COUNT=$(git ls-files 2>/dev/null | grep -E "(input|logs|analytics|quality_analysis|metadata|output|archive|config\.yaml|branches\.yaml|credentials/)" | wc -l || echo "0")

if [ "$CONFIDENTIAL_COUNT" -gt 0 ]; then
    echo "⚠️ ВНИМАНИЕ: В репозитории найдены конфиденциальные файлы ($CONFIDENTIAL_COUNT шт.)"
    echo "📋 Рекомендуется выполнить очистку:"
    echo "   git rm -r --cached input/ logs/ analytics/ quality_analysis/ metadata/ output/ archive/ config.yaml branches.yaml credentials/"
    echo "   git commit -m 'SECURITY: Remove confidential data'"
else
    echo "✅ Репозиторий безопасен"
fi

# Проверка здоровья системы
echo "🏥 Проверка здоровья системы..."
if uv run python main.py health; then
    echo "✅ Система готова к работе!"
else
    echo "⚠️ Некоторые компоненты требуют настройки"
    echo "📖 См. документацию: README.md"
fi

echo ""
echo "🎯 Следующие шаги:"
echo "=================="
echo "1. 📝 Отредактируйте config.yaml под ваш бизнес"
echo "2. 🔐 Заполните .env реальными секретами (если нужно)"
echo "3. 🚀 Запустите систему: uv run python main.py run"
echo "4. 📊 Загрузите тестовые файлы в input/"
echo "5. 📈 Проверьте работу: uv run python main.py health"
echo ""
echo "📚 Документация:"
echo "- README.md - основное руководство"
echo "- DEPLOYMENT_GUIDE.md - полное руководство по развертыванию"
echo ""
echo "🎉 Успешного деплоя!"
