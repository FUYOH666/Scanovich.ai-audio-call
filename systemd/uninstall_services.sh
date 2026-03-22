#!/usr/bin/env bash
#
# Remove systemd units — Call Analytics Platform
# 
# Author: 
# Project: ASR Call Quality Analyzer
#

set -e

echo "=================================================="
echo "Удаление systemd сервисов Call Analytics Platform"
echo "=================================================="

# 1. Остановить сервисы
echo ""
echo "1️⃣  Остановка сервисов..."
sudo systemctl stop asr-watcher || true
sudo systemctl stop vllm || true
echo "   ✓ Сервисы остановлены"

# 2. Отключить автозагрузку
echo ""
echo "2️⃣  Отключение автозагрузки..."
sudo systemctl disable asr-watcher || true
sudo systemctl disable vllm || true
echo "   ✓ Автозагрузка отключена"

# 3. Удалить файлы сервисов
echo ""
echo "3️⃣  Удаление файлов сервисов..."
sudo rm -f /etc/systemd/system/asr-watcher.service
sudo rm -f /etc/systemd/system/vllm.service
echo "   ✓ Файлы сервисов удалены"

# 4. Перезагрузить systemd
echo ""
echo "4️⃣  Перезагрузка systemd daemon..."
sudo systemctl daemon-reload
sudo systemctl reset-failed
echo "   ✓ systemd обновлён"

echo ""
echo "=================================================="
echo "✅ Удаление завершено!"
echo "=================================================="
echo ""
echo "Теперь можно запускать процессы вручную:"
echo "  cd /path/to/project/call-analytics"
echo "  uv run python main.py run"
echo ""

