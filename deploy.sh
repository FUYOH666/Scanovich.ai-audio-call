#!/bin/bash
# Безопасный деплой скрипт для ASR-4.5
# Author: 
# Date: 21 октября 2025

set -e  # Прерывать выполнение при ошибке

echo "🚀 ASR-4.5 Deployment Script"
echo "============================"

# Проверка наличия Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 не найден. Установите Python 3.12+"
    exit 1
fi

# Проверка версии Python
PYTHON_VERSION=$(python3 -c "import sys; print(sys.version_info[:2])" | tr ' ' '.' | tr -d ',()')
if [[ "$(printf '%s\n' "3.12" "$PYTHON_VERSION" | sort -V | head -n1)" != "3.12" ]]; then
    echo "❌ Требуется Python 3.12+. Текущая версия: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION найден"

# Создание виртуального окружения
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
else
    echo "✅ Виртуальное окружение уже существует"
fi

# Активация виртуального окружения и установка зависимостей
echo "📦 Установка зависимостей..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

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

# Создание .env файла
if [ ! -f ".env" ]; then
    echo "🔐 Создание .env файла..."
    cp .env.example .env
    echo "✅ .env создан. ЗАПОЛНИТЕ ЕГО реальными секретами!"
else
    echo "✅ .env уже существует"
fi

# Проверка безопасности (что конфиденциальные файлы не отслеживаются git)
echo "🔒 Проверка безопасности репозитория..."
CONFIDENTIAL_COUNT=$(git ls-files 2>/dev/null | grep -E "(input|logs|analytics|quality_analysis|metadata|output|archive)" | wc -l || echo "0")

if [ "$CONFIDENTIAL_COUNT" -gt 0 ]; then
    echo "⚠️ ВНИМАНИЕ: В репозитории найдены конфиденциальные файлы ($CONFIDENTIAL_COUNT шт.)"
    echo "📋 Рекомендуется выполнить очистку:"
    echo "   git rm -r --cached input/ logs/ analytics/ quality_analysis/ metadata/ output/ archive/"
    echo "   git commit -m 'SECURITY: Remove confidential data'"
else
    echo "✅ Репозиторий безопасен"
fi

# Проверка здоровья системы
echo "🏥 Проверка здоровья системы..."
if python3 main.py health; then
    echo "✅ Система готова к работе!"
else
    echo "⚠️ Некоторые компоненты требуют настройки"
    echo "📖 См. документацию: README.md"
fi

echo ""
echo "🎯 Следующие шаги:"
echo "=================="
echo "1. 📝 Отредактируйте config.yaml под ваш бизнес"
echo "2. 🔐 Заполните .env реальными секретами"
echo "3. 🚀 Запустите систему: python main.py run"
echo "4. 📊 Загрузите тестовые файлы в input/"
echo "5. 📈 Проверьте работу: python main.py health"
echo ""
echo "📚 Документация:"
echo "- README.md - основное руководство"
- QUICKSTART.md - быстрый старт"
echo "- GITHUB_PUBLISH_GUIDE.md - правила публикации"
echo ""
echo "🎉 Успешного деплоя!"
