# Architecture

Call Analytics Platform is an on-prem, artifact-first pipeline for turning audio into transcripts, classifications, quality analysis, and optional reporting.

## Main data flow

```text
VoIP downloaders (optional, voip/) → input/
    → daemon watcher (daemon_watcher.py)
    → audio preprocessor (audio_preprocessor.py)
    → ASR (asr.py)
    → VLLM/OpenAI-compatible post-processing (vllm_postprocessor.py)
    → output/<id>.txt
    → metadata/<id>.json
    → quality_analysis/individual/<id>.json
    → analytics / Telegram / Google Sheets / CSV (optional)
```

Supporting services include `cleanup_manager.py` for archive policies, `branches_manager.py` for canonical names, and `model_resolver.py` for Whisper preset selection by available VRAM.

## Web/API flow

The browser and HTTP layer reuses the same processing path instead of implementing a parallel stack.

```text
browser UI (src/web/static/)
    → FastAPI app (src/web/app.py)
    → shared single-file pipeline (src/pipeline_service.py)
    → audio_preprocessor / asr / vllm_postprocessor / quality_analyzer
    → persisted artifacts
    → recent analyses list/detail
```

Primary runtime entrypoint:

```bash
uv run python main.py web
```

Advanced equivalent:

```bash
uv run uvicorn src.web.app:app --host 127.0.0.1 --port 8080
```

## Persisted artifact model

The web layer and the daemon now share one persisted storage story:

- `output/<result_id>.txt` stores the cleaned transcript
- `metadata/<result_id>.json` stores filename, processed time, classification, and ASR metrics
- `quality_analysis/individual/<result_id>.json` stores per-call quality results when enabled

The recent-analyses API reads these directories directly. There is no extra history database for the web layer.

## Current HTTP surface

- `GET /healthz` for liveness and config summary
- `POST /analyze` for new single-file analysis
- `GET /analyses` for recent persisted analyses
- `GET /analyses/{result_id}` for a specific saved result
- `/` for the static browser UI

If `web.require_api_key` is enabled, these routes require `X-API-Key`.

## Main Python modules (`src/`)

| Module | Role |
|--------|------|
| `daemon_watcher.py` | Watches `input/`, queues continuous processing |
| `audio_preprocessor.py` | Format conversion, normalization, resampling |
| `asr.py` | Faster-Whisper transcription |
| `vllm_postprocessor.py` | OpenAI-compatible LLM cleanup, masking, and classification |
| `quality_analyzer.py` | Script parsing and quality scoring |
| `pipeline_service.py` | Shared single-file pipeline reused by CLI and web/API |
| `web/app.py` | FastAPI app, history endpoints, and static UI mounting |
| `config_validation.py` | Pydantic config model for YAML and env overrides |
| `branches_manager.py` | Branch / admin normalization (`branches.yaml`) |
| `db_manager.py` | SQLite persistence for analytics |
| `analytics_aggregator.py` | Day/week aggregates |
| `dashboard_generator.py` | Dashboard row generation |
| `telegram_reporter.py` | Scheduled Telegram reports |
| `google_sheets_integrator.py` | Google Sheets synchronization |
| `sheets_cleanup.py` | Sheets deduplication helper |
| `cleanup_manager.py` | Archive and disk cleanup policies |
| `cost_tracker.py` | Cloud-LLM token and cost accounting |
| `model_comparison.py` | Local-vs-cloud comparison helpers |
| `report_generator.py` | Markdown reporting |
| `csv_exporter.py` | CSV export |
| `error_extractor.py` | Error summaries from analytics DB |
| `utils.py` | Config loading, logging, GPU helpers |

## External services

- **LLM**: OpenAI-compatible HTTP API, local or remote. See [REMOTE_ASR_AND_LLM.md](REMOTE_ASR_AND_LLM.md).
- **Optional cloud quality path**: OpenRouter-compatible provider for comparison or customer-specific trade-offs.
- **ASR today**: in-process Faster-Whisper only. Optional HTTP ASR is a future extension, not part of the current code path.

## Security note

Default `.gitignore` excludes `input/`, `output/`, `metadata/`, real transcripts, and credentials. Only synthetic examples under `docs/examples/` should be committed.

Public UI screenshots for the README live under [`assets/`](assets/README.md) (synthetic/redacted content only).
