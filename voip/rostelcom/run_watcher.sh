#!/bin/bash
# CloudPBX RT Call Records Watcher - Скрипт запуска
# Запускает загрузчик для одного аккаунта

# Переходим в директорию проекта
cd "$(dirname "$0")"

# Проверяем, существует ли .env файл
if [ ! -f ".env" ]; then
    echo "$(date): Ошибка - файл .env не найден!"
    echo "Скопируйте .env.example в .env и заполните данные:"
    echo "  cp .env.example .env"
    exit 1
fi

# Проверяем наличие uv
if ! command -v uv &> /dev/null; then
    echo "$(date): Ошибка - uv не установлен!"
    echo "Установите uv:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Синхронизируем зависимости через uv
uv sync

if [ $? -ne 0 ]; then
    echo "$(date): Ошибка синхронизации зависимостей"
    exit 1
fi

# Запускаем watcher
uv run call_records_watcher.py "$@"

# Код выхода
exit $?
