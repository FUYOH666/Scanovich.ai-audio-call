#!/usr/bin/env bash
#
# Автоматическая проверка перед коммитом
# Проверяет на утечки PII, секретов и упоминаний клиентов
#
# Использование: ./check_before_commit.sh
#
# Author: 
# Project: ASR Call Quality Analyzer
#

set -e

echo "=================================================="
echo "🔒 Проверка безопасности перед коммитом"
echo "=================================================="

ERRORS=0
WARNINGS=0

# 1. Проверка на телефонные номера
echo ""
echo "1️⃣  Проверка на телефонные номера..."
PHONES=$(grep -r "79[0-9]\{9\}" --include="*.py" --include="*.md" --include="*.yaml" \
  --exclude-dir=venv --exclude-dir=.git . 2>/dev/null | \
  grep -v "example\|placeholder" || true)

if [ -n "$PHONES" ]; then
    echo "   ❌ НАЙДЕНЫ ТЕЛЕФОННЫЕ НОМЕРА:"
    echo "$PHONES"
    ((ERRORS++))
else
    echo "   ✅ Телефонные номера не найдены"
fi

# 2. Проверка на email (кроме публичных)
echo ""
echo "2️⃣  Проверка на email адреса..."
EMAILS=$(grep -r "@" --include="*.py" --include="*.md" --include="*.yaml" \
  --exclude-dir=venv --exclude-dir=.git . 2>/dev/null | \
  grep -v "example\|placeholder\|Author\|Copyright\|LICENSE\|iamfuyoh666\|scanovich.ai\|ScanovichAI\|@FUYOH666" || true)

if [ -n "$EMAILS" ]; then
    echo "   ⚠️  НАЙДЕНЫ EMAIL АДРЕСА (проверьте вручную):"
    echo "$EMAILS" | head -5
    ((WARNINGS++))
else
    echo "   ✅ Подозрительные email не найдены"
fi

# 3. Проверка на API keys, tokens
echo ""
echo "3️⃣  Проверка на секреты..."
SECRETS=$(grep -ri "api[_-]key\|api[_-]secret\|token\|password" \
  --include="*.yaml" --include="*.py" --exclude-dir=venv --exclude-dir=.git . 2>/dev/null | \
  grep -v "example\|placeholder\|# \|def \|class \|import " | \
  grep -v "SECURITY.md\|check_before_commit.sh" || true)

if [ -n "$SECRETS" ]; then
    echo "   ⚠️  НАЙДЕНЫ УПОМИНАНИЯ СЕКРЕТОВ (проверьте вручную):"
    echo "$SECRETS" | head -5
    ((WARNINGS++))
else
    echo "   ✅ Секреты не найдены"
fi

# 4. Проверка staged файлов
echo ""
echo "4️⃣  Проверка staged файлов..."
STAGED=$(git diff --cached --name-only 2>/dev/null || true)

if [ -z "$STAGED" ]; then
    echo "   ⚠️  Нет файлов в staging (git add не выполнен?)"
    ((WARNINGS++))
else
    echo "   ✅ Staged файлы:"
    echo "$STAGED" | sed 's/^/      /'
    
    # Проверить, что не добавлены критичные файлы
    CRITICAL=$(echo "$STAGED" | grep -E "config.yaml|credentials/|branches.yaml|input/|output/|metadata/|\.db$|\.log$" || true)
    if [ -n "$CRITICAL" ]; then
        echo ""
        echo "   ❌ КРИТИЧНО: Staged файлы содержат конфиденциальные данные:"
        echo "$CRITICAL" | sed 's/^/      /'
        ((ERRORS++))
    fi
fi

# 5. Проверка .gitignore
echo ""
echo "5️⃣  Проверка .gitignore..."
GITIGNORE_CHECK=$(cat .gitignore | grep -E "input/|output/|metadata/|credentials/|config.yaml|branches.yaml" | wc -l)

if [ "$GITIGNORE_CHECK" -ge 5 ]; then
    echo "   ✅ .gitignore содержит критичные директории"
else
    echo "   ❌ .gitignore НЕ содержит все критичные директории"
    ((ERRORS++))
fi

# Итоги
echo ""
echo "=================================================="
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "✅ Проверка пройдена! Можно коммитить."
    echo "=================================================="
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo "⚠️  Найдены предупреждения ($WARNINGS), но критичных ошибок нет."
    echo "   Проверьте вручную перед коммитом."
    echo "=================================================="
    exit 0
else
    echo "❌ КРИТИЧНЫЕ ОШИБКИ ($ERRORS)! НЕ КОММИТЬТЕ!"
    echo "   Исправьте проблемы перед коммитом."
    echo "=================================================="
    exit 1
fi

