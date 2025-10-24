# 🚀 Руководство по развертыванию ScanovichAI

**Быстрый старт для развертывания на новом ПК**

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
- ✅ SSH ключ для GitHub (для приватного репо)

---

## 🔧 Шаг 1: Клонирование репозитория

```bash
# Клонировать приватный репозиторий
git clone git@github.com:FUYOH666/Scanovich.ai-audio-call.git ASR-4.5
cd ASR-4.5
```

---

## 🐍 Шаг 2: Установка Python зависимостей

```bash
# Создать виртуальное окружение
python3.12 -m venv venv

# Обновить pip
./venv/bin/python -m pip install --upgrade pip==25.2

# Установить зависимости
./venv/bin/pip install -r requirements.txt
```

**Ожидаемое время:** 5-10 минут (зависит от скорости интернета)

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
cp branches.yaml.example branches.yaml

# Отредактировать branches.yaml
nano branches.yaml
```

**Структура:**
```yaml
branches:
  - address: "ул. Республики д.196А"
    variants: ["республики 196а", "республики 196"]
    
admins:
  - canonical_name: "Арзу"
    variants: ["РУ", "РЗУ", "арз"]
```

---

## 🤖 Шаг 4: Установка VLLM сервера

### 4.1. Клонировать VLLM проект

```bash
cd /home/ai/Документы/
git clone https://github.com/vllm-project/vllm.git vLLm
cd vLLm
```

### 4.2. Установить VLLM

```bash
# Создать venv
python3.12 -m venv venv
./venv/bin/python -m pip install --upgrade pip

# Установить VLLM
./venv/bin/pip install vllm
```

### 4.3. Скачать модель Qwen3-30B

```bash
# Создать директорию для моделей
mkdir -p models

# Скачать модель (через huggingface-cli или wget)
huggingface-cli download Qwen/Qwen3-30B-A3B-Instruct-2507-AWQ-4bit --local-dir models/Qwen3-30B-A3B-Instruct-2507-AWQ-4bit
```

**Ожидаемое время:** 30-60 минут (модель ~15GB)

---

## 🔍 Шаг 5: Проверка установки

```bash
cd /home/ai/Документы/ScanovichAI/ASR-4.5

# Проверить здоровье системы
./venv/bin/python main.py health
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
cd /home/ai/Документы/vLLm
./venv/bin/python -m vllm.entrypoints.openai.api_server \
    --model models/Qwen3-30B-A3B-Instruct-2507-AWQ-4bit \
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
cd /home/ai/Документы/ScanovichAI/ASR-4.5

# Запустить daemon
./venv/bin/python main.py run
```

**Остановка:** `Ctrl+C`

### Вариант B: Systemd сервисы (для 24/7 работы)

```bash
cd /home/ai/Документы/ScanovichAI/ASR-4.5

# 1. Установить все сервисы
sudo ./systemd/install_all_services.sh

# 2. Запустить VLLM
sudo systemctl start vllm.service

# 3. Запустить ASR
sudo systemctl start asr-watcher.service

# 4. Проверить статус
sudo systemctl status vllm.service asr-watcher.service
```

**Мониторинг логов:**
```bash
# VLLM
journalctl -u vllm.service -f

# ASR
journalctl -u asr-watcher.service -f
```

---

## 📥 Шаг 7: Настройка загрузчиков аудиозвонков (опционально)

Если у вас есть АТС с записями звонков:

```bash
# 1. Клонировать проект загрузчиков
cd /home/ai/Документы/ScanovichAI/
git clone <ваш-репо-загрузчиков> Calls-downloader

# 2. Настроить каждый загрузчик
cd Calls-downloader/SvyazTransit-Irkutsk
cp .env.example .env
nano .env  # Указать credentials АТС

# 3. Установить systemd сервисы
cd /home/ai/Документы/ScanovichAI/ASR-4.5
sudo systemctl start call-downloader-irkutsk.service
sudo systemctl start call-downloader-volgodonks.service
sudo systemctl start call-downloader-tymen.service
sudo systemctl start call-downloader-angarsk.service
```

---

## 🛡️ Шаг 8: Защита от автологаута (критично!)

```bash
cd /home/ai/Документы/ScanovichAI/ASR-4.5

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
./venv/bin/python main.py telegram-report --type daily

# Обновить Dashboard
./venv/bin/python main.py update-dashboard
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
cd /home/ai/Документы/vLLm
./venv/bin/pip uninstall vllm
./venv/bin/pip install vllm
```

### Проблема: Whisper не находит модель

**Решение:**
```bash
# Скачать модель вручную
./venv/bin/python -c "from faster_whisper import WhisperModel; WhisperModel('large-v3', device='cuda')"
```

### Проблема: Google Sheets ошибка доступа

**Решение:**
```bash
# Проверить credentials
cat credentials/google_credentials.json

# Проверить доступ
./venv/bin/python main.py test-sheets
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

## 📚 Дополнительные ресурсы

- **`PROJECT_OVERVIEW.md`** — полное описание проекта
- **`Бесперебойная работа.md`** — настройка systemd для 24/7
- **`README.md`** — основная документация
- **`systemd/README_SESSION_FIX.md`** — исправление проблем с сессией

---

## ✅ Чеклист готовности к production

- [ ] Python 3.12 установлен
- [ ] CUDA 12.4+ установлен
- [ ] GPU доступен (nvidia-smi)
- [ ] Репозиторий склонирован
- [ ] Зависимости установлены (requirements.txt)
- [ ] config.yaml настроен
- [ ] Google credentials добавлены
- [ ] branches.yaml настроен
- [ ] VLLM сервер запущен
- [ ] Whisper модель скачана
- [ ] `./venv/bin/python main.py health` проходит
- [ ] Systemd сервисы установлены
- [ ] Автологаут отключен
- [ ] Тестовый файл обработан успешно
- [ ] Telegram отчет отправлен
- [ ] Google Sheets обновлена

---

**© 2025 ScanovichAI | Aleksandr Mordvinov**
