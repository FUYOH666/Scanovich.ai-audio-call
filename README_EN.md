# Call Analytics Platform — deep reference

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/FUYOH666/Scanovich.ai-audio-call/actions/workflows/ci.yml/badge.svg)](https://github.com/FUYOH666/Scanovich.ai-audio-call/actions/workflows/ci.yml)

**Start here:** [`README.md`](README.md) — product overview, quick start, screenshots, and documentation lanes.

This file is the **extended operator and developer reference**: CLI commands, configuration details, testing, and troubleshooting.

---

## Entry modes

| Mode | Command | Use when |
|------|---------|----------|
| Web UI + API | `uv run python main.py web` | Demo, pilot, single-file review |
| Daemon | `uv run python main.py run` | Continuous processing from `input/` |
| One-off CLI | `uv run python main.py process-file path/to/call.mp3` | Scripts and debugging |

Web endpoints: `GET /healthz`, `POST /analyze`, `GET /analyses`, `GET /analyses/{result_id}`, `/`.

---

## Main commands

```bash
uv run python main.py run
uv run python main.py process-file path/to/call.mp3
uv run python main.py web
uv run python main.py health
uv run python main.py metrics
uv run python main.py analyze-quality output/call.txt
uv run python main.py analyze-batch
uv run python main.py report "Operator Name"
uv run python main.py aggregate --period day
uv run python main.py telegram-report --type daily
uv run python main.py sync-sheets
uv run python main.py update-dashboard
uv run python main.py test-sheets
```

---

## Configuration

Sources of truth:

- [`config.example.yaml`](config.example.yaml)
- [`.env.example`](.env.example)
- [`branches.example.yaml`](branches.example.yaml)

Key facts:

- Nested env overrides: `WEB__API_KEY`, `VLLM__BASE_URL`, `QUALITY_ANALYSIS__BASE_URL`, etc.
- Web settings live under `web.*` (host, port, optional API key).
- Quality-analysis directories are created only when `quality_analysis.enabled: true`.
- Minimal first-run without Telegram/Sheets: see [`README.md`](README.md#4-minimal-mode-no-telegram--google-sheets).

---

## Requirements

- **Production:** Linux, Python 3.12, NVIDIA GPU recommended for local Whisper + large LLM.
- **LLM:** local or remote OpenAI-compatible server (VPN / Tailscale / LAN supported).
- **ASR:** in-process Faster-Whisper today; optional HTTP ASR is a future extension ([`docs/REMOTE_ASR_AND_LLM.md`](docs/REMOTE_ASR_AND_LLM.md)).

---

## Testing

```bash
uv sync --extra dev
uv run pytest tests/
uv run pytest tests/test_api.py tests/test_cli_web.py
uv run ruff check src/web src/pipeline_service.py tests/test_api.py tests/test_cli_web.py
```

Coverage includes config validation, VLLM post-processing, web/API contracts, CLI `web` launch, script parsing, and cleanup.

---

## Troubleshooting

### Web layer returns 401

Check `WEB__REQUIRE_API_KEY`, `WEB__API_KEY`, and the `X-API-Key` header (or UI API-key field).

### LLM endpoint unavailable

```bash
uv run python main.py health
```

Verify `vllm.base_url` and `quality_analysis.base_url`.

### Recent analyses list is empty

History reads persisted artifacts under `output/`, `metadata/`, and `quality_analysis/individual/`. Run at least one successful analysis first.

### Rate limit behind a reverse proxy

Upload rate limits use the first `X-Forwarded-For` hop. Configure your proxy to pass the client IP, or rate-limit at the proxy. See [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md).

---

## Documentation index

| Topic | File |
|-------|------|
| Full doc map | [`docs/README.md`](docs/README.md) |
| Architecture | [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) |
| Deployment | [`DEPLOYMENT_GUIDE.md`](DEPLOYMENT_GUIDE.md) |
| Evaluation | [`docs/EVALUATION_GUIDE.md`](docs/EVALUATION_GUIDE.md) |
| FAQ | [`docs/FAQ.md`](docs/FAQ.md) |
| Remote LLM | [`docs/REMOTE_ASR_AND_LLM.md`](docs/REMOTE_ASR_AND_LLM.md) |
| Russian overview | [`PROJECT_OVERVIEW.md`](PROJECT_OVERVIEW.md) |
| Support | [`FUNDING.md`](FUNDING.md) |

---

## Commercial support

MIT-licensed open source. Paid pilot, on-prem implementation, and criteria tuning: [`FUNDING.md`](FUNDING.md).
