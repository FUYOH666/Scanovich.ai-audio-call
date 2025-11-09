# Инструкция по публикации проекта

## Подготовка к публикации

Все изменения готовы к коммиту. Для публикации выполните:

```bash
# 1. Проверить, что все файлы добавлены
git add -A
git status

# 2. Создать коммит с описанием изменений
git commit -m "feat: Приведение проекта в соответствие с user rules и очистка

- Миграция Dockerfile на uv sync --frozen
- Удаление requirements.txt и устаревших примеров портфолио
- Создание CI/CD workflow (.github/workflows/ci.yml)
- Добавление английской версии README (README_EN.md)
- Обновление документации о Context-7 консультациях
- Очистка проекта от временных и неактуальных файлов
- Обновление всех ссылок на venv → uv run

Website: https://scanovich.ai"

# 3. Push в репозиторий
git push origin main
```

## Что было сделано:

✅ Dockerfile переписан для использования uv
✅ requirements.txt удален
✅ Удалены примеры портфолио (ai_service_example.py, data_processor_example.py)
✅ Удалены тесты для примеров
✅ Удалены временные файлы (vc_post.md, vc_rules.md, github.md, docker-compose.yml)
✅ Создан CI/CD workflow
✅ Создана английская версия README
✅ Обновлена документация о Context-7
✅ Все ссылки на venv обновлены на uv run

