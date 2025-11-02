#!/usr/bin/env bash
#
# Проверка настроек сессии и энергосбережения для предотвращения отключений
#
# Author: 
# Project: ASR Call Quality Analyzer
#

echo "=================================================="
echo "🔍 Проверка настроек сессии и энергосбережения"
echo "=================================================="

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

WARNINGS=0
ERRORS=0

# 1. Проверка GNOME настроек сессии
echo ""
echo "1️⃣  Проверка GNOME настроек сессии..."

IDLE_DELAY=$(gsettings get org.gnome.desktop.session idle-delay 2>/dev/null)
if [ "$IDLE_DELAY" = "uint32 0" ]; then
    echo "   ✅ idle-delay: $IDLE_DELAY (правильно)"
else
    echo -e "   ❌ idle-delay: $IDLE_DELAY ${RED}(должно быть 0)${NC}"
    ((ERRORS++))
fi

# 2. Проверка настроек экрана
echo ""
echo "2️⃣  Проверка настроек экрана..."

LOCK_ENABLED=$(gsettings get org.gnome.desktop.screensaver lock-enabled 2>/dev/null)
if [ "$LOCK_ENABLED" = "false" ]; then
    echo "   ✅ lock-enabled: $LOCK_ENABLED (правильно)"
else
    echo -e "   ❌ lock-enabled: $LOCK_ENABLED ${RED}(должно быть false)${NC}"
    ((ERRORS++))
fi

LOGOUT_ENABLED=$(gsettings get org.gnome.desktop.screensaver logout-enabled 2>/dev/null)
if [ "$LOGOUT_ENABLED" = "false" ]; then
    echo "   ✅ logout-enabled: $LOGOUT_ENABLED (правильно)"
else
    echo -e "   ❌ logout-enabled: $LOGOUT_ENABLED ${RED}(должно быть false)${NC}"
    ((ERRORS++))
fi

LOGOUT_DELAY=$(gsettings get org.gnome.desktop.screensaver logout-delay 2>/dev/null)
if [[ "$LOGOUT_DELAY" == "uint32 0" ]] || [ "$LOGOUT_DELAY" = "0" ]; then
    echo "   ✅ logout-delay: $LOGOUT_DELAY (правильно)"
else
    echo -e "   ❌ logout-delay: $LOGOUT_DELAY ${RED}(должно быть 0)${NC}"
    ((ERRORS++))
fi

# 3. Проверка настроек энергосбережения
echo ""
echo "3️⃣  Проверка настроек энергосбережения..."

SLEEP_AC=$(gsettings get org.gnome.settings-daemon.plugins.power sleep-inactive-ac-timeout 2>/dev/null)
if [ "$SLEEP_AC" = "0" ]; then
    echo "   ✅ sleep-inactive-ac-timeout: $SLEEP_AC (правильно)"
else
    echo -e "   ❌ sleep-inactive-ac-timeout: $SLEEP_AC ${RED}(должно быть 0)${NC}"
    ((ERRORS++))
fi

SLEEP_BATTERY=$(gsettings get org.gnome.settings-daemon.plugins.power sleep-inactive-battery-timeout 2>/dev/null)
if [ "$SLEEP_BATTERY" = "0" ]; then
    echo "   ✅ sleep-inactive-battery-timeout: $SLEEP_BATTERY (правильно)"
else
    echo -e "   ❌ sleep-inactive-battery-timeout: $SLEEP_BATTERY ${RED}(должно быть 0)${NC}"
    ((ERRORS++))
fi

IDLE_DIM=$(gsettings get org.gnome.settings-daemon.plugins.power idle-dim 2>/dev/null)
if [ "$IDLE_DIM" = "false" ]; then
    echo "   ✅ idle-dim: $IDLE_DIM (правильно)"
else
    echo -e "   ❌ idle-dim: $IDLE_DIM ${RED}(должно быть false)${NC}"
    ((WARNINGS++))
fi

# 4. Проверка systemd-logind
echo ""
echo "4️⃣  Проверка systemd-logind..."

if [ -f /etc/systemd/logind.conf ]; then
    IDLE_ACTION=$(grep "^IdleAction=" /etc/systemd/logind.conf 2>/dev/null | cut -d'=' -f2)
    if [ "$IDLE_ACTION" = "ignore" ]; then
        echo "   ✅ IdleAction: $IDLE_ACTION (правильно)"
    else
        echo -e "   ❌ IdleAction: $IDLE_ACTION ${RED}(должно быть ignore)${NC}"
        ((ERRORS++))
    fi

    IDLE_ACTION_SEC=$(grep "^IdleActionSec=" /etc/systemd/logind.conf 2>/dev/null | cut -d'=' -f2)
    if [ "$IDLE_ACTION_SEC" = "0" ]; then
        echo "   ✅ IdleActionSec: $IDLE_ACTION_SEC (правильно)"
    else
        echo -e "   ❌ IdleActionSec: $IDLE_ACTION_SEC ${RED}(должно быть 0)${NC}"
        ((ERRORS++))
    fi
else
    echo -e "   ❌ ${RED}Файл /etc/systemd/logind.conf не найден${NC}"
    ((ERRORS++))
fi

# 5. Проверка маскировки suspend
echo ""
echo "5️⃣  Проверка маскировки suspend..."

SLEEP_MASKED=$(systemctl is-enabled sleep.target 2>/dev/null | grep masked)
if [ -n "$SLEEP_MASKED" ]; then
    echo "   ✅ sleep.target: замаскирован (правильно)"
else
    echo -e "   ❌ sleep.target: ${RED}не замаскирован${NC}"
    ((ERRORS++))
fi

SUSPEND_MASKED=$(systemctl is-enabled suspend.target 2>/dev/null | grep masked)
if [ -n "$SUSPEND_MASKED" ]; then
    echo "   ✅ suspend.target: замаскирован (правильно)"
else
    echo -e "   ❌ suspend.target: ${RED}не замаскирован${NC}"
    ((ERRORS++))
fi

# 6. Проверка текущей сессии
echo ""
echo "6️⃣  Проверка текущей сессии..."

SESSION_IDLE=$(loginctl session-status | grep "Idle:" | awk '{print $2}')
if [ "$SESSION_IDLE" = "no" ]; then
    echo "   ✅ Сессия активна (не idle)"
else
    echo -e "   ❌ Сессия в режиме idle: ${RED}$SESSION_IDLE${NC}"
    ((WARNINGS++))
fi

# Итоги
echo ""
echo "=================================================="
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "✅ ${GREEN}Все настройки корректны!${NC}"
    echo "   Система настроена для 24/7 работы."
elif [ $ERRORS -eq 0 ] && [ $WARNINGS -gt 0 ]; then
    echo -e "⚠️  ${YELLOW}Найдены предупреждения ($WARNINGS), но критических ошибок нет${NC}"
    echo "   Рекомендуется исправить предупреждения."
else
    echo -e "❌ ${RED}Найдены критические проблемы ($ERRORS ошибок, $WARNINGS предупреждений)${NC}"
    echo "   Требуется исправление настроек!"
fi
echo "=================================================="

if [ $ERRORS -gt 0 ]; then
    echo ""
    echo "💡 Для исправления проблем запустите:"
    echo "   sudo ./systemd/disable_autologout.sh"
    echo ""
    echo "🔄 После исправлений перезагрузите систему:"
    echo "   sudo reboot"
fi
