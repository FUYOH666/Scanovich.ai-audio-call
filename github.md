# GitHub Repository Best Practices

**Универсальная инструкция по оформлению репозиториев на GitHub**

---

## 📝 About секция (метаданные)

### Description
- **Длина:** до 160 символов
- **Формат:** краткое описание функциональности + ключевые технологии
- **Пример:** `Production-ready система автоматической транскрипции и анализа качества телефонных звонков. Whisper, LLM, локальное развертывание.`

### Website
- Указывать если есть: `https://scanovich.ai`
- Если нет — оставить пустым

### Topics (5-15 тегов)
**Категории:**
1. **Язык:** `python`, `javascript`, `typescript`, `go`, `rust`
2. **Тип:** `cli`, `library`, `web-app`, `api`, `tool`
3. **Технологии:** `react`, `fastapi`, `docker`, `kubernetes`
4. **Назначение:** `automation`, `machine-learning`, `data-processing`
5. **Платформа:** `linux`, `macos`, `windows`, `cross-platform`
6. **Особенности:** `open-source`, `mit-license`, `production-ready`

**Правила:**
- Используйте популярные теги (проверяйте на GitHub)
- Комбинируйте общие и специфичные
- Избегайте уникальных/длинных тегов

---

## 📄 README.md - Стандартная структура

```markdown
# Project Name

[![License](badge)](link)
[![Language](badge)](link)
[![Platform](badge)](link)

**Краткое описание (1-2 предложения)**

---

## Краткое описание
Что делает проект, для кого предназначен.

## Проблемы, которые решает (опционально)
Конкретные проблемы и примеры использования.

## Возможности
- ✅ Функция 1
- ✅ Функция 2

## Требования
- Версии языков/инструментов
- Зависимости

## Установка
```bash
# Пошаговые команды
```

## Использование
```bash
# Примеры команд
```

## Конфигурация (если нужно)
Описание конфигурационных файлов и примеры.

## Документация
Ссылки на подробную документацию.

## Contributing
Как внести вклад (или ссылка на CONTRIBUTING.md).

## Лицензия
Тип лицензии и ссылка на LICENSE.

## Контакты
**Автор:** Имя (ScanovichAI)

**Для коммерческих запросов:**
- 🌐 **Website:** [scanovich.ai](https://scanovich.ai)
- 💬 **Telegram:** [@ScanovichAI](https://t.me/ScanovichAI)
- 📧 **Email:** iamfuyoh@gmail.com

**Для open-source вопросов:**
- 🐙 **GitHub:** [@FUYOH666](https://github.com/FUYOH666) - создавайте issues

---

**© 2025 Project Name | [ScanovichAI](https://scanovich.ai)**
```

### Badge'ы (опционально)
```markdown
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Platform: Linux](https://img.shields.io/badge/platform-Linux-lightgrey.svg)](https://github.com/USER/REPO)
[![Website](https://img.shields.io/badge/website-scanovich.ai-blue)](https://scanovich.ai)
```

**Генератор:** https://shields.io/

---

## 📋 Обязательные файлы

### Базовые
- `README.md` — основная документация
- `LICENSE` — лицензия (MIT для open-source)
- `.gitignore` — исключения для git

