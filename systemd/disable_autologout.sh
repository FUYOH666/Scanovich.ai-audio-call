#!/usr/bin/env bash
#
# Отключение всех автоматических logout/suspend/lock для 24/7 работы
# 
# Author: 
# Project: ASR Call Quality Analyzer
#

echo "=================================================="
echo "🔧 Отключение автоматических logout/suspend/lock"
echo "=================================================="

# 1. Отключить автоматический idle logout (GNOME)
echo ""
echo "1️⃣  Отключение автоматического logout..."
gsettings set org.gnome.desktop.session idle-delay 0
IDLE=$(gsettings get org.gnome.desktop.session idle-delay)
if [ "$IDLE" = "uint32 0" ]; then
    echo "   ✅ Автологout отключён (idle-delay=0)"
else
    echo "   ⚠️  Проверь: idle-delay=$IDLE"
fi

# 2. Отключить автоблокировку экрана
echo ""
echo "2️⃣  Отключение автоблокировки экрана..."
gsettings set org.gnome.desktop.screensaver lock-enabled false
gsettings set org.gnome.desktop.screensaver idle-activation-enabled false
LOCK=$(gsettings get org.gnome.desktop.screensaver lock-enabled)
if [ "$LOCK" = "false" ]; then
    echo "   ✅ Автоблокировка экрана отключена"
else
    echo "   ⚠️  Проверь: lock-enabled=$LOCK"
fi

# 3. Отключить автоматический suspend/hibernate
echo ""
echo "3️⃣  Отключение suspend/hibernate..."
sudo systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target 2>/dev/null || true
echo "   ✅ Suspend/hibernate замаскированы"

# 4. Отключить автоматическое выключение экрана и сон
echo ""
echo "4️⃣  Отключение автоматического затемнения/выключения экрана..."
gsettings set org.gnome.desktop.session idle-delay 0
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing'
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type 'nothing'
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-timeout 0
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-timeout 0
gsettings set org.gnome.settings-daemon.plugins.power idle-dim false
echo "   ✅ Автоматическое выключение экрана и сон отключены"

# 4.1. Отключить автоматический logout в GNOME
echo ""
echo "4️⃣  Отключение автоматического logout в GNOME..."
gsettings set org.gnome.desktop.screensaver logout-enabled false
gsettings set org.gnome.desktop.screensaver logout-delay 0
echo "   ✅ Автоматический logout в GNOME отключен"

# 5. Systemd logind - отключить автологout
echo ""
echo "5️⃣  Настройка systemd-logind..."
if ! grep -q "^IdleAction=ignore" /etc/systemd/logind.conf 2>/dev/null; then
    echo "IdleAction=ignore" | sudo tee -a /etc/systemd/logind.conf > /dev/null
fi
if ! grep -q "^IdleActionSec=0" /etc/systemd/logind.conf 2>/dev/null; then
    echo "IdleActionSec=0" | sudo tee -a /etc/systemd/logind.conf > /dev/null
fi
echo "   ✅ systemd-logind настроен (требуется перезагрузка для применения)"

echo ""
echo "=================================================="
echo "✅ Все настройки применены!"
echo "=================================================="
echo ""
echo "📋 Что было отключено:"
echo "  • Автоматический logout при бездействии"
echo "  • Автоблокировка экрана"
echo "  • Suspend/Hibernate"
echo "  • Автоматическое выключение экрана"
echo "  • Автоматический сон системы"
echo "  • Затемнение экрана"
echo "  • Автоматический logout в GNOME"
echo ""
echo "💡 Рекомендация:"
echo "  Перезагрузи систему для полного применения настроек:"
echo "  sudo reboot"
echo ""
echo "🔍 Проверка настроек:"
echo "  gsettings get org.gnome.desktop.session idle-delay  # Должно быть: 0"
echo "  gsettings get org.gnome.desktop.screensaver lock-enabled  # Должно быть: false"
echo "  gsettings get org.gnome.settings-daemon.plugins.power sleep-inactive-ac-timeout  # Должно быть: 0"
echo "  gsettings get org.gnome.desktop.screensaver logout-enabled  # Должно быть: false"
echo ""
echo "=================================================="

