#!/usr/bin/env bash
#
# Установка всех systemd сервисов для ScanovichAI
#
# Author: Aleksandr Mordvinov
# Project: ScanovichAI
#

set -e

echo "=================================================="
echo "🚀 Установка systemd сервисов ScanovichAI"
echo "=================================================="

# 1. VLLM Server
echo ""
echo "1️⃣  Установка VLLM Server..."
sudo cp systemd/vllm.service /etc/systemd/system/
echo "   ✅ vllm.service установлен"

# 2. ASR-4.5 Watcher
echo ""
echo "2️⃣  Установка ASR-4.5 Watcher..."
sudo cp systemd/asr-watcher.service /etc/systemd/system/
echo "   ✅ asr-watcher.service установлен"

# 3. Загрузчики аудиозвонков
echo ""
echo "3️⃣  Установка загрузчиков аудиозвонков..."
sudo cp systemd/call-downloader-irkutsk.service /etc/systemd/system/
sudo cp systemd/call-downloader-volgodonks.service /etc/systemd/system/
sudo cp systemd/call-downloader-tymen.service /etc/systemd/system/
sudo cp systemd/call-downloader-angarsk.service /etc/systemd/system/
echo "   ✅ Все 4 загрузчика установлены"

# 4. Перезагрузить systemd
echo ""
echo "4️⃣  Перезагрузка systemd..."
sudo systemctl daemon-reload
echo "   ✅ systemd перезагружен"

# 5. Включить автозапуск
echo ""
echo "5️⃣  Включение автозапуска всех сервисов..."
sudo systemctl enable vllm.service
sudo systemctl enable asr-watcher.service
sudo systemctl enable call-downloader-irkutsk.service
sudo systemctl enable call-downloader-volgodonks.service
sudo systemctl enable call-downloader-tymen.service
sudo systemctl enable call-downloader-angarsk.service
echo "   ✅ Автозапуск включен для всех сервисов"

echo ""
echo "=================================================="
echo "✅ Установка завершена!"
echo "=================================================="
echo ""
echo "📋 Следующие шаги:"
echo ""
echo "1. Остановите все процессы в терминалах (Ctrl+C)"
echo ""
echo "2. Запустите все сервисы:"
echo "   sudo systemctl start vllm.service"
echo "   sudo systemctl start asr-watcher.service"
echo "   sudo systemctl start call-downloader-irkutsk.service"
echo "   sudo systemctl start call-downloader-volgodonks.service"
echo "   sudo systemctl start call-downloader-tymen.service"
echo "   sudo systemctl start call-downloader-angarsk.service"
echo ""
echo "3. Проверьте статус:"
echo "   sudo systemctl status vllm.service asr-watcher.service call-downloader-*.service"
echo ""
echo "4. Мониторинг логов:"
echo "   journalctl -u vllm.service -f"
echo "   journalctl -u asr-watcher.service -f"
echo "   journalctl -u call-downloader-irkutsk.service -f"
echo ""
echo "=================================================="

