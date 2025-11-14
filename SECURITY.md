# 🔒 Security Policy

## Защита персональных данных

Этот проект разработан с учетом максимальной защиты персональных данных клиентов.

### ⚠️ КРИТИЧНО: Что НИКОГДА не должно попадать в репозиторий

#### 1. **Персональные данные клиентов (PII)**
- ❌ Аудиозаписи звонков (*.mp3, *.wav, *.m4a)
- ❌ Транскрипции с ФИО, телефонами, адресами (*.txt)
- ❌ Метаданные звонков (*.json с реальными данными)
- ❌ Логи обработки (могут содержать PII)
- ❌ Базы данных с реальными данными (*.db, *.sqlite)

#### 2. **Конфиденциальные конфигурации**
- ❌ `config.yaml` с реальными API keys, chat_id, spreadsheet_id
- ❌ `credentials/google_credentials.json` с реальными ключами
- ❌ `branches.yaml` с реальными адресами филиалов и именами сотрудников
- ❌ `.env` файлы с секретами

#### 3. **Упоминания клиентов**
- ❌ Названия конкретных компаний/клиентов в коде
- ❌ Реальные адреса филиалов в примерах
- ❌ Имена реальных сотрудников в примерах
- ❌ Специфичные термины, выдающие клиента

### ✅ Что МОЖНО публиковать

#### 1. **Примеры конфигураций**
- ✅ `config.example.yaml` с placeholder значениями
- ✅ `branches.example.yaml` с вымышленными данными
- ✅ `credentials/README.md` с инструкциями

#### 2. **Generic код**
- ✅ Исходный код без упоминаний клиентов
- ✅ Документация с обобщенными примерами
- ✅ Тесты с mock данными

#### 3. **Публичная информация**
- ✅ Описание архитектуры и технологий
- ✅ Инструкции по установке
- ✅ Лицензия и контакты автора

---

## 🛡️ Чеклист перед коммитом

Перед каждым `git commit` проверьте:

### 1. **Проверка на PII**
```bash
# Проверить на телефонные номера
grep -r "79[0-9]\{9\}" --include="*.py" --include="*.md" --include="*.yaml" \
  --exclude-dir=venv --exclude-dir=.git . | grep -v "example"

# Проверить на email (кроме публичных)
grep -r "@" --include="*.py" --include="*.md" --include="*.yaml" \
  --exclude-dir=venv --exclude-dir=.git . | \
  grep -v "example\|placeholder\|Author\|Copyright\|LICENSE\|iamfuyoh"
```

### 2. **Проверка на секреты**
```bash
# Проверить на API keys, tokens
grep -ri "key\|token\|secret\|password" --include="*.yaml" --include="*.py" \
  --exclude-dir=venv --exclude-dir=.git . | \
  grep -v "example\|placeholder\|# "
```

### 3. **Проверка на упоминания клиентов**
```bash
# Проверить на конкретные названия (замените на актуальные)
grep -ri "название_клиента\|конкретный_адрес" \
  --include="*.py" --include="*.md" --exclude-dir=venv --exclude-dir=.git .
```

### 4. **Проверка .gitignore**
```bash
# Убедиться, что критичные директории в .gitignore
cat .gitignore | grep -E "input/|output/|metadata/|credentials/|config.yaml|branches.yaml"
```

### 5. **Проверка staged файлов**
```bash
# Просмотреть что будет закоммичено
git diff --cached

# Убедиться, что нет случайно добавленных файлов
git status
```

---

## 🚨 Если случайно закоммитили секреты

### Немедленные действия:

1. **НЕ ПУШИТЬ в remote!** Если еще не запушили:
```bash
# Отменить последний коммит (файлы останутся)
git reset --soft HEAD~1

# Удалить файлы из staging
git reset HEAD <file>

# Исправить и закоммитить заново
```

2. **Если УЖЕ запушили:**
```bash
# Удалить файл из истории (ОПАСНО!)
git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch <file>" \
  --prune-empty --tag-name-filter cat -- --all

# Принудительно запушить (перезапишет историю)
git push origin --force --all
```

3. **Сменить скомпрометированные секреты:**
- Пересоздать API keys
- Сменить пароли
- Обновить credentials
- Уведомить клиента (если утекли их данные)

---

## 📋 Рекомендации для contributors

Если вы хотите внести вклад в проект:

1. **Форкните репозиторий**
2. **Создайте feature branch**
3. **Используйте только mock/example данные**
4. **Пройдите чеклист перед PR**
5. **Опишите изменения в PR**

### Пример хорошего PR:
```
Title: Add support for new audio format

Changes:
- Added support for .ogg files
- Updated audio_preprocessor.py
- Added tests with mock data
- Updated documentation

Checklist:
✅ No PII in code
✅ No secrets in config
✅ No client mentions
✅ Tests pass
✅ Documentation updated
```

---

## 🔐 Reporting Security Issues

Если вы обнаружили уязвимость или утечку данных:

**НЕ создавайте публичный issue!**

Свяжитесь напрямую:
- 📧 Email: iamfuyoh@gmail.com
- 💬 Telegram: [@ScanovichAI](https://t.me/ScanovichAI)

Я отвечу в течение 24 часов и исправлю проблему.

---

**© 2025 ASR Call Quality Analyzer | **

