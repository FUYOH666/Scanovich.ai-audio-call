# 🚀 Руководство по развертыванию ASR Call Quality Analyzer

**Полное руководство по установке и настройке для 24/7 работы**

---

## 📋 Предварительные требования

### Аппаратные:
- ✅ NVIDIA GPU (RTX 5090 или аналог с 24GB+ VRAM)
- ✅ 16GB+ RAM
- ✅ 100GB+ свободного места на диске
- ✅ Стабильное интернет-соединение (для загрузки моделей)

### Программные:
- ✅ Ubuntu 22.04+ (или другой Linux)
- ✅ Python 3.12
- ✅ CUDA 12.4+
- ✅ Git
- ✅ SSH ключ для GitHub

---

## 🔧 Шаг 1: Клонирование репозитория

```bash
# Клонировать репозиторий
git clone git@github.com:YOUR_USERNAME/analyze-calls-AI.git ASR-4.5
cd ASR-4.5
```

---

## 🐍 Шаг 2: Установка Python зависимостей

```bash
# Установить uv (если не установлен)
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"

# Синхронизировать зависимости из uv.lock
uv sync
```

**Ожидаемое время:** 5-10 минут (зависит от скорости интернета и загрузки PyTorch)

**Примечание:** PyTorch с CUDA устанавливается автоматически через `uv.toml` конфигурацию

---

## ⚙️ Шаг 3: Настройка конфигураций

### 3.1. Основной конфиг (config.yaml)

```bash
# Скопировать пример
cp config.example.yaml config.yaml

# Отредактировать config.yaml
nano config.yaml
```

**Что нужно настроить:**
- `analytics.telegram.chat_id` — ваш Telegram chat ID
- `google_sheets.spreadsheet_id` — ID вашей Google таблицы
- Остальное можно оставить по умолчанию

### 3.2. Google Sheets credentials

```bash
# Положить файл с credentials в директорию
cp /path/to/your/google_credentials.json credentials/google_credentials.json
```

