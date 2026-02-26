# Changelog

All notable changes are documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
[Semantic Versioning](https://semver.org/).

## [5.0.0] - 2026-02-26

### Added
- **VoIP integration** — Rostelcom and Svyaztransit downloaders merged into main repo
- **Hardware-based model selection** — `model_preset: "auto"` detects GPU VRAM and selects Whisper model (tiny → large-v3)
- **VoIP → ASR pipeline** — Downloaders write to `input/`; ASR daemon processes automatically
- `voip/rostelcom/` — CloudPBX Rostelecom call records downloader
- `voip/svyaztransit/` — Svyaztransit call records downloader
- `src/model_resolver.py` — GPU VRAM detection and model preset resolution
- English README as primary documentation

### Changed
- Project renamed to `call-analytics-platform`
- README restructured for end-to-end platform overview
- VoIP `.env.example`: `DOWNLOAD_DIR=../../input` for ASR integration
- `config.example.yaml`: added `model_preset` for hardware selection

## [4.5.1] - 2025-01-XX

### Added
- CI/CD workflow (`.github/workflows/ci.yml`) с автоматической проверкой кода
- Английская версия README (`README_EN.md`) для англоговорящих пользователей

### Changed
- Dockerfile переписан для использования `uv sync --frozen` вместо `pip install`
- Multi-stage build в Dockerfile для оптимизации размера образа
- Все ссылки на `venv` обновлены на `uv run` в документации и примерах
- Systemd сервисы обновлены для использования `uv` вместо `venv`

### Removed
- `requirements.txt` - заменен на `pyproject.toml` + `uv.lock`
- Примеры портфолио: `src/ai_service_example.py`, `src/data_processor_example.py`
- Тесты для примеров: `tests/test_ai_service.py`, `tests/test_data_processor.py`
- Временные файлы: `vc_post.md`, `vc_rules.md`, `github.md`
- `docker-compose.yml` - пример портфолио, не используется в production

### Fixed
- Обновлены все инструкции установки для использования `uv`
- Исправлены ссылки на удаленные файлы в документации
- Обновлены примеры команд в документации

## [4.5.0] - 2025-11-04

### Added
- Полная миграция на `uv` и `pyproject.toml` для управления зависимостями
- `uv.lock` как источник истины для детерминированной установки зависимостей
- Автоматическая генерация ежедневного Dashboard в Google Sheets с временным рядом
- Апсейл метрики: видеозаключение, допродажи, цена (%)
- Рейтинг администраторов и филиалов в Dashboard и Telegram отчетах
- Нормализация адресов и имен администраторов через `branches.yaml`
- Инструкция для менеджеров в Google Sheets (лист "📖 Инструкция")
- Поддержка JSON-wrapped MP3 файлов (Asterisk/VoIP системы)
- Автоматическое base64 декодирование для JSON-формата
- Система карантина для битых/проблемных файлов
- Восстановление файлов из карантина через `restore_from_quarantine.py`
- Health CLI команда для диагностики системы
- Метрики производительности через `metrics` команду
- CSV экспорт для глубокого анализа
- A/B тестирование моделей через `compare-models` команду
- Cost tracking для статистики токенов и стоимости
- Pre-commit hooks для проверки безопасности
- GitHub Actions CI/CD pipeline

### Changed
- Полная переработка системы управления зависимостями: переход с `requirements.txt` на `pyproject.toml` + `uv`
- Обновлены все инструкции по установке для использования `uv`
- Улучшена логика сравнения филиалов: при одинаковом ERR сравнение по среднему баллу
- Оптимизированы запросы к Google Sheets API для батчевой синхронизации
- Улучшена обработка ошибок и логирование
- Обновлена структура документации согласно стандартам GitHub

### Fixed
- Исправлена проблема с дубликатами в Google Sheets
- Улучшена обработка больших аудиофайлов
- Исправлена нормализация имен администраторов с вариантами
- Исправлена обработка edge cases в анализе качества
- Улучшена стабильность daemon режима

### Security
- Добавлена проверка безопасности перед коммитом (`check_before_commit.sh`)
- Добавлена финальная проверка безопасности (`check_security.sh`)
- Улучшена защита PII данных через маскирование
- Добавлены проверки на утечку секретов в CI/CD

## [4.0.0] - 2025-10-20

### Added
- Полная автоматизация pipeline обработки звонков
- Интеграция с Telegram для автоматических отчетов
- Интеграция с Google Sheets для Dashboard и детализации
- Анализ качества по 30 критериям через LLM-30B
- Маскирование PII данных через LLM
- SQLite база данных для аналитики ошибок
- Агрегация данных по дням и неделям
- CSV экспорт для анализа

### Changed
- Переход на Whisper Large V3 для транскрипции
- Использование локального LLM-30B вместо внешних API
- Оптимизация производительности ASR pipeline

---

## Формат версий

- **MAJOR** — несовместимые изменения API
- **MINOR** — новая функциональность с обратной совместимостью
- **PATCH** — исправления багов с обратной совместимостью

[4.5.1]: https://github.com/FUYOH666/Scanovich.ai-audio-call/compare/v4.5.0...v4.5.1
[4.5.0]: https://github.com/FUYOH666/Scanovich.ai-audio-call/releases/tag/v4.5.0
[4.0.0]: https://github.com/FUYOH666/Scanovich.ai-audio-call/releases/tag/v4.0.0

