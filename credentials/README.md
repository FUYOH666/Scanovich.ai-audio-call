# 🔐 Настройка Google Sheets API

## 📋 Требования
- Аккаунт Google Cloud Platform
- Проект GCP с включенным Google Sheets API
- Сервисный аккаунт с правами доступа

## 🚀 Пошаговая настройка

### Шаг 1: Создание проекта GCP
1. Перейдите в [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект или выберите существующий
3. Включите Google Sheets API:
   - Перейдите в "APIs & Services" > "Library"
   - Найдите "Google Sheets API"
   - Нажмите "Enable"

### Шаг 2: Создание сервисного аккаунта
1. Перейдите в "APIs & Services" > "Credentials"
2. Нажмите "Create credentials" > "Service account"
3. Заполните:
   - **Service account name:** `asr-call-quality-service`
   - **Description:** `Service account for ASR Call Quality Analyzer Google Sheets integration`
4. Нажмите "Create and continue"

### Шаг 3: Создание ключа
1. В списке сервисных аккаунтов нажмите на созданный аккаунт
2. Перейдите на вкладку "Keys"
3. Нажмите "Add Key" > "Create new key"
4. Выберите формат "JSON"
5. Скачайте файл ключа

### Шаг 4: Настройка доступа к таблице
1. Откройте вашу Google Sheets таблицу:
   ```
   https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID
   ```
2. Нажмите "Share" (Поделиться)
3. В поле email введите email сервисного аккаунта (заканчивается на `@project.iam.gserviceaccount.com`)
4. Установите права "Editor" (Редактор)
5. Нажмите "Send" (Отправить)

### Шаг 5: Размещение файла ключа
1. Переименуйте скачанный JSON файл в `google_credentials.json`
2. Поместите файл в папку `credentials/`:
   ```
   ASR-4.5/
   ├── credentials/
   │   └── google_credentials.json  ← сюда
   ```

### Шаг 6: Проверка настройки
```bash
# Проверьте доступ к Google Sheets
uv run python main.py test-sheets

# Должны увидеть сообщение об успешной аутентификации
✅ Google Sheets доступна
```

## 🔧 Структура service_account.json

Файл должен содержать следующие поля:
```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...",
  "client_email": "asr-call-quality-service@project.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
}
```

## 🚨 Важные замечания

### Безопасность:
- ✅ Никогда не коммитьте `service_account.json` в git
- ✅ Добавьте `credentials/` в `.gitignore`
- ✅ Регулярно ротируйте ключи сервисного аккаунта

### Ограничения:
- ⚠️ Google Sheets API имеет лимиты на количество запросов
- ⚠️ Бесплатный tier: 100 запросов в минуту
- ⚠️ Для production рассмотрите Google Cloud Billing

### Troubleshooting:
- **Ошибка аутентификации:** Проверьте права доступа к таблице
- **Файл не найден:** Убедитесь в правильном пути `credentials/google_credentials.json`
- **API disabled:** Включите Google Sheets API в GCP

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте логи: `tail -20 logs/asr_processor.log`
2. Проверьте структуру JSON файла
3. Убедитесь в правах доступа к таблице
4. Проверьте статус API в Google Cloud Console
