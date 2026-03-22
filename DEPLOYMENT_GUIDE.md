# Руководство по развертыванию

Актуальное руководство для текущего состояния репозитория: daemon-режим, web/API вход через `main.py web`, pilot-safe API key режим и история последних анализов на основе уже сохранённых артефактов.

## Что разворачивается

В репозитории есть два основных режима:

1. `uv run python main.py run` для непрерывной обработки файлов из `input/`.
2. `uv run python main.py web` для browser UI и HTTP API поверх того же shared pipeline.

Web/API слой сейчас умеет:

- `GET /healthz`
- `POST /analyze`
- `GET /analyses`
- `GET /analyses/{result_id}`
- `/` для browser UI

Поверх истории результатов уже есть базовые pilot-friendly возможности:

- поиск по имени файла, ID и preview,
- фильтр только по звонкам с quality-analysis,
- пагинация списка,
- базовое ограничение частоты upload-запросов.

## Предварительные требования

### Базовый production-хост

- Linux
- Python 3.12
- `uv`
- NVIDIA GPU для production ASR и локального LLM-сценария

### Важное по моделям

- ASR сегодня работает через in-process Faster-Whisper.
- LLM уже может быть локальным или удалённым OpenAI-compatible endpoint.
- Если LLM вынесен на другой хост, настройте `vllm.base_url` и `quality_analysis.base_url`.

## Установка

```bash
git clone https://github.com/FUYOH666/Scanovich.ai-audio-call.git call-analytics
cd call-analytics
uv sync
cp config.example.yaml config.yaml
cp branches.example.yaml branches.yaml
```

Минимальная первичная проверка:

```bash
uv run python main.py health
```

## Конфигурация

Основные источники истины:

- `config.example.yaml`
- `.env.example`
- `branches.example.yaml`

Ключевые настройки:

- `web.host`, `web.port`
- `web.require_api_key`, `web.api_key`
- `vllm.base_url`, `vllm.model`
- `quality_analysis.base_url`, `quality_analysis.model`
- `paths.output`, `paths.metadata`
- `quality_analysis.paths.individual`

Для секретов и env overrides используйте nested env names, например:

```bash
export WEB__REQUIRE_API_KEY=true
export WEB__API_KEY=replace-with-a-strong-key
export VLLM__BASE_URL=http://your-llm-host:8005/v1
export QUALITY_ANALYSIS__BASE_URL=http://your-llm-host:8005/v1
```

## Вариант A: локальный demo / pilot через web UI

Основной запуск:

```bash
uv run python main.py web
```

Откройте `http://127.0.0.1:8080`.

Browser UI позволяет:

- загрузить один файл,
- посмотреть transcript, classification, ASR metrics и quality output,
- открыть список последних анализов,
- перейти к деталям уже сохранённого анализа без повторной загрузки файла,
- фильтровать и догружать историю результатов.

### Protected pilot deployment

```bash
export WEB__REQUIRE_API_KEY=true
export WEB__API_KEY=replace-with-a-strong-key
uv run python main.py web --host 0.0.0.0 --port 8080
```

Ключ передаётся через `X-API-Key`. В browser UI для этого есть отдельное поле.

### Альтернативный продвинутый запуск

```bash
uv run uvicorn src.web.app:app --host 0.0.0.0 --port 8080
```

Используйте этот вариант только если осознанно хотите обойти CLI-обёртку. Для большинства сценариев основной entrypoint — `main.py web`.

## Вариант B: Docker для web/API слоя

Контейнер по умолчанию запускает именно web/API слой.

```bash
docker build -t call-analytics:pilot .

docker run --rm -it --gpus all \
  -p 8080:8080 \
  -e WEB__REQUIRE_API_KEY=true \
  -e WEB__API_KEY=replace-with-a-strong-key \
  -v "$(pwd)/config.yaml:/home/asruser/app/config.yaml:ro" \
  -v "$(pwd)/branches.yaml:/home/asruser/app/branches.yaml:ro" \
  -v "$(pwd)/output:/home/asruser/app/output" \
  -v "$(pwd)/metadata:/home/asruser/app/metadata" \
  -v "$(pwd)/quality_analysis:/home/asruser/app/quality_analysis" \
  call-analytics:pilot
```

