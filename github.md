# GitHub Repository Best Practices

<i>Универсальный свод правил для оформления репозиториев на GitHub</i>

---

## 📝 About секция (метаданные репозитория)

### Description (описание)

**Формат:**
- Краткое описание (до 160 символов)
- Указывает основную функцию/назначение проекта
- Использует ключевые слова для поиска
- Можно добавить поддерживаемые платформы/технологии

**Примеры:**
```
✅ Python библиотека для работы с API: асинхронные запросы, кэширование, retry логика. Простая интеграция.
✅ Веб-приложение для управления задачами: React, FastAPI, PostgreSQL. Drag-and-drop интерфейс.
✅ CLI инструмент для автоматизации: обработка файлов, интеграции с сервисами. Кроссплатформенный.
```

**Плохие примеры:**
```
❌ Моя программа
❌ Проект для курса
❌ Тестовый репозиторий
```

### Website (веб-сайт)

- Если есть отдельный сайт проекта — указывайте его
- Если нет — можно оставить пустым или указать ссылку на репозиторий
- Для документации — ссылка на GitHub Pages или другой хостинг

### Topics (теги)

**Количество:** 5-15 тегов оптимально

**Категории тегов:**

1. **Язык программирования:**
   - `python`, `javascript`, `typescript`, `go`, `rust`, `java`, `cpp`

2. **Тип проекта:**
   - `cli`, `library`, `framework`, `web-app`, `api`, `tool`, `script`

3. **Технологии/фреймворки:**
   - `react`, `fastapi`, `django`, `flask`, `vue`, `nextjs`
   - `docker`, `kubernetes`, `aws`, `terraform`

4. **Назначение:**
   - `automation`, `security-audit`, `data-processing`
   - `machine-learning`, `web-scraping`, `monitoring`

5. **Платформы:**
   - `macos`, `linux`, `windows`, `cross-platform`

6. **Особенности:**
   - `open-source`, `mit-license`, `cli-tool`
   - `pydantic`, `typer`, `rich` (если используете)

**Правила:**
- Используйте общепринятые теги (легче найти)
- Комбинируйте общие и специфичные теги
- Избегайте слишком длинных или уникальных тегов
- Проверяйте популярность тега на GitHub перед использованием

---

## 📄 README.md

### Структура README

1. **Заголовок с badge'ами**
   ```markdown
   # Project Name
   
   [![Language](badge-url)](link)
   [![License](badge-url)](link)
   [![Platform](badge-url)](link)
   ```

2. **Краткое описание** (1-2 предложения)
   - Что делает проект
   - Для кого предназначен

3. **Проблемы, которые решает** (опционально)
   - Конкретные проблемы
   - Примеры использования

4. **Возможности** (Features)
   - Список ключевых функций
   - Используйте эмодзи для визуального разделения

5. **Требования**
   - Версии языков/инструментов
   - Зависимости

6. **Установка**
   - Пошаговые инструкции
   - Примеры команд

7. **Использование**
   - Примеры команд
   - Примеры кода

8. **Конфигурация** (если нужно)
   - Описание конфигурационных файлов
   - Примеры

9. **Документация**
   - Ссылки на подробную документацию
   - API reference

10. **Contributing**
    - Как внести вклад
    - Требования к коду

11. **Лицензия**
    - Тип лицензии
    - Ссылка на LICENSE файл

12. **Автор/Контакты**
    - Информация об авторе
    - Способы связи

### Badge'ы

**Популярные сервисы:**
- **Shields.io** — https://shields.io/
- **GitHub Badges** — стандартные badge'ы GitHub

**Примеры:**
```markdown
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Linux-lightgrey.svg)](https://github.com/user/repo)
```

---

## 📋 Структура файлов

### Обязательные файлы

- `README.md` — основная документация
- `LICENSE` — лицензия проекта
- `.gitignore` — исключения для git
- `CHANGELOG.md` — история изменений (рекомендуется)

### Конфигурационные файлы

- `pyproject.toml` — для Python проектов
- `package.json` — для Node.js проектов
- `Cargo.toml` — для Rust проектов
- `go.mod` — для Go проектов
- `requirements.txt` — для Python (если не используется pyproject.toml)

### Дополнительные файлы

- `CONTRIBUTING.md` — руководство для контрибьюторов
- `CODE_OF_CONDUCT.md` — кодекс поведения
- `SECURITY.md` — политика безопасности
- `.github/` — GitHub workflows, templates, issues

