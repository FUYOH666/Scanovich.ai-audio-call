# 🚀 Quick Start Guide - ASR-4.5

## Быстрый запуск (5 минут)

### 1. Проверка окружения

```bash
cd /home/ai/Документы/ScanovichAI/ASR-4.5
./venv/bin/python main.py health
```

Должно вывести:
- ✓ Config валиден
- ✓ GPU: NVIDIA GeForce RTX 5090
- ✓ VLLM доступен

### 2. Тестирование на одном файле

```bash
./venv/bin/python main.py process-file input/19.10.2025_08-13-47_89025767786_Входящий.mp3
```

Результат:
- Транскрипция с маскированием PII
- Классификация звонка (тип, тональность, темы)
- Сохранённые данные: имя админа, адрес клиники

### 3. Запуск в production (daemon режим)

```bash
./venv/bin/python main.py run
```

Daemon будет:
- ✅ Мониторить `input/` на новые файлы
- ✅ Автоматически транскрибировать (Whisper Large V3)
- ✅ Постобрабатывать через VLLM (Qwen3-30B)
- ✅ Сохранять результаты в `output/` и `metadata/`
- ✅ Архивировать обработанные файлы
- ✅ Автоочистка каждый день в 03:00

**Остановка:** Ctrl+C (graceful shutdown, завершит обработку текущих файлов)

---

## Автозапуск через systemd

### Установка сервиса

```bash
sudo cp systemd/asr-watcher.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable asr-watcher
sudo systemctl start asr-watcher
```

### Мониторинг

```bash
# Статус
sudo systemctl status asr-watcher

# Логи в реальном времени
journalctl -u asr-watcher -f

# Перезапуск
sudo systemctl restart asr-watcher
```

---

## Результаты обработки

### Структура выходных файлов

```
output/
  └── 19.10.2025_08-13-47_89025767786_Входящий.txt    # Финальная транскрипция

metadata/
  └── 19.10.2025_08-13-47_89025767786_Входящий.json   # Классификация + метрики

archive/
  └── 2025-10/
      └── 19.10.2025_08-13-47_89025767786_Входящий.mp3  # Исходное аудио
```

### Пример metadata JSON

```json
{
  "filename": "19.10.2025_08-13-47_89025767786_Входящий.mp3",
  "processed_at": "2025-10-20 15:26:43",
  "classification": {
    "type": "запись_на_прием",
    "sentiment": "нейтральный",
    "key_topics": ["МСКТ", "подготовка", "цена"],
    "admin_name": "Дарья",
    "clinic_address": "улица Сверлова [ЧИСЛО]"
  },
  "asr_metrics": {
    "elapsed_time": 6.34,
    "audio_duration": 190.62,
    "rtf": 0.0333,
    "segment_count": 45
  }
}
```

---

## CLI Команды (шпаргалка)

| Команда | Описание |
|---------|----------|
| `health` | Диагностика: GPU, VLLM, конфиг, диск |
| `run` | Запуск daemon (непрерывная обработка) |
| `process-file <path>` | Обработать один файл (тестирование) |
| `cleanup` | Ручной запуск автоочистки |
| `metrics` | Статистика обработки |

---

## Производительность

**Измерено на RTX 5090 + Qwen3-30B:**

- **RTF:** 0.033 (30x быстрее реального времени)
- **Скорость:** 6 сек для 3-минутного звонка
- **Throughput:** ~40-50 файлов/час
- **GPU память:** ~30GB (Whisper + VLLM)

---

## Troubleshooting

### VLLM недоступен

```bash
# Проверить статус VLLM
curl http://localhost:8000/v1/models

# Если не работает - запустите VLLM сервер
```

### Диск заполнен

```bash
# Ручная очистка
./venv/bin/python main.py cleanup

# Проверить свободное место
df -h
```

### GPU занята

```bash
# Проверить GPU
nvidia-smi

# Освободить память (если нужно)
sudo systemctl restart asr-watcher
```

---

## Логи

```bash
# Основной лог
tail -f logs/asr-watcher.log

# Только ошибки
tail -f logs/errors.log

# Systemd логи
journalctl -u asr-watcher -f
```

---

## Контакты

**Author:** Aleksandr Mordvinov  
**Project:** ScanovichAI  
**Version:** 4.5.0

✅ Система готова к production использованию!

