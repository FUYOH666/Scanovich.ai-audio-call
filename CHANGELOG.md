# Changelog

All notable changes are documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed
- `README.md`, `PROJECT_OVERVIEW.md`, `docs/FAQ.md`, `FUNDING.md` — clarify that the shipped stack is a demonstration configuration for a specific telephony profile; ASR quality depends on model, language, and audio; contact path for customization

## [5.2.1] - 2026-06-12

### Added
- `docs/assets/` — README screenshots (`web-ui-overview.png`, `web-ui-detail.png`) and `github-social-preview.png` with regen guide
- `docs/FAQ.md` — evaluator and operator FAQ
- Reader paths (Evaluator / Operator / Contributor) in `docs/README.md`

### Changed
- `README.md` — tier-1 EN storefront: hero, who-it's-for, quick start, doc lanes, release badge, screenshots
- `README_EN.md` — trimmed to deep CLI/config/troubleshooting reference (no duplicate landing)
- `PROJECT_OVERVIEW.md`, `docs/EVALUATION_GUIDE.md`, `docs/examples/README.md`, `CONTRIBUTING.md`, `DEPLOYMENT_GUIDE.md`, `docs/ARCHITECTURE.md` — aligned with new doc structure
- `pyproject.toml` — Ruff config migrated to `[tool.ruff.lint]` (fixes Cursor/VS Code Ruff extension workspace errors)

## [5.2.0] - 2026-06-12

### Added
- `docs/reviews/STAFF_REVIEW_2026-06.md` — full staff review, tech-delta matrix, and deferred GPU upgrade notes
- Minimal first-run documentation in `README.md` and `README_EN.md` — disable Telegram and Google Sheets while keeping ASR → LLM → local artifacts
- WSL2 deployment notes in `DEPLOYMENT_GUIDE.md` (experimental Windows path)
- Reverse-proxy note for upload rate limiting behind `X-Forwarded-For`

### Changed
- Version unified at **5.2.0** (`pyproject.toml`, `src/__init__.py`, FastAPI app metadata)
- CI: `actions/checkout@v6`, `astral-sh/setup-uv@v7` — apply manually on GitHub (workflow file requires `workflow` OAuth scope from local push)
- `pydantic` 2.10.3 → 2.12.5, `pydantic-settings` 2.6.1 → 2.7.1
- `pytest.ini` and `pyproject.toml` — exclude `voip/` from default collection to avoid import collisions
- `config.example.yaml` — minimal-mode header comment
- `docs/README.md`, `docs/ROADMAP.md` — linked staff review and marked minimal docs / WSL2 done

### Deferred (explicit)
- `torch` 2.5.1 → 2.10.0, `faster-whisper` 1.0.3 → 1.2.x, `openai` 1.54 → 2.x — require GPU / integration smoke on Linux before merge

## [5.1.0] - 2026-03-22

### Added
- `docs/PRODUCTIZATION_PLAN.md` — product audit, monetization model, prioritized backlog, and execution phases
- `docs/EVALUATION_GUIDE.md` — quick path for fit checks and first pilots before full deployment
- `FUNDING.md` — support, pilot, and sponsorship options that preserve the MIT open-source core
- `.github/ISSUE_TEMPLATE/bug_report.md`, `.github/ISSUE_TEMPLATE/feature_request.md` — GitHub issue templates for reproducible bugs and feature proposals
- `.github/pull_request_template.md` — lightweight PR checklist for summary, test plan, docs, and security review
- `src/pipeline_service.py` — shared single-file analysis pipeline reused by CLI and the new web layer
- `src/web/app.py` and `src/web/static/` — minimal FastAPI demo API and browser UI for single-file analysis
- `tests/test_api.py` — HTTP contract tests for `/healthz`, `/analyze`, upload validation, file-size limits, auth boundary, and safe 500 responses
- `tests/test_cli_web.py` — CLI tests for `main.py web` launch behavior and public-bind safety checks
- `GET /analyses` and `GET /analyses/{result_id}` in `src/web/app.py` — filesystem-backed history endpoints over persisted artifacts from `output/`, `metadata/`, and `quality_analysis/individual/`
- recent-analyses browser workflow in `src/web/static/` — users can reopen saved results without re-uploading the original file
- seeded history tests in `tests/test_api.py` — recent-list ordering, orphan artifact handling, detail retrieval, and API-key protection for saved results
- `docs/DEPLOYMENT_PROFILES.md` — operator-facing deployment profiles for all-local GPU, remote LLM, and future remote ASR
- `docs/PILOT_OUTREACH_PLAYBOOK.md` — solo-founder outreach and first-pilot conversation playbook
- `docs/WORKING_TOGETHER.md` — simple collaboration paths that preserve the open-source core
- `CODE_OF_CONDUCT.md` — public collaboration norms for contributors and discussions
- `.github/ISSUE_TEMPLATE/config.yml` — issue template routing with links for security reports and support paths
- `.github/FUNDING.yml`, `CODEOWNERS`, and `.github/dependabot.yml` — public community signals and lightweight maintenance automation
- `templates/script_evaluation_template_a.md` and `templates/script_evaluation_template_b.md` — moved full evaluation templates out of the repository root

