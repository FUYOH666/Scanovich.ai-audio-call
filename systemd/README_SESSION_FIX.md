# Исправление проблем с отключением сессии пользователя

## Проблема
Система автоматически завершала пользовательские сессии из-за настроек энергосбережения GNOME, что приводило к остановке всех процессов (ASR, VLLM и т.д.).

## Найденные проблемы
1. `org.gnome.settings-daemon.plugins.power sleep-inactive-ac-timeout` = 3600 сек (1 час)
2. `org.gnome.desktop.screensaver logout-delay` = 7200 сек (2 часа)
3. `org.gnome.settings-daemon.plugins.power idle-dim` = true

## Исправления
Все настройки исправлены на значения, предотвращающие автоматический сон и выход из сессии.

## Профилактика

### 1. Проверка настроек
Запустите скрипт проверки:
```bash
./systemd/check_session_settings.sh
```

### 2. Применение исправлений
Если найдены проблемы, запустите:
```bash
sudo ./systemd/disable_autologout.sh
sudo reboot
```

### 3. Установка сервисов
Установите системные сервисы для 24/7 работы:
```bash
# Установка ASR сервиса
sudo cp systemd/asr-watcher.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable asr-watcher.service
sudo systemctl start asr-watcher.service

# Установка VLLM сервиса
sudo cp systemd/vllm.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable vllm.service
sudo systemctl start vllm.service
```

### 4. Мониторинг
Для мониторинга состояния системы:
```bash
# Проверка сервисов
systemctl status asr-watcher.service vllm.service

# Проверка логов
journalctl -u asr-watcher.service -f
journalctl -u vllm.service -f

# Проверка сессии
./systemd/check_session_settings.sh
```

## Автоматический запуск при загрузке
Скрипт `finish_setup.sh` автоматически применяет настройки systemd-logind:
```bash
sudo ./systemd/finish_setup.sh
sudo reboot
```

## Рекомендации
1. **Не используйте графический интерфейс для длительной работы** - используйте только SSH или Tmux/Screen
2. **Регулярно проверяйте настройки** с помощью `check_session_settings.sh`
3. **Мониторьте системные логи** на предмет новых проблем
4. **Настройте уведомления** о падении сервисов в Telegram

## Критически важные настройки
```bash
# Должны быть установлены в 0/false:
gsettings get org.gnome.settings-daemon.plugins.power sleep-inactive-ac-timeout     # 0
gsettings get org.gnome.settings-daemon.plugins.power sleep-inactive-battery-timeout # 0
gsettings get org.gnome.desktop.screensaver logout-delay                             # 0
gsettings get org.gnome.desktop.screensaver logout-enabled                           # false
gsettings get org.gnome.settings-daemon.plugins.power idle-dim                       # false

# systemd-logind должен содержать:
# IdleAction=ignore
# IdleActionSec=0
```