### Рекомендуемые
- `CHANGELOG.md` — история изменений (формат: [Keep a Changelog](https://keepachangelog.com/))
- `CONTRIBUTING.md` — руководство для контрибьюторов
- `SECURITY.md` — политика безопасности
- `.github/` — workflows, templates, issues

### Конфигурационные (по типу проекта)
- `pyproject.toml` — Python (PEP 621)
- `package.json` — Node.js
- `Cargo.toml` — Rust
- `go.mod` — Go

---

## 🏷️ Версионирование (SemVer)

**Формат:** `MAJOR.MINOR.PATCH`

- **MAJOR** — breaking changes
- **MINOR** — новая функциональность (обратная совместимость)
- **PATCH** — исправления багов

**Git Tags:**
```bash
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

---

## 📝 CHANGELOG.md

```markdown
# Changelog

## [1.0.0] - 2025-11-04

### Added
- Новая функция X

### Changed
- Улучшена производительность

### Fixed
- Исправлен баг Z

### Removed
- Удалена устаревшая функция

[1.0.0]: https://github.com/USER/REPO/compare/v0.9.0...v1.0.0
```

---

## 🔒 Безопасность

### ❌ НЕ коммитить:
- Секреты (API keys, токены, пароли)
- Персональные данные (PII)
- Конфигурации с секретами
- Временные файлы
- Большие бинарные файлы

### ✅ Добавить в .gitignore:
```
.env, .env.*
*.key, *.pem, *.crt
venv/, .venv/, __pycache__/
node_modules/, dist/, build/
*.log, *.tmp, .DS_Store
```

### Проверка перед коммитом:
```bash
# Проверить на секреты
./check_before_commit.sh  # если есть скрипт
git diff --cached | grep -iE "password|token|secret|key"
```

---

## 🌟 GitHub Features

### Issues
- Используйте шаблоны (`.github/ISSUE_TEMPLATE/`)
- Добавляйте labels (bug, feature, enhancement)
- Привязывайте к PR через `Fixes #123`

### Pull Requests
- Подробное описание изменений
- Ссылки на связанные issues
- Скриншоты/примеры если нужно

### Releases
- Создавать через GitHub Releases
- Привязывать к git tags
- Добавлять release notes
- Прикреплять артефакты сборки

### GitHub Actions (CI/CD)
- Тесты, линтинг, проверка типов
- Автоматические релизы
- Пример: `.github/workflows/ci.yml`

---

## 🔧 Автоматизация

### GitHub CLI (gh)
```bash
# Обновить описание
gh repo edit USER/REPO --description "Описание"

# Добавить topics
gh repo edit USER/REPO --add-topic python --add-topic automation

# Создать release
gh release create v1.0.0 --title "Version 1.0.0" --notes "Release notes"
```

### GitHub API
```bash
# Обновить описание
curl -X PATCH https://api.github.com/repos/USER/REPO \
  -H "Authorization: token TOKEN" \
  -d '{"description":"Описание"}'

# Обновить topics
curl -X PUT https://api.github.com/repos/USER/REPO/topics \
  -H "Authorization: token TOKEN" \
  -H "Accept: application/vnd.github.mercy-preview+json" \
  -d '{"names":["tag1","tag2"]}'
```

---

## ✅ Quick Checklist

Перед публикацией репозитория:

- [ ] **About секция:** описание, website, topics (5-15)
- [ ] **README.md:** полная структура, примеры использования
- [ ] **LICENSE:** файл добавлен (MIT для open-source)
- [ ] **.gitignore:** настроен правильно, секреты исключены
- [ ] **CHANGELOG.md:** создан (если проект активно развивается)
- [ ] **CONTRIBUTING.md:** создан (если принимаете вклад)
- [ ] **SECURITY.md:** создан (если обрабатываете данные)
- [ ] **Badge'ы:** добавлены (опционально)
- [ ] **CI/CD:** настроен (опционально, но рекомендуется)
- [ ] **Контакты:** единый блок в конце README (без дублирования)

---

## 📚 Полезные ссылки

- **GitHub Docs:** https://docs.github.com/
- **Shields.io:** https://shields.io/ (badge генератор)
- **Semantic Versioning:** https://semver.org/
- **Keep a Changelog:** https://keepachangelog.com/
- **Choose a License:** https://choosealicense.com/

---

## 👤 Стандартные контакты для всех проектов

**Для коммерческих запросов:**
- 🌐 **Website:** [scanovich.ai](https://scanovich.ai)
- 💬 **Telegram:** [@ScanovichAI](https://t.me/ScanovichAI)
- 📧 **Email:** iamfuyoh@gmail.com

**Для open-source вопросов:**
- 🐙 **GitHub:** [@FUYOH666](https://github.com/FUYOH666) - создавайте issues в репозитории

---

**Последнее обновление:** 2025-11-04