### Changed
- `README.md`, `README_EN.md`, `docs/README.md`, and `PROJECT_OVERVIEW.md` — linked evaluation, product strategy, and funding docs; added CI badge to public READMEs
- `README.md` — clarified hardware wording: 24GB+ VRAM recommended for large models, 8GB+ workable with smaller presets
- `CONTRIBUTING.md` — mentions GitHub templates for bug reports, feature requests, and pull requests
- `src/cli/commands.py` — `process-file` now uses the shared pipeline, `health` respects `asr.device`, and `test-sheets` uses Pydantic config fields correctly
- `src/config_validation.py` — quality-analysis directories are created only when the feature is enabled
- `docs/ARCHITECTURE.md`, `README.md`, and `README_EN.md` — document the new demo API/UI entrypoint and shared pipeline
- `src/web/app.py` — web layer now supports protected pilot deployments with optional `X-API-Key` and hides internal 500 details from clients
- `src/cli/commands.py`, `Dockerfile`, and `DEPLOYMENT_GUIDE.md` — aligned around `main.py web` and the pilot-ready web/API deployment story
- `config.example.yaml` and `.env.example` — added `web` settings for host, port, and optional API key protection
- `docs/ROADMAP.md`, `docs/EVALUATION_GUIDE.md`, `docs/examples/README.md`, and `FUNDING.md` — updated to reflect shipped API/UI MVP, pilot checklist, sample report flow, and stronger mission/sponsorship framing
- `.github/workflows/ci.yml` — added selective Ruff and pilot-ready web/API checks without enforcing full-tree linting
- `README.md`, `README_EN.md`, `DEPLOYMENT_GUIDE.md`, `docs/README.md`, `docs/ARCHITECTURE.md`, `docs/ROADMAP.md`, `docs/EVALUATION_GUIDE.md`, `docs/examples/README.md`, `FUNDING.md`, `config.example.yaml`, `.env.example`, and `docs/REMOTE_ASR_AND_LLM.md` — refreshed to match the shared pipeline, web/API entrypoint, recent-analyses flow, and current local-first deployment story
- `src/web/app.py`, `src/web/static/index.html`, `src/web/static/app.js`, and `src/web/static/styles.css` — added rate limiting for uploads, history search/filter/pagination, and a clearer operator-facing detail summary
- `tests/test_api.py` — added coverage for upload rate limits and recent-analysis filtering/pagination
- `DEPLOYMENT_GUIDE.md`, `docs/ROADMAP.md`, `docs/EVALUATION_GUIDE.md`, and `FUNDING.md` — aligned with pilot hardening, deployment profiles, outreach, and collaboration model
- `README.md`, `README_EN.md`, `docs/README.md`, `PROJECT_OVERVIEW.md`, `CONTRIBUTING.md`, `SECURITY.md`, and `pyproject.toml` — aligned around a cleaner public entrypoint, consistent project naming, stronger community links, and less public-facing drift
- `config.example.yaml`, `src/config_validation.py`, `tests/test_script_parser.py`, and `templates/README.md` — updated for the new `templates/` locations of the full script evaluation templates
- `.github-topics.txt` — trimmed niche topics and aligned discovery tags with the current public product surface

## [5.0.2] - 2026-03-22

### Added
- `.github/workflows/ci.yml` — `pytest` on push/PR to `main`/`master` (ruff on full tree deferred: legacy Cyrillic strings in CLI)
- `docs/ARCHITECTURE.md` — focused pipeline and module map
- `docs/ROADMAP.md` — consolidated backlog (replaces root `next_steps.md`)
- `docs/README.md` — index of technical docs
- `src/cli/` — Click CLI implementation moved out of root `main.py` (`commands.py` + `__init__.py`)

### Removed
- Portfolio / generic marketing Markdown under `docs/` (`ocr-automation-overview`, `healthcare-solutions`, `voice-analytics-overview`, `architecture-guide`, duplicate `production-deployment.md`)
- Root `next_steps.md` (content merged into `docs/ROADMAP.md`)

### Changed
- `PROJECT_OVERVIEW.md` shortened to a summary with links (full pitch belongs on the website)
- `DEPLOYMENT_GUIDE.md` — correct clone URL, Docker section, VoIP paths under `voip/`, quarantine note
- `CommercialLLMAnalyzer` renamed to `OpenRouterAnalyzer` in `quality_analyzer.py` (cloud OpenAI-compatible path)
- User-facing strings: prefer “Call Analytics Platform” and package version via `importlib.metadata`
- `Dockerfile` labels aligned with package version

## [5.0.1] - 2026-03-22

### Added
- `docs/examples/` — synthetic sample transcript and quality JSON for onboarding ([`docs/examples/README.md`](docs/examples/README.md))
- `docs/REMOTE_ASR_AND_LLM.md` — remote OpenAI-compatible LLM and CPU/small-model ASR notes
- `templates/generic_sales_support.md` — 10-criteria starter evaluation template for generic sales/support calls
- `config.generic.example.yaml` — analytics criteria aligned with the generic template
- `templates/README.md` — index of evaluation templates
- `tests/test_script_parser.py` — regression tests for script Markdown parsing

### Changed
- `.gitignore` — exceptions so synthetic `docs/examples/*.txt` and `*.json` can be versioned (still excludes real `output/` / `metadata/` data)
- `ScriptParser` in `quality_analyzer.py` accepts both legacy headings (`### Основные сущности`, …) and the headings used in shipped templates (`### Основные критерии оценки`, `### Дополнительные критерии`)
- `README.md`, `README_EN.md` — pipeline diagram (Mermaid), links to examples, generic template, telephony/resampling note, remote LLM doc
- `PROJECT_OVERVIEW.md` — correct GitHub URL, author, MIT alignment (removed conflicting proprietary footer)
- `.github-topics.txt` — extra discovery topics (`self-hosted`, `vllm`, `telephony`, …)

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

