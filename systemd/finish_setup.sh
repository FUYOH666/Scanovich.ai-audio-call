#!/usr/bin/env bash
#
# Финальная настройка systemd-logind и маскирование suspend/hibernate
# Запусти этот скрипт в своём терминале: sudo ./systemd/finish_setup.sh
#

set -e

echo "=================================================="
echo "🔧 Финальная настройка системы для 24/7 работы"
echo "=================================================="

# 1. Проверить что уже есть в конфиге
if grep -q "^IdleAction=ignore" /etc/systemd/logind.conf 2>/dev/null; then
    echo "✅ IdleAction уже настроен"
else
    echo "" >> /etc/systemd/logind.conf
    echo "# ASR-4.5: отключение автологаута" >> /etc/systemd/logind.conf
    echo "IdleAction=ignore" >> /etc/systemd/logind.conf
    echo "IdleActionSec=0" >> /etc/systemd/logind.conf
    echo "✅ Настройки добавлены в /etc/systemd/logind.conf"
fi

# 2. Маскировать suspend/hibernate
echo ""
systemctl mask sleep.target suspend.target hibernate.target hybrid-sleep.target
echo "✅ Suspend/Hibernate замаскированы"

echo ""
echo "=================================================="
echo "✅ Настройка завершена!"
echo "=================================================="
echo ""
echo "Для полного применения настроек рекомендуется:"
echo "  sudo reboot"
echo ""

