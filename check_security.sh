#!/usr/bin/env bash
# Финальная проверка безопасности репозитория

set -e

echo "🔍 ФИНАЛЬНАЯ ПРОВЕРКА БЕЗОПАСНОСТИ РЕПОЗИТОРИЯ"
echo "================================================"
echo ""

# 1. Проверка на упоминания клиентов
echo "1️⃣ Проверка на упоминания конкретных клиентов..."
# Проверка на конкретные названия компаний (добавьте свои паттерны при необходимости)
if grep -riE "название_клиента|конкретная_компания|client_company_name" \
    --include="*.md" --include="*.py" --include="*.yaml" --include="*.sh" --include="*.service" \
    --exclude-dir=venv --exclude-dir=.git . 2>/dev/null; then
    echo "❌ НАЙДЕНЫ упоминания конкретных клиентов!"
    exit 1
else
    echo "✅ Упоминания конкретных клиентов не найдены"
fi
echo ""

# 2. Проверка на упоминания провайдеров и партнеров
echo "2️⃣ Проверка на упоминания конкретных провайдеров..."
# Проверка на конкретные названия провайдеров (добавьте свои паттерны при необходимости)
if grep -riE "название_провайдера|конкретный_провайдер|provider_name" \
    --include="*.md" --include="*.py" --include="*.yaml" --include="*.sh" --include="*.service" \
    --exclude-dir=venv --exclude-dir=.git . 2>/dev/null; then
    echo "❌ НАЙДЕНЫ упоминания конкретных провайдеров!"
    exit 1
else
    echo "✅ Упоминания конкретных провайдеров не найдены"
fi
echo ""

# 3. Проверка на телефонные номера (кроме примеров)
echo "3️⃣ Проверка на реальные телефонные номера..."
if grep -rE "\+7[0-9]{10}|8[0-9]{10}|79[0-9]{9}" \
    --include="*.md" --include="*.py" --include="*.yaml" \
    --exclude-dir=venv --exclude-dir=.git . 2>/dev/null | \
    grep -v "79XXXXXXXXX" | grep -v "example" | grep -v "ТЕЛЕФОН" | grep -v "89501234567"; then
    echo "❌ НАЙДЕНЫ реальные телефонные номера!"
    exit 1
else
    echo "✅ Реальные телефонные номера не найдены"
fi
echo ""

# 4. Проверка на email (кроме публичных)
echo "4️⃣ Проверка на приватные email адреса..."
if grep -rE "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}" \
    --include="*.md" --include="*.py" --include="*.yaml" \
    --exclude-dir=venv --exclude-dir=.git . 2>/dev/null | \
    grep -v "iamfuyoh666@gmail.com" | grep -v "example@" | grep -v "user@" | \
    grep -v "admin@" | grep -v "git@github.com" | grep -v "client_email" | \
    grep -v "@project.iam.gserviceaccount.com"; then
    echo "⚠️  Найдены email адреса (проверьте вручную)"
else
    echo "✅ Приватные email не найдены"
fi
echo ""

# 5. Проверка .gitignore
echo "5️⃣ Проверка .gitignore на критичные паттерны..."
critical_patterns=(
    "config.yaml"
    "credentials/"
    "branches.yaml"
    "input/"
    "output/"
    "logs/"
    "*.db"
    "analytics/"
    "quarantine/"
)

missing_patterns=()
for pattern in "${critical_patterns[@]}"; do
    if ! grep -q "^${pattern}" .gitignore 2>/dev/null; then
        missing_patterns+=("$pattern")
    fi
done

if [ ${#missing_patterns[@]} -gt 0 ]; then
    echo "⚠️  Отсутствуют паттерны в .gitignore:"
    printf '   - %s\n' "${missing_patterns[@]}"
else
    echo "✅ Все критичные паттерны в .gitignore"
fi
echo ""

# 6. Проверка на наличие защищенных файлов в репо
echo "6️⃣ Проверка на случайно добавленные приватные файлы..."
if git ls-files | grep -E "config\.yaml|credentials/.*\.json|branches\.yaml|.*\.db$" | grep -v "example"; then
    echo "❌ НАЙДЕНЫ приватные файлы в репозитории!"
    exit 1
else
    echo "✅ Приватные файлы не добавлены в репозиторий"
fi
echo ""

echo "================================================"
echo "✅ ПРОВЕРКА ЗАВЕРШЕНА УСПЕШНО!"
echo "Репозиторий готов к публичному использованию."