**Как получить credentials:**
1. Перейти в [Google Cloud Console](https://console.cloud.google.com/)
2. Создать проект
3. Включить Google Sheets API
4. Создать Service Account
5. Скачать JSON ключ

### 3.3. Эталонные адреса и админы (branches.yaml)

```bash
# Создать файл с эталонными данными
cp branches.example.yaml branches.yaml

# Отредактировать branches.yaml
nano branches.yaml
```

**Структура:**
```yaml
branches:
  - address: "Street Name, Building 123"
    variants: ["street example 123", "street example"]
    
admins:
  - canonical_name: "Admin Name"
    variants: ["Variant1", "Variant2", "Variant3"]
```

---

## 🤖 Шаг 4: Установка VLLM сервера

### 4.1. Клонировать VLLM проект

```bash
cd /path/to/project
git clone https://github.com/vllm-project/vllm.git vLLm
cd vLLm
```

### 4.2. Установить VLLM

```bash
# Создать venv
# Виртуальное окружение создается автоматически через uv sync
uv run python -m pip install --upgrade pip

# Установить VLLM
uv pip install vllm
```

### 4.3. Скачать модель LLM

```bash
# Создать директорию для моделей
mkdir -p models

# Скачать модель (через huggingface-cli или wget)
huggingface-cli download YOUR_MODEL_NAME --local-dir models/YOUR_MODEL_NAME
```

**Ожидаемое время:** 30-60 минут (модель ~15GB)

---

## 🔍 Шаг 5: Проверка установки

```bash
cd /path/to/project/ASR-4.5

# Проверить здоровье системы
uv run python main.py health
```

**Ожидаемый вывод:**
```
✓ Config валиден
✓ GPU: NVIDIA GeForce RTX 5090
✓ VLLM доступен
✓ Telegram бот активен
✓ Google Sheets доступна
```

**Если VLLM недоступен:**
```bash
# Запустить VLLM вручную (в отдельном терминале)
cd /path/to/project/vLLm
uv run python -m vllm.entrypoints.openai.api_server \
    --model models/YOUR_MODEL_NAME \
    --dtype float16 \
    --max-model-len 16384 \
    --tensor-parallel-size 1 \
    --gpu-memory-utilization 0.8 \
    --max-num-seqs 1 \
    --host 0.0.0.0 \
    --port 8000
```

---

## 🚀 Шаг 6: Запуск системы

### Вариант A: Ручной запуск (для тестирования)

```bash
cd /path/to/project/ASR-4.5

# Запустить daemon
uv run python main.py run
```

**Остановка:** `Ctrl+C`

### Вариант B: Systemd сервисы (для 24/7 работы)

**Рекомендуется для production!** Подробности в разделе [Настройка systemd сервисов](#настройка-systemd-сервисов-для-247-работы).

---

## 📥 Шаг 7: Настройка загрузчиков аудиозвонков (опционально)

Если у вас есть АТС с записями звонков:

```bash
# 1. Клонировать проект загрузчиков
cd /path/to/project
git clone <ваш-репо-загрузчиков> Calls-downloader

# 2. Настроить каждый загрузчик
cd Calls-downloader/Provider-A-City1
cp .env.example .env
nano .env  # Указать credentials АТС

# 3. Установить systemd сервисы (см. раздел ниже)
cd /path/to/project/ASR-4.5
sudo ./systemd/install_all_services.sh
```

---

## 🛡️ Шаг 8: Защита от автологаута (критично!)

```bash
cd /path/to/project/ASR-4.5

# Отключить автоматические logout/suspend
sudo ./systemd/disable_autologout.sh

# Финальная настройка systemd-logind
sudo ./systemd/finish_setup.sh

# Перезагрузить систему
sudo reboot
```

**После перезагрузки:**
```bash
# Проверить настройки
./systemd/check_session_settings.sh
```

**Должно вывести:**
```
✅ Все настройки корректны!
   Система настроена для 24/7 работы.
```

---

## 📊 Шаг 9: Проверка работы

### 9.1. Добавить тестовый аудиофайл

```bash
# Скопировать MP3 файл в input/
cp /path/to/test.mp3 input/

# Проверить логи
tail -f logs/asr-watcher.log
```

**Ожидаемый результат:**
- Файл обработан (~45 секунд)
- Транскрипция в `output/test.txt`
- Метаданные в `metadata/test.json`
- Анализ качества в `quality_analysis/individual/test.json`
- Запись в Google Sheets

### 9.2. Проверить отчеты

```bash
# Отправить тестовый Telegram отчет
uv run python main.py telegram-report --type daily

# Обновить Dashboard
uv run python main.py update-dashboard
```

---

## 🔧 Troubleshooting

### Проблема: VLLM не запускается

**Решение:**
```bash
# Проверить GPU
nvidia-smi

# Проверить CUDA
nvcc --version

# Переустановить VLLM
cd /path/to/project/vLLm
uv pip uninstall vllm
uv pip install vllm
```

### Проблема: Whisper не находит модель

**Решение:**
```bash
# Скачать модель вручную
uv run python -c "from faster_whisper import WhisperModel; WhisperModel('large-v3', device='cuda')"
```

### Проблема: Google Sheets ошибка доступа

**Решение:**
```bash
# Проверить credentials
cat credentials/google_credentials.json

# Проверить доступ
uv run python main.py test-sheets
```

### Проблема: Telegram не отправляется

**Решение:**
```bash
# Проверить chat_id в config.yaml
grep chat_id config.yaml

# Проверить бот токен
curl https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getMe
```

---

## 🛡️ Настройка systemd сервисов для 24/7 работы

### Зачем нужны systemd сервисы?

**Проблема:** Если запускать процессы вручную через терминал, они привязаны к пользовательской сессии и остановятся при:
- Logout пользователя
- Перезагрузке системы
- Сбое GNOME сессии
- Закрытии терминала

**Решение:** Миграция на systemd сервисы дает:
- ✅ Независимость от пользовательской сессии
- ✅ Автозапуск при загрузке системы
- ✅ Автоматический перезапуск при падении
- ✅ Централизованное логирование
- ✅ Управление зависимостями

---

### Архитектура системы

Система состоит из следующих компонентов:

1. **VLLM Server** — LLM постобработка (порт 8000)
2. **ASR-4.5 Watcher** — главный процесс транскрипции
3. **Загрузчики аудиозвонков** (опционально, 4 процесса)

---

### Установка всех сервисов

#### Быстрая установка (рекомендуется):

```bash
cd /path/to/project/ASR-4.5

# Установить все сервисы одной командой
sudo ./systemd/install_all_services.sh

# Запустить все сервисы
sudo systemctl start vllm.service
sudo systemctl start asr-watcher.service
sudo systemctl start call-downloader-provider-a-city1.service
sudo systemctl start call-downloader-provider-b-city1.service
sudo systemctl start call-downloader-provider-b-city2.service
sudo systemctl start call-downloader-provider-a-city2.service
```

#### Ручная установка:

**1. VLLM Server:**
```bash
# Установить сервис
sudo cp systemd/vllm.service /etc/systemd/system/
sudo systemctl daemon-reload

# Включить автозапуск
sudo systemctl enable vllm.service

# Запустить
sudo systemctl start vllm.service

# Проверить статус
sudo systemctl status vllm.service
```

**2. ASR-4.5 Watcher:**
```bash
# Установить сервис
sudo cp systemd/asr-watcher.service /etc/systemd/system/
sudo systemctl daemon-reload

# Включить автозапуск
sudo systemctl enable asr-watcher.service

# Запустить
sudo systemctl start asr-watcher.service

# Проверить статус
sudo systemctl status asr-watcher.service
```

**3. Загрузчики аудиозвонков (опционально):**
```bash
# Установить все 4 сервиса
sudo cp systemd/call-downloader-*.service /etc/systemd/system/
sudo systemctl daemon-reload

# Включить автозапуск
sudo systemctl enable call-downloader-provider-a-city1.service
sudo systemctl enable call-downloader-provider-b-city1.service
sudo systemctl enable call-downloader-provider-b-city2.service
sudo systemctl enable call-downloader-provider-a-city2.service

# Запустить все
sudo systemctl start call-downloader-provider-a-city1.service
sudo systemctl start call-downloader-provider-b-city1.service
sudo systemctl start call-downloader-provider-b-city2.service
sudo systemctl start call-downloader-provider-a-city2.service
```

---

### Мониторинг и управление сервисами

#### Проверка статуса всех сервисов

```bash
# Все сразу
sudo systemctl status vllm.service asr-watcher.service call-downloader-*.service

# По отдельности
sudo systemctl status vllm.service
sudo systemctl status asr-watcher.service
```

#### Просмотр логов

```bash
# В реальном времени
journalctl -u vllm.service -f
journalctl -u asr-watcher.service -f
journalctl -u call-downloader-provider-a-city1.service -f

# Последние 100 строк
journalctl -u vllm.service -n 100
journalctl -u asr-watcher.service -n 100

# За сегодня
journalctl -u vllm.service --since today
journalctl -u asr-watcher.service --since today

# Только ошибки
journalctl -u vllm.service -p err
journalctl -u asr-watcher.service -p err
```

#### Управление сервисами

```bash
# Запуск
sudo systemctl start vllm.service
sudo systemctl start asr-watcher.service

# Остановка
sudo systemctl stop vllm.service
sudo systemctl stop asr-watcher.service

# Перезапуск
sudo systemctl restart vllm.service
sudo systemctl restart asr-watcher.service

# Включить автозапуск
sudo systemctl enable vllm.service

# Отключить автозапуск
sudo systemctl disable vllm.service
```

---

### Исправление проблем с отключением сессии пользователя

#### Проблема

Система автоматически завершала пользовательские сессии из-за настроек энергосбережения GNOME, что приводило к остановке всех процессов.

#### Найденные проблемы

1. `org.gnome.settings-daemon.plugins.power sleep-inactive-ac-timeout` = 3600 сек (1 час)
2. `org.gnome.desktop.screensaver logout-delay` = 7200 сек (2 часа)
3. `org.gnome.settings-daemon.plugins.power idle-dim` = true

#### Исправления

Все настройки исправлены на значения, предотвращающие автоматический сон и выход из сессии через скрипт `disable_autologout.sh`.

#### Проверка настроек

```bash
cd /path/to/project/ASR-4.5
./systemd/check_session_settings.sh
```

**Должно вывести:**
```
✅ Все настройки корректны!
```

#### Применение исправлений

Если найдены проблемы, запустите:

```bash
sudo ./systemd/disable_autologout.sh
sudo reboot
```

#### Критически важные настройки

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

---

### Troubleshooting systemd сервисов

#### Проблема: Сервис не запускается

```bash
# 1. Проверить статус
sudo systemctl status service-name.service

# 2. Проверить логи
journalctl -u service-name.service -n 50

# 3. Проверить синтаксис сервиса
systemd-analyze verify /etc/systemd/system/service-name.service

# 4. Перезагрузить systemd
sudo systemctl daemon-reload
```

#### Проблема: Сервис падает при запуске

```bash
# 1. Проверить права доступа
ls -la /path/to/working/directory

# 2. Проверить наличие venv
ls -la /path/tuv run python

# 3. Проверить переменные окружения
systemctl show service-name.service | grep Environment

# 4. Запустить вручную для отладки
cd /path/to/working/directory
uv run python script.py
```

#### Проблема: GPU не доступен в systemd сервисе

```bash
# Добавить в сервис:
Environment="CUDA_VISIBLE_DEVICES=0"

# Проверить доступность GPU
nvidia-smi
```

---

## 📊 Системные ресурсы

### GPU:
- **Модель:** NVIDIA GeForce RTX 5090 (или аналог)
- **VRAM:** 32GB (используется ~30GB для VLLM)
- **Утилизация:** 0% (idle), до 100% при инференсе

### Диск:
- **Рекомендуется:** 1TB+ свободного места
- **Автоочистка:** включена
- **Хранение входных файлов:** 30 дней
- **Сжатие архивов:** после 7 дней
- **Максимальное использование диска:** 80%
- **Время запуска:** 03:00 каждый день

---

## ✅ Чеклист готовности к production

- [ ] Python 3.12 установлен
- [ ] CUDA 12.4+ установлен
- [ ] GPU доступен (nvidia-smi)
- [ ] Репозиторий склонирован
- [ ] Зависимости установлены (pyproject.toml + uv.lock)
- [ ] config.yaml настроен
- [ ] Google credentials добавлены
- [ ] branches.yaml настроен
- [ ] VLLM сервер запущен
- [ ] LLM модель скачана
- [ ] `uv run python main.py health` проходит
- [ ] Systemd сервисы установлены
- [ ] Автологаут отключен (disable_autologout.sh выполнен)
- [ ] Система перезагружена
- [ ] Настройки сессии проверены (check_session_settings.sh)
- [ ] Тестовый файл обработан успешно
- [ ] Telegram отчет отправлен
- [ ] Google Sheets обновлена

---

## 📚 Дополнительные ресурсы

- **`README.md`** — основная документация
- **`PROJECT_OVERVIEW.md`** — полное описание проекта и архитектуры
- **`CONTRIBUTING.md`** — руководство для контрибьюторов
- **`SECURITY.md`** — политика безопасности

---

**© 2025 ASR Call Quality Analyzer**