---

## 🏷️ Версионирование

### Semantic Versioning (SemVer)

Формат: `MAJOR.MINOR.PATCH`

- **MAJOR** — несовместимые изменения API
- **MINOR** — новая функциональность с обратной совместимостью
- **PATCH** — исправления багов с обратной совместимостью

**Примеры:**
- `1.0.0` — первый стабильный релиз
- `1.1.0` — добавлена новая функция
- `1.1.1` — исправлен баг
- `2.0.0` — breaking changes

### Git Tags

```bash
# Создать тег
git tag -a v1.0.0 -m "Release version 1.0.0"

# Push тега
git push origin v1.0.0

# Push все теги
git push origin --tags
```

---

## 📝 CHANGELOG.md

### Формат

```markdown
# Changelog

## [1.0.0] - 2025-11-04

### Added
- Новая функция X
- Поддержка платформы Y

### Changed
- Улучшена производительность
- Обновлен API

### Fixed
- Исправлен баг Z

### Removed
- Удалена устаревшая функция

[1.0.0]: https://github.com/user/repo/compare/v0.9.0...v1.0.0
```

---

## 🔒 Безопасность

### Не коммитить в репозиторий:

- ❌ Секреты (API keys, токены, пароли)
- ❌ Персональные данные
- ❌ Конфигурационные файлы с секретами
- ❌ Временные файлы
- ❌ Большие бинарные файлы

### Добавить в .gitignore:

- `.env`, `.env.local`
- `*.key`, `*.pem`
- `node_modules/`, `__pycache__/`
- `.venv/`, `venv/`
- `*.log`
- `dist/`, `build/`

---

## 🌟 GitHub Features

### Issues

- Используйте шаблоны для issues
- Добавляйте labels (bug, feature, enhancement)
- Привязывайте issues к PR через `Fixes #123`

### Pull Requests

- Описывайте изменения подробно
- Ссылайтесь на связанные issues
- Добавляйте скриншоты/примеры если нужно
- Проверяйте перед merge

### Releases

- Создавайте релизы через GitHub Releases
- Привязывайте к git tags
- Добавляйте release notes
- Прикрепляйте артефакты сборки

### GitHub Actions

- Настройте CI/CD для автоматических проверок
- Тесты, линтинг, проверка типов
- Автоматические релизы

---

## 📊 Статистика и метрики

### Что делает репозиторий привлекательным:

- ✅ Четкое описание
- ✅ Хорошая документация
- ✅ Активные issues и PR
- ✅ Регулярные коммиты
- ✅ Звезды и форки
- ✅ CI/CD настроен
- ✅ Примеры использования

---

## 🎯 Quick Checklist

Перед публикацией репозитория:

- [ ] Описание в About секции заполнено
- [ ] Topics добавлены (5-15 тегов)
- [ ] README.md содержит всю необходимую информацию
- [ ] LICENSE файл добавлен
- [ ] .gitignore настроен правильно
- [ ] Нет секретов в коде
- [ ] Нет временных файлов
- [ ] CHANGELOG.md создан (опционально)
- [ ] Примеры использования в README
- [ ] Badge'ы добавлены (опционально)

---

## 🔧 Автоматизация через GitHub API

### Обновление метаданных через API:

```bash
# Описание
curl -X PATCH https://api.github.com/repos/OWNER/REPO \
  -H "Authorization: token TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  -d '{"description":"Описание проекта"}'

# Topics
curl -X PUT https://api.github.com/repos/OWNER/REPO/topics \
  -H "Authorization: token TOKEN" \
  -H "Accept: application/vnd.github.mercy-preview+json" \
  -d '{"names":["tag1","tag2","tag3"]}'
```

### Через GitHub CLI (gh):

```bash
# Описание
gh repo edit OWNER/REPO --description "Описание"

# Topics
gh repo edit OWNER/REPO --add-topic tag1 --add-topic tag2
```

---

## 📚 Полезные ссылки

- **GitHub Docs**: https://docs.github.com/
- **Shields.io**: https://shields.io/
- **Semantic Versioning**: https://semver.org/
- **Keep a Changelog**: https://keepachangelog.com/
- **Choose a License**: https://choosealicense.com/

---

## 👤 Контакты автора

- **Сайт**: https://scanovich.ai
- **Telegram**: [@ScanovichAI](https://t.me/ScanovichAI)

---

<i>Последнее обновление: 2025-11-04</i>

