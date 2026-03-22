# Architecture

Call Analytics Platform: **on-prem pipeline** from audio files to transcripts, LLM post-processing, quality scoring, and optional reporting (Telegram, Google Sheets, SQLite).

## Data flow

```text
VoIP downloaders (optional, voip/) → input/
    → watchdog (daemon_watcher)
    → audio preprocessor (normalize, resample, often to 16 kHz mono)
    → ASR (faster-whisper, asr.py)
    → raw transcript → output/
    → VLLM post-processor (PII masking, classification, vllm_postprocessor.py)
    → metadata/
    → quality analyzer (criteria from Markdown templates, quality_analyzer.py)
    → quality_analysis/
    → analytics (SQLite, aggregates, analytics_aggregator.py, db_manager.py)
    → Google Sheets / Telegram / CSV (optional)
```

Supporting: **cleanup_manager** (archive rotation), **branches_manager** (canonical names), **model_resolver** (Whisper preset vs VRAM).

## Main Python modules (`src/`)

| Module | Role |
|--------|------|
| `daemon_watcher.py` | Watches `input/`, queues processing |
| `audio_preprocessor.py` | Format / loudness / resampling |
| `asr.py` | faster-whisper transcription |
| `vllm_postprocessor.py` | OpenAI-compatible LLM: PII + classification |
| `quality_analyzer.py` | Script parsing + quality scoring (local vLLM or optional OpenRouter) |
| `branches_manager.py` | Branch / admin normalization (`branches.yaml`) |
| `db_manager.py` | SQLite persistence |
| `analytics_aggregator.py` | Day/week aggregates |
| `dashboard_generator.py` | Sheet row generation |
| `telegram_reporter.py` | Scheduled Telegram reports |
| `google_sheets_integrator.py` | Sheets sync |
| `sheets_cleanup.py` | Deduplication helper |
| `cleanup_manager.py` | Archive and disk policies |
| `cost_tracker.py` | Token usage when using cloud LLM APIs |
| `model_comparison.py` | Compare local vs cloud analysis (dev / experiments) |
| `report_generator.py` | Markdown reports |
| `csv_exporter.py` | CSV export |
| `error_extractor.py` | Error summaries from DB |
| `config_validation.py` | Pydantic config for `config.yaml` |
| `model_resolver.py` | Whisper model preset vs GPU memory |
| `utils.py` | Config load, logging, GPU monitor |

## CLI

All commands live under `main.py` (refactored into `src/cli/` for maintainability). Entry: `uv run python main.py --help`.

## External services

- **LLM**: OpenAI-compatible HTTP API (typical: vLLM on localhost or VPN host). See [REMOTE_ASR_AND_LLM.md](REMOTE_ASR_AND_LLM.md).
- **Optional cloud path**: OpenRouter (or similar) for comparison / cost tracking — not required for default on-prem setup.

## Security note

Default `.gitignore` excludes `input/`, `output/`, `metadata/`, real transcripts, and credentials. Use only synthetic samples in git (e.g. `docs/examples/`).
