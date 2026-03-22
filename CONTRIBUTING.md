# 🤝 Contributing to ASR Call Quality Analyzer

Спасибо за интерес к проекту! Я открыт для вклада от сообщества.

---

## 🎯 Как внести вклад

### 1. **Fork & Clone**
```bash
# Форкните репозиторий на GitHub
# Затем клонируйте свой fork
git clone git@github.com:YOUR_USERNAME/Scanovich.ai-audio-call.git
cd Scanovich.ai-audio-call
```

### 2. **Создайте feature branch**
```bash
git checkout -b feature/your-feature-name
```

### 3. **Установка зависимостей**
```bash
# Установить uv (если не установлен)
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"

# Синхронизировать зависимости
uv sync
```

### 4. **Внесите изменения**
- Следуйте стилю кода (ruff для форматирования и линтинга)
- Добавьте тесты для новой функциональности
- Обновите документацию
- Используйте `uv run` для запуска команд Python

### 4.1. **Использование библиотек и документация**

**Важно**: Перед использованием новых библиотек рекомендуется ознакомиться с их актуальной документацией и best practices.

**Ключевые библиотеки проекта:**
- **uv** - менеджер пакетов и окружений
- **pydantic** - валидация данных
- **pydantic-settings** - управление настройками
- **pytest** - тестирование
- **ruff** - линтинг и форматирование
- **pyright** - проверка типов
- **bandit** - безопасность

**Рекомендации:**
- ✅ Изучайте официальную документацию перед использованием библиотек
- ✅ Следуйте best practices из документации
- ✅ Проверяйте актуальность версий и API
- ✅ Используйте примеры из официальных источников

### 5. **Проверьте безопасность**
```bash
# ОБЯЗАТЕЛЬНО перед коммитом!
./check_before_commit.sh
```

### 6. **Commit & Push**
```bash
git add -A
git commit -m "feat: your feature description"
git push origin feature/your-feature-name
```

### 7. **Create Pull Request**
- Опишите изменения
- Приложите скриншоты (если UI)
- Укажите связанные issues

---

## 🔒 Правила безопасности

### ❌ НИКОГДА не коммитьте:

1. **Персональные данные (PII)**
   - Аудиозаписи звонков
   - Транскрипции с реальными ФИО/телефонами
   - Логи с реальными данными

2. **Секреты**
   - API keys, tokens
   - Credentials файлы
   - Пароли, chat_id

3. **Упоминания клиентов**
   - Названия конкретных компаний
   - Реальные адреса филиалов
   - Имена реальных сотрудников

### ✅ Используйте:

- `config.example.yaml` для примеров
- `branches.example.yaml` для демо данных
- Mock данные в тестах
- Generic термины в коде

---

## 📝 Стиль коммитов

Используйте [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: Add new audio format support
fix: Fix transcription bug for 8kHz files
docs: Update installation guide
refactor: Improve quality analyzer performance
test: Add tests for audio preprocessor
chore: Update dependencies
```

---

## 🧪 Тестирование

```bash
# Запустить все тесты
uv run pytest tests/

# Запустить конкретный тест
uv run pytest tests/test_config_validation.py

# С coverage
uv run pytest --cov=src tests/
```

---

## 📚 Документация

При добавлении новой функциональности:

1. **Docstrings** в коде (Google style)
2. **README.md** — обновить если нужно
3. **PROJECT_OVERVIEW.md** — для архитектурных изменений
4. **DEPLOYMENT_GUIDE.md** — для изменений в установке

---

## 🐛 Reporting Bugs

**Перед созданием issue:**

1. Проверьте, что bug еще не reported
2. Убедитесь, что используете последнюю версию
3. Проверьте SECURITY.md — возможно это security issue

**Создайте issue с:**

- Описанием проблемы
- Шагами для воспроизведения
- Ожидаемым и фактическим поведением
- Версией Python, OS, GPU
- Логами (БЕЗ PII!)

---

## 💡 Feature Requests

Хотите новую функцию?

1. Создайте issue с тегом `enhancement`
2. Опишите use case
3. Объясните почему это полезно
4. Предложите реализацию (опционально)

---

## 🎨 Code Style

### Python:
```bash
# Форматирование и линтинг
uv run ruff check src/
uv run ruff format src/

# Type checking (опционально)
uv run pyright src/
```

### Docstrings:
```python
def analyze_quality(transcript: str, script: str) -> dict:
    """
    Анализирует качество обслуживания по транскрипции.
    
    Args:
        transcript: Текст транскрипции звонка
        script: Корпоративный скрипт для оценки
        
    Returns:
        dict: Результаты анализа с оценками и рекомендациями
        
    Raises:
        ValueError: Если transcript пустой
    """
    pass
```

---

## Good first issues / topics (maintainers)

- Ищите задачи с префиксом **`[good first issue]`** в [Issues](https://github.com/FUYOH666/Scanovich.ai-audio-call/issues).
- **Topics** репозитория на GitHub: список для копирования в настройках репозитория лежит в [`.github-topics.txt`](.github-topics.txt) (одна тема на строку).

---

## 🏆 Признание вклада

Все contributors будут добавлены в:
- README.md (Contributors section)
- Git history
- Release notes

---

## 📞 Вопросы?

- 🌐 Website: [scanovich.ai](https://scanovich.ai)
- 📧 Email: iamfuyoh@gmail.com
- 💬 Telegram: [@ScanovichAI](https://t.me/ScanovichAI)

---

**Спасибо за вклад в ASR Call Quality Analyzer! 🚀**

**© 2025 ASR Call Quality Analyzer | **

