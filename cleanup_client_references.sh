#!/usr/bin/env bash
#
# Скрипт для удаления упоминаний клиента перед публикацией
#
# Author: Aleksandr Mordvinov
# Project: ScanovichAI
#

set -e

echo "=================================================="
echo "🧹 Очистка упоминаний клиента из кода"
echo "=================================================="

# Замены в Python файлах
echo ""
echo "1️⃣  Обработка Python файлов..."

# src/quality_analyzer.py
sed -i 's/медицинских центрах МРТ-Лидер/компаниях и организациях/g' src/quality_analyzer.py
sed -i 's/Сеть клиник МРТ с оборудованием 1.5T и 3T/Компания с несколькими филиалами/g' src/quality_analyzer.py
sed -i 's/Администраторы принимают звонки для записи на диагностику/Операторы принимают звонки от клиентов/g' src/quality_analyzer.py
sed -i 's/скрипты обслуживания для каждого типа оборудования/корпоративные скрипты обслуживания/g' src/quality_analyzer.py

echo "   ✅ quality_analyzer.py обработан"

# Замены в Markdown файлах
echo ""
echo "2️⃣  Обработка Markdown файлов..."

# PROJECT_OVERVIEW.md
sed -i 's/МРТ-центров "МРТ-Лидер"/медицинских центров/g' PROJECT_OVERVIEW.md
sed -i 's/МРТ-центры/медицинские центры/g' PROJECT_OVERVIEW.md
sed -i 's/МРТ-Лидер/медицинская сеть/g' PROJECT_OVERVIEW.md
sed -i 's/Сеть МРТ-центров/Сеть медицинских центров/g' PROJECT_OVERVIEW.md

echo "   ✅ PROJECT_OVERVIEW.md обработан"

# README.md
sed -i 's/МРТ-центр/медицинский центр/g' README.md
sed -i 's/МРТ-Лидер/медицинская сеть/g' README.md

echo "   ✅ README.md обработан"

echo ""
echo "=================================================="
echo "✅ Очистка завершена!"
echo "=================================================="
echo ""
echo "📋 Проверьте изменения:"
echo "   git diff"
echo ""
echo "Если все корректно, закоммитьте:"
echo "   git add -A"
echo "   git commit -m '🔒 Remove client-specific references'"
echo ""