Почему эти volume важны:

- `output/`, `metadata/`, `quality_analysis/` нужны не только для новых запусков,
- они же питают страницу последних анализов и detail view.

## Вариант C: daemon для непрерывной обработки

```bash
uv run python main.py run
```

Используйте этот режим, если записи уже попадают в `input/` из АТС или другого upstream процесса.

## VoIP-интеграции

В `voip/` лежат отдельные загрузчики для Rostelcom и Svyaztransit. Их задача — положить записи в общий `input/` проекта. Дальше работает общий daemon pipeline.

## Артефакты и история результатов

После успешной обработки формируются артефакты:

- `output/<result_id>.txt`
- `metadata/<result_id>.json`
- `quality_analysis/individual/<result_id>.json`

Именно эти файлы использует:

- daemon-экосистема,
- web/API ответы,
- recent-analyses список в UI.

Отдельная база для web history сейчас не нужна.

## 24/7 эксплуатация

Для production daemon-режима по-прежнему подходят systemd unit-файлы из `systemd/`.

Типичный набор:

- `vllm.service` для локального LLM-сервера, если он живёт на том же хосте
- `asr-watcher.service` для `main.py run`
- VoIP downloader services при необходимости

Если ваша архитектура уже использует удалённый OpenAI-compatible LLM, локальный `vllm.service` может быть не нужен.

## Проверка после запуска

### Web/API слой

```bash
curl http://127.0.0.1:8080/healthz
```

Затем:

1. Загрузите один тестовый файл через UI.
2. Убедитесь, что он появился в списке последних анализов.
3. Проверьте, что поиск и фильтр по истории работают ожидаемо.
4. Проверьте, что на диске появились `output/`, `metadata/` и при включённом качестве `quality_analysis/individual/` файлы.

### Daemon

```bash
cp /path/to/test.mp3 input/
uv run python main.py metrics
```

## Troubleshooting

### `main.py web` не стартует на публичном адресе

CLI блокирует public bind без API key. Включите:

```bash
export WEB__REQUIRE_API_KEY=true
export WEB__API_KEY=replace-with-a-strong-key
```

Или явно используйте `--allow-insecure-public-bind` только для временного demo.

### История анализов пустая

Проверьте:

- был ли хотя бы один успешный анализ,
- доступны ли каталоги `output/`, `metadata/`, `quality_analysis/individual/`,
- не указывают ли `paths.*` на другой путь, чем вы ожидаете.

### `429 Rate limit exceeded`

Web upload flow теперь ограничивается по `security.rate_limit_per_hour`.

Если вы запускаете короткий pilot и боитесь abuse на публичном URL, это полезно. Если ваш внутренний demo-host используется только вашей командой и лимит слишком строгий, поднимите значение в `config.yaml`.

### LLM недоступен

Проверьте `vllm.base_url` и `quality_analysis.base_url`. Это может быть localhost, LAN/VPN/Tailscale хост или другой OpenAI-compatible server.

### Нужен remote ASR

В текущем коде HTTP ASR ещё не реализован. Текущий безопасный путь — запускать worker на GPU-хосте или временно использовать `device: cpu` для экспериментов.

## Чеклист production-ready пилота

- [ ] `uv run python main.py health` проходит
- [ ] `main.py web` поднимается на нужном host/port
- [ ] При публичном bind включён API key
- [ ] Настроен разумный `security.rate_limit_per_hour`
- [ ] Хотя бы один тестовый файл успешно проанализирован
- [ ] Новый анализ появляется в recent-analyses списке
- [ ] Поиск, фильтр и пагинация истории проверены на реальных saved artifacts
- [ ] `output/`, `metadata/`, `quality_analysis/` подключены как persistent volumes
- [ ] LLM endpoint стабилен и задокументирован вне git

## Дополнительные документы

- [`README.md`](README.md) / [`README_EN.md`](README_EN.md)
- [`docs/README.md`](docs/README.md)
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/EVALUATION_GUIDE.md`](docs/EVALUATION_GUIDE.md)
- [`docs/REMOTE_ASR_AND_LLM.md`](docs/REMOTE_ASR_AND_LLM.md)
