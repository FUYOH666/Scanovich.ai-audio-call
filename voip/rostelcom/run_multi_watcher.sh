#!/bin/bash
# CloudPBX RT Multi-Account Downloader - Скрипт запуска
# Запускает параллельную загрузку из всех 16 городов

# Переходим в директорию проекта
cd "$(dirname "$0")"

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}CloudPBX RT Multi-Account Downloader${NC}"
echo -e "${GREEN}Параллельная загрузка из всех городов${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""

# Проверяем, существует ли .env файл
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Ошибка - файл .env не найден!${NC}"
    echo "Скопируйте .env.example в .env и заполните данные:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
fi

# Проверяем наличие uv
if ! command -v uv &> /dev/null; then
    echo -e "${RED}❌ Ошибка - uv не установлен!${NC}"
    echo "Установите uv:"
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

# Синхронизируем зависимости через uv
echo -e "${YELLOW}Синхронизация зависимостей через uv...${NC}"
uv sync

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Ошибка синхронизации зависимостей${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Зависимости синхронизированы${NC}"

# Проверяем, установлены ли пароли
if grep -q "ЗАПОЛНИТЕ_ПАРОЛЬ" .env; then
    echo -e "${RED}❌ Ошибка - в .env найдены незаполненные пароли (ЗАПОЛНИТЕ_ПАРОЛЬ)${NC}"
    echo "Пожалуйста, откройте .env и заполните все пароли для городов"
    exit 1
fi

# Создаем директорию для загрузок если её нет
DOWNLOAD_DIR=$(grep "^DOWNLOAD_DIR=" .env | cut -d'=' -f2)
if [ -n "$DOWNLOAD_DIR" ]; then
    mkdir -p "$DOWNLOAD_DIR"
    echo -e "${GREEN}✅ Директория загрузок: $DOWNLOAD_DIR${NC}"
fi

echo ""
echo -e "${GREEN}Запуск Multi-Account Downloader...${NC}"
echo "Для остановки нажмите Ctrl+C"
echo ""

# Добавляем --delay 3 по умолчанию, если не указан
if [[ "$@" != *"--delay"* ]]; then
    echo -e "${YELLOW}Используется задержка 3 секунды между городами (защита от rate limit)${NC}"
    uv run multi_account_downloader.py --delay 3 "$@"
else
    uv run multi_account_downloader.py "$@"
fi

# Код выхода
exit_code=$?

if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}✅ Завершено успешно${NC}"
else
    echo -e "${RED}❌ Завершено с ошибкой (код: $exit_code)${NC}"
fi

exit $exit_code

