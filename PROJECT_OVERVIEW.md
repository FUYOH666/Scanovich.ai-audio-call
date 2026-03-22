# Call Analytics Platform — обзор

**Автор:** Aleksandr Mordvinov (ScanovichAI)  
**Репозиторий:** [github.com/FUYOH666/Scanovich.ai-audio-call](https://github.com/FUYOH666/Scanovich.ai-audio-call)  
**Лицензия:** [MIT](LICENSE) (коммерческие услуги внедрения — отдельно, [scanovich.ai](https://scanovich.ai))

## Что это

Production-ориентированная система: **записи звонков** (VoIP или файлы) → **транскрипция** (Whisper / faster-whisper) → **постобработка и QA** (локальный LLM через OpenAI-compatible API) → **метрики, отчёты** (Telegram, Google Sheets, SQLite, CSV). Подходит для колл-центров, записи на услуги, техподдержки — при настройке критериев под ваш скрипт.

## Документация (один источник правды по разделам)

| Нужно | Файл |
|--------|------|
| Быстрый старт (EN) | [README.md](README.md) |
| Полное руководство (EN) | [README_EN.md](README_EN.md) |
| Развёртывание 24/7, systemd | [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) |
| Пайплайн и модули | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| Планы развития | [docs/ROADMAP.md](docs/ROADMAP.md) |
| Удалённый LLM / CPU ASR | [docs/REMOTE_ASR_AND_LLM.md](docs/REMOTE_ASR_AND_LLM.md) |
| Индекс docs | [docs/README.md](docs/README.md) |

## Технологии (кратко)

- Python 3.12, `uv`, Pydantic config  
- faster-whisper, PyTorch (CUDA на Linux)  
- LLM: vLLM или совместимый сервер; опционально облачный API для сравнения  
- Интеграции: Telegram, Google Sheets, загрузчики в `voip/`

## Исторический контекст

Система выросла из внедрения в сети приёмов с высоким потоком звонков: полный охват записей, объективные чеклисты качества, апсейл-метрики. Точные цифры и внутренние кейсы намеренно не дублируются здесь — для публичного репозитория важна **воспроизводимая** архитектура и документация.

## Roadmap и коммерция

- Идеи и чеклист: [docs/ROADMAP.md](docs/ROADMAP.md) и [Issues](https://github.com/FUYOH666/Scanovich.ai-audio-call/issues).  
- Кастомизация под отрасль, on-prem внедрение, поддержка: [scanovich.ai](https://scanovich.ai).

---

**© 2025 Aleksandr Mordvinov (ScanovichAI)**
