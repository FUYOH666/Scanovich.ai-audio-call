# ASR Call Quality Analyzer

**Language:** [🇷🇺 Русский](README.md) | [🇬🇧 English](README_EN.md)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Platform: Linux](https://img.shields.io/badge/platform-Linux-lightgrey.svg)](https://github.com/FUYOH666/Scanovich.ai-audio-call)
[![Website](https://img.shields.io/badge/website-scanovich.ai-blue)](https://scanovich.ai)

**Production-ready система для автоматической транскрипции и анализа качества телефонных звонков**

---

## Краткое описание

ASR Call Quality Analyzer — это полностью автоматизированная система для анализа качества обслуживания клиентов по телефону. Система использует локальные модели AI (Whisper для транскрипции и LLM для анализа), обеспечивая 100% конфиденциальность данных и значительную экономию по сравнению с коммерческими решениями.

**Версия:** 4.5.0

**Для кого:** Медицинские центры, call-центры, ритейл, банки, образование — любой бизнес с телефонным обслуживанием клиентов.

---

## Проблемы, которые решает

### Основные проблемы:

1. **Отсутствие объективной оценки качества обслуживания** — ручная оценка звонков неэффективна и субъективна
2. **Высокая стоимость коммерческих решений** — внешние API стоят десятки тысяч долларов в год
3. **Риск утечки конфиденциальных данных** — использование внешних сервисов ставит под угрозу PII клиентов
4. **Недостаточная детализация аналитики** — отсутствие детальных метрик и рекомендаций для обучения персонала

### Примеры использования:

- **Медицинские центры:** контроль качества записи на прием, соблюдение скриптов консультации
- **Call-центры:** автоматическая оценка работы операторов, выявление типичных ошибок
- **Банки:** контроль продаж финансовых продуктов, анализ качества техподдержки
- **Ритейл:** оценка консультаций, анализ апсейл-метрик

---

## Возможности

### 🎯 Основной функционал

- ✅ **Автоматическая транскрипция** — Whisper (современные модели), RTF < 0.1 (в 10+ раз быстрее реального времени)
- ✅ **Анализ качества по 30 критериям** — объективная оценка от 0 до 100 баллов
- ✅ **Маскирование PII** — автоматическая защита персональных данных клиентов
- ✅ **Нормализация данных** — унификация адресов филиалов и имен администраторов
- ✅ **3-уровневая аналитика** — Telegram отчеты, Google Sheets Dashboard, CSV экспорт

### 📊 Аналитика и отчеты

- ✅ **Ежедневные Telegram отчеты** — автоматические сводки в 09:00
- ✅ **Еженедельные отчеты** — рейтинги администраторов и динамика
- ✅ **Google Sheets Dashboard** — временной ряд с апсейл-метриками
- ✅ **Детальная аналитика** — топ-3 ошибки, рейтинги филиалов, рекомендации

### 🔒 Безопасность и производительность

- ✅ **100% локально** — никаких внешних API, полный контроль данных
- ✅ **Production-ready** — systemd сервисы, graceful shutdown, error handling
- ✅ **Экономия $51K/год** — по сравнению с коммерческими решениями
- ✅ **Multi-format поддержка** — JSON/MP3/WAV/M4A (Asterisk, VoIP системы)

---

## Требования

### Аппаратные требования:

- **GPU:** NVIDIA GPU с 24GB+ VRAM (рекомендуется RTX 4090/5090 или аналоги)
- **RAM:** 16GB+
- **Диск:** 100GB+ свободного места
- **CUDA:** 12.0+ (для PyTorch)

### Программные требования:

- **OS:** Linux (Ubuntu 22.04+)
- **Python:** 3.12 (единственная поддерживаемая версия)
- **VLLM:** Запущен на порту 8000 с LLM моделью (рекомендуется 30B+ параметров для качества)
- **uv:** Менеджер пакетов (устанавливается автоматически)

---

## Установка

### Быстрая установка

```bash
# 1. Клонировать репозиторий
git clone git@github.com:FUYOH666/Scanovich.ai-audio-call.git ASR-4.5
cd ASR-4.5

# 2. Установить uv (если не установлен)
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"

# 3. Синхронизировать зависимости
uv sync

# 4. Скопировать примеры конфигураций
cp config.example.yaml config.yaml
cp branches.example.yaml branches.yaml

# 5. Настроить config.yaml
# Отредактируйте config.yaml: укажите Telegram chat_id, Google Sheets ID и т.д.

# 6. Проверить установку
uv run python main.py health
```

**Ожидаемый вывод:**
```
✓ Config валиден
✓ GPU: NVIDIA GPU доступен
✓ VLLM доступен
✓ Telegram бот активен
✓ Google Sheets доступна
```

### Установка systemd сервисов (для 24/7 работы)

```bash
# 1. Установить все сервисы
sudo ./systemd/install_all_services.sh

# 2. Запустить сервисы
sudo systemctl start vllm.service
sudo systemctl start asr-watcher.service

# 3. Проверить статус
sudo systemctl status vllm.service asr-watcher.service
```

**Подробнее:** См. `DEPLOYMENT_GUIDE.md`

---

## Использование

### Быстрый запуск

```bash
# Запуск daemon в режиме 24/7
uv run python main.py run

# Остановка: Ctrl+C (graceful shutdown)
```

### Основные CLI команды

#### Транскрибация:
```bash
uv run python main.py run              # Daemon 24/7 (главный режим)
uv run python main.py process-file input/звонок.mp3  # Обработка одного файла
uv run python main.py health           # Диагностика системы
uv run python main.py metrics          # Статистика обработки
```

#### Анализ качества:
```bash
uv run python main.py analyze-quality  # Анализ одного звонка (30 критериев)
uv run python main.py analyze-batch    # Пакетный анализ всех транскрипций
uv run python main.py report           # Отчёт по администратору (Markdown)
```

#### Аналитика:
```bash
uv run python main.py aggregate        # Генерация витрин (day/week)
uv run python main.py telegram-report  # Отправка в Telegram (daily/weekly)
uv run python main.py export-csv       # Экспорт ошибок в CSV
```

#### Google Sheets:
```bash
uv run python main.py sync-sheets      # Батчевая синхронизация
uv run python main.py update-dashboard # Обновление Dashboard за день
uv run python main.py test-sheets      # Проверка доступа
```

Полный список команд: см. `main.py --help`

---

## Конфигурация

### Основной конфиг (config.yaml)

Основные параметры уже настроены оптимально для современных GPU с 24GB+ VRAM.

**Что можно настроить:**
- `analytics.telegram.chat_id` — ваш Telegram chat ID
- `analytics.telegram.enabled` — включить/выключить Telegram отчёты
- `google_sheets.spreadsheet_id` — ID вашей Google таблицы
- `google_sheets.enabled` — включить/выключить Google Sheets sync

**Создание config.yaml:**
```bash
cp config.example.yaml config.yaml
# Отредактируйте config.yaml под ваш бизнес
```

### Нормализация адресов и админов (branches.yaml)

```yaml
branches:
  - address: "Street Example, Building 123"
    variants: ["street example 123", "street example", "avenue example"]
    
admins:
  - canonical_name: "Admin Name"
    variants: ["variant1", "variant2", "variant3"]
```

**Создание branches.yaml:**
```bash
cp branches.example.yaml branches.yaml
# Заполните реальными адресами филиалов и именами администраторов
```

---

## Документация

### Основная документация:

- **`README.md`** — это руководство
- **`DEPLOYMENT_GUIDE.md`** — полное руководство по развертыванию
- **`PROJECT_OVERVIEW.md`** — описание проекта, технологий, архитектуры
- **`CHANGELOG.md`** — история изменений
- **`SECURITY.md`** — политика безопасности
- **`CONTRIBUTING.md`** — руководство для контрибьюторов

### Скрипты оценки:

- **`script_evaluation_template_a.md`** — шаблон оценки Template A (расширенный)
- **`script_evaluation_template_b.md`** — шаблон оценки Template B (стандартный)

### Конфигурация:

- **`config.example.yaml`** — пример конфигурации
- **`branches.example.yaml`** — пример нормализации адресов и админов

---

## Contributing

Спасибо за интерес к проекту! Мы открыты для вклада от сообщества.

### Как внести вклад:

1. **Fork & Clone** — форкните репозиторий и клонируйте
2. **Создайте feature branch** — `git checkout -b feature/your-feature`
3. **Внесите изменения** — следуйте стилю кода (ruff, pyright)
4. **Добавьте тесты** — для новой функциональности
5. **Проверьте безопасность** — запустите `./check_before_commit.sh`
6. **Создайте Pull Request** — опишите изменения подробно

**Подробнее:** См. `CONTRIBUTING.md`

---

## Лицензия

Этот проект распространяется под лицензией MIT. См. файл `LICENSE` для подробностей.

**Copyright (c) 2025 Aleksandr Mordvinov (ScanovichAI)**

---

## Коммерческая поддержка и услуги

### Профессиональные услуги

Этот проект является open-source решением, демонстрирующим возможности автоматизации анализа качества звонков. Для коммерческого внедрения и кастомизации доступны следующие услуги:

#### 🔧 Консультация и настройка
- Анализ ваших бизнес-процессов и требований
- Подбор оптимальной конфигурации под вашу инфраструктуру
- Настройка скриптов оценки под ваши стандарты качества

#### 🚀 Развертывание и интеграция
- Установка и настройка на вашей инфраструктуре
- Интеграция с вашей АТС, CRM, системами аналитики
- Настройка интеграций с Telegram, Google Sheets, другими системами

#### 📚 Обучение и поддержка
- Обучение вашей команды работе с системой
- Техническая поддержка и консультации
- Обновления и развитие функциональности

#### 🏢 Enterprise решения
- Multi-tenant архитектура для больших организаций
- Кастомные аналитические дашборды
- Расширенная интеграция с корпоративными системами
- SLA и гарантии доступности

### Почему стоит выбрать эту систему:

- ✅ **100% локально** — все данные остаются у вас, никаких внешних API
- ✅ **Экономия** — значительная экономия по сравнению с коммерческими решениями
- ✅ **Масштабируемость** — от 10K до 100K+ звонков/месяц на одном GPU
- ✅ **Гибкость** — легко адаптируется под любую отрасль и бизнес-процессы
- ✅ **Production-ready** — проверенная архитектура, работающая 24/7

**💼 Для коммерческих запросов:** посетите [scanovich.ai](https://scanovich.ai) для получения подробной информации о коммерческих услугах, ценах и условиях сотрудничества.

---

## Производительность

### Производительность:

- **Пропускная способность:** до 100K+ звонков/месяц на одном GPU
- **Скорость обработки:** RTF < 0.1 (в 10+ раз быстрее реального времени)
- **Точность:** объективная оценка по 30 настраиваемым критериям
- **Стабильность:** production-ready, работает 24/7

### Экономика:

- **Стоимость:** $0 при локальном развертывании
- **Экономия:** значительная экономия по сравнению с коммерческими API решениями
- **ROI:** быстрая окупаемость при использовании собственной инфраструктуры

---

## Структура проекта

```
ASR-4.5/
├── src/                    # Исходный код (21 модуль, ~6100 строк)
│   ├── asr.py              # Whisper Large V3 транскрипция
│   ├── vllm_postprocessor.py   # LLM маскирование + нормализация
│   ├── quality_analyzer.py     # Анализ 30 критериев
│   ├── db_manager.py           # SQLite БД
│   ├── analytics_aggregator.py # Витрины day/week + апсейл
│   ├── dashboard_generator.py  # Генератор Dashboard строк
│   ├── telegram_reporter.py   # Telegram отчёты
│   ├── google_sheets_integrator.py  # Google Sheets
│   ├── branches_manager.py     # Нормализация филиалов/админов
│   ├── daemon_watcher.py      # Главный daemon (watchdog)
│   └── ... (12 других модулей)
├── tests/                  # Тесты
├── input/                  # Входящие аудио (.mp3, .wav, .m4a)
├── output/                 # Транскрипции (.txt)
├── metadata/               # Классификация (JSON)
├── quality_analysis/       # Оценки качества (JSON)
├── analytics/              # SQLite БД + витрины
├── archive/                # Обработанные аудио (30 дней)
├── quarantine/             # Битые/проблемные файлы
├── logs/                   # Логи системы
├── credentials/            # Google Sheets credentials
├── systemd/                # Systemd сервисы
├── pyproject.toml          # Конфигурация проекта (uv)
├── uv.lock                # Зафиксированные зависимости
├── uv.toml                # Конфигурация uv (PyTorch index)
├── config.example.yaml    # Пример конфигурации
├── branches.example.yaml   # Пример нормализации
├── main.py                 # CLI (18 команд)
└── README.md               # Эта документация
```

---

## Troubleshooting

### VLLM недоступен
```bash
uv run python main.py health
# Проверьте: curl http://localhost:8000/v1/models
```

### Telegram не отправляется
```bash
# Проверьте chat_id в config.yaml
uv run python main.py telegram-report --type daily
```

### Google Sheets ошибка доступа
```bash
uv run python main.py test-sheets
# Проверьте credentials/google_credentials.json
```

### Dashboard не обновляется
```bash
# Ручное обновление для проверки
uv run python main.py update-dashboard

# Проверка автоматического планировщика (23:00)
# Смотрите logs/asr-watcher.log
```

**Подробнее:** См. раздел Troubleshooting в `DEPLOYMENT_GUIDE.md`

---

## Тестирование

```bash
# Запуск тестов
uv run pytest tests/

# С покрытием
uv run pytest tests/ --cov=src --cov-report=html
```

**Покрытие:**
- ✅ test_config_validation.py
- ✅ test_vllm_postprocessor.py
- ✅ test_cleanup.py

---

## Архитектура

### Главный Pipeline:

1. **Watchdog** — мониторинг input/ (inotify events)
2. **Worker Queue** — обработка файлов (последовательно)
3. **ASR** — транскрибация (Whisper)
4. **VLLM** — маскирование + классификация (LLM модель)
5. **Quality** — анализ качества (30 критериев)
6. **Analytics** — сохранение в SQLite
7. **Sheets** — real-time обновление Google Sheets

### Планировщики (daemon threads):

- **03:00** — автоочистка archive/ (30 дней ротация)
- **23:00** — батчевая синхронизация + обновление Dashboard
- **09:00** — Telegram daily отчет
- **Пн 10:00** — Telegram weekly отчет

---

---

## Контакты

**Автор:** Aleksandr Mordvinov (ScanovichAI)

**Для коммерческих запросов:**
- 🌐 **Website:** [scanovich.ai](https://scanovich.ai)
- 💬 **Telegram:** [@ScanovichAI](https://t.me/ScanovichAI)
- 📧 **Email:** iamfuyoh@gmail.com

**Для open-source вопросов:**
- 🐙 **GitHub:** [@FUYOH666](https://github.com/FUYOH666) - создавайте issues в репозитории

---

**© 2025 ASR Call Quality Analyzer | [ScanovichAI](https://scanovich.ai)**

**Этот проект является open-source демонстрацией возможностей автоматизации анализа качества звонков. Для коммерческого внедрения и кастомизации обращайтесь через [официальный сайт](https://scanovich.ai).**
