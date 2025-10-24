#!/usr/bin/env bash
# Очистка Git истории от скомпрометированного ключа

set -e

echo "🧹 ОЧИСТКА GIT ИСТОРИИ ОТ CREDENTIALS"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "⚠️  ВНИМАНИЕ: Это перепишет историю Git!"
echo "⚠️  После этого потребуется force push!"
echo ""
read -p "Продолжить? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Отменено."
    exit 0
fi

echo ""
echo "1️⃣ Создаю backup текущей ветки..."
git branch backup-before-cleanup-$(date +%Y%m%d-%H%M%S)

echo ""
echo "2️⃣ Удаляю credentials/google_credentials.json из истории..."
git filter-branch --force --index-filter \
  'git rm --cached --ignore-unmatch credentials/google_credentials.json' \
  --prune-empty --tag-name-filter cat -- --all

echo ""
echo "3️⃣ Очищаю рефлоги..."
git for-each-ref --format='delete %(refname)' refs/original | git update-ref --stdin
git reflog expire --expire=now --all
git gc --prune=now --aggressive

echo ""
echo "✅ Готово!"
echo ""
echo "📋 СЛЕДУЮЩИЕ ШАГИ:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. Проверь, что credentials/ в .gitignore:"
echo "   grep 'credentials/' .gitignore"
echo ""
echo "2. Force push в GitHub:"
echo "   git push origin main --force"
echo ""
echo "3. Убедись, что новый credentials НЕ попал в Git:"
echo "   git ls-files | grep credentials"
echo ""
