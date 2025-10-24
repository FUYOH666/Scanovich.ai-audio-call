#!/usr/bin/env bash
#
# Подготовка репозитория к публичному релизу
# Удаление всех упоминаний клиента и персональных данных
#
# Author: Aleksandr Mordvinov
# Project: ScanovichAI
#

set -e

echo "=================================================="
echo "🚀 Подготовка к публичному релизу"
echo "=================================================="

# 1. Удалить директории с реальными данными
echo ""
echo "1️⃣  Удаление директорий с реальными данными..."
rm -rf quality_analysis/reports/ 2>/dev/null || true
echo "   ✅ quality_analysis/reports/ удалена"

# 2. Замены в Python файлах
echo ""
echo "2️⃣  Обработка Python файлов..."

# src/quality_analyzer.py
sed -i 's/медицинских центрах МРТ-Лидер/организациях/g' src/quality_analyzer.py
sed -i 's/Сеть клиник МРТ с оборудованием 1.5T и 3T/Организация с несколькими филиалами/g' src/quality_analyzer.py
sed -i 's/Администраторы принимают звонки для записи на диагностику/Операторы принимают звонки от клиентов/g' src/quality_analyzer.py
sed -i 's/скрипты обслуживания для каждого типа оборудования/корпоративные скрипты обслуживания/g' src/quality_analyzer.py
sed -i 's/администратора/оператора/g' src/quality_analyzer.py

echo "   ✅ quality_analyzer.py обработан"

# 3. Замены в Markdown файлах
echo ""
echo "3️⃣  Обработка Markdown файлов..."

# PROJECT_OVERVIEW.md
sed -i 's/Сеть МРТ-центров "МРТ-Лидер"/Сеть диагностических центров/g' PROJECT_OVERVIEW.md
sed -i 's/МРТ-центр/диагностический центр/g' PROJECT_OVERVIEW.md
sed -i 's/МРТ-Лидер/диагностическая сеть/g' PROJECT_OVERVIEW.md
sed -i 's/Анализ требований бизнеса (МРТ-центры)/Анализ требований бизнеса (диагностические центры)/g' PROJECT_OVERVIEW.md
sed -i 's/Текущий рынок: МРТ-центры/Текущий рынок: Диагностические центры/g' PROJECT_OVERVIEW.md
sed -i 's/Другие сети МРТ-центров/Другие сети диагностических центров/g' PROJECT_OVERVIEW.md
sed -i 's/Текущее:** МРТ-центры/Текущее:** Диагностические центры/g' PROJECT_OVERVIEW.md
sed -i 's/Подключение 2-3 новых филиалов МРТ-центров/Подключение 2-3 новых филиалов диагностических центров/g' PROJECT_OVERVIEW.md

echo "   ✅ PROJECT_OVERVIEW.md обработан"

# README.md - уже обработан ранее

# 4. Переименовать скрипты
echo ""
echo "4️⃣  Переименование скриптов..."
if [ -f "script установлены 1.5T.md" ]; then
    mv "script установлены 1.5T.md" "script_evaluation_type_A.md"
    echo "   ✅ script_evaluation_type_A.md создан"
fi

if [ -f "script установлены 3T.md" ]; then
    mv "script установлены 3T.md" "script_evaluation_type_B.md"
    echo "   ✅ script_evaluation_type_B.md создан"
fi

echo ""
echo "=================================================="
echo "✅ Подготовка завершена!"
echo "=================================================="
echo ""
echo "📋 Следующие шаги:"
echo "   1. Проверьте изменения: git diff"
echo "   2. Добавьте в staging: git add -A"
echo "   3. Закоммитьте: git commit -m '🔒 Prepare for public release'"
echo "   4. Запушьте: git push origin main"
echo ""

