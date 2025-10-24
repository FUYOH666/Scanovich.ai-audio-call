#!/usr/bin/env bash
#
# Установка systemd сервисов для ASR-4.5
# 
# Author: Aleksandr Mordvinov
# Project: ScanovichAI
#

set -e

PROJECT_DIR="/home/ai/Документы/ScanovichAI/ASR-4.5"

echo "=================================================="
echo "Установка systemd сервисов ASR-4.5"
echo "=================================================="

# 1. VLLM сервис
echo ""
echo "1️⃣  Установка VLLM сервиса..."
sudo cp "$PROJECT_DIR/systemd/vllm.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable vllm.service
echo "   ✓ VLLM сервис установлен и добавлен в автозагрузку"

# 2. ASR-Watcher сервис
echo ""
echo "2️⃣  Установка ASR-Watcher сервиса..."
sudo cp "$PROJECT_DIR/systemd/asr-watcher.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable asr-watcher.service
echo "   ✓ ASR-Watcher сервис установлен и добавлен в автозагрузку"

echo ""
echo "=================================================="
echo "✅ Установка завершена!"
echo "=================================================="
echo ""
echo "Для запуска сервисов:"
echo "  sudo systemctl start vllm"
echo "  sudo systemctl start asr-watcher"
echo ""
echo "Для проверки статуса:"
echo "  sudo systemctl status vllm"
echo "  sudo systemctl status asr-watcher"
echo ""
echo "Для просмотра логов:"
echo "  sudo journalctl -u vllm -f"
echo "  sudo journalctl -u asr-watcher -f"
echo ""
echo "Для остановки:"
echo "  sudo systemctl stop vllm"
echo "  sudo systemctl stop asr-watcher"
echo ""
echo "=================================================="

