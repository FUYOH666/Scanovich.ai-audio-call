# Call Analytics Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Platform: Linux](https://img.shields.io/badge/platform-Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/FUYOH666/Scanovich.ai-audio-call)

**End-to-end call analytics: VoIP recording download → transcription → quality analysis → dashboards**

Production-ready platform for automated phone call transcription, quality scoring, and business intelligence. 100% local AI — no external APIs, full data sovereignty.

---

## Overview

Call Analytics Platform unifies two critical pipelines:

1. **VoIP Downloaders** — Automatic recording fetch from CloudPBX (Rostelecom) and Svyaztransit
2. **ASR Quality Analyzer** — Whisper transcription, LLM post-processing, 30-criteria quality scoring

Recordings flow directly from VoIP providers into the ASR pipeline. Scale from 1K to 100K+ calls/month on a single GPU.

---

## Architecture

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│  VoIP Downloaders   │     │   ASR Pipeline      │     │   Analytics         │
│  (Rostelcom,        │────▶│   input/            │────▶│   SQLite, Sheets,   │
│   Svyaztransit)     │     │   Whisper + VLLM    │     │   Telegram          │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
```

---

## Features

### Core
- **Hardware-adaptive models** — Set `model_preset: "auto"` to auto-select Whisper model by GPU VRAM (tiny → large-v3)
- **VoIP integration** — Downloaders write to `input/`; ASR daemon processes automatically
- **30-criteria quality scoring** — Objective 0–100 assessment per call
- **PII masking** — Automatic redaction of personal data
- **Multi-format** — MP3, WAV, M4A, JSON (Asterisk, VoIP)

### Analytics
- **Telegram reports** — Daily (09:00) and weekly summaries
- **Google Sheets** — Time-series dashboard, upsell metrics
- **CSV export** — Error analysis, branch rankings

### Scalability
- **RTF < 0.1** — 10× faster than real-time transcription
- **100K+ calls/month** — Single GPU (24GB VRAM)
- **systemd/cron** — 24/7 operation

---

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/FUYOH666/Scanovich.ai-audio-call.git call-analytics
cd call-analytics
uv sync
cp config.example.yaml config.yaml
cp branches.example.yaml branches.yaml
```

### 2. Configure ASR (hardware-based model selection)

In `config.yaml`:

```yaml
asr:
  model_preset: "auto"   # Detects GPU VRAM, selects best model
  # Or set explicitly: tiny, base, small, medium, large-v3, large-v3-turbo
  device: "cuda"
```

### 3. Configure VoIP → ASR integration

For **Rostelcom** (`voip/rostelcom`):

```bash
cd voip/rostelcom
cp .env.example .env
# Set DOWNLOAD_DIR=../../input in .env for ASR integration
# Add CLOUDPBX_LOGIN, CLOUDPBX_PASSWORD, CLOUDPBX_DOMAIN
uv sync
uv run call_records_watcher.py --once
```

For **Svyaztransit** (`voip/svyaztransit`):

```bash
cd voip/svyaztransit
cp .env.example .env
# Set DOWNLOAD_DIR=../../input
# Add STRANZIT_USERNAME, STRANZIT_PASSWORD
uv run call_records_watcher.py --once
```

### 4. Run ASR daemon

```bash
uv run python main.py run
```

---

## Project Structure

```
call-analytics/
├── src/                    # ASR engine, VLLM postprocessor, quality analyzer
├── voip/
│   ├── rostelcom/          # CloudPBX Rostelecom downloader
│   └── svyaztransit/       # Svyaztransit downloader
├── input/                  # VoIP writes here → ASR reads
├── output/                 # Transcriptions
├── analytics/              # SQLite, dashboards
├── main.py                 # CLI (18 commands)
├── config.example.yaml
└── README.md
```

---

## Hardware Presets

| Preset        | Model          | VRAM   | Use case              |
|---------------|----------------|--------|------------------------|
| `auto`        | Detected       | —      | Best for your GPU     |
| `tiny`        | tiny           | ~1 GB  | CPU / low VRAM        |
| `base`        | base           | ~1 GB  | Light workloads       |
| `small`       | small          | ~2 GB  | Balanced               |
| `medium`      | medium         | ~5 GB  | Good accuracy         |
| `large-v3`    | large-v3       | ~10 GB | Best accuracy         |
| `large-v3-turbo` | large-v3-turbo | ~3 GB | Fast, good accuracy   |

---

## Requirements

- **GPU:** NVIDIA 8GB+ VRAM (24GB recommended for large-v3)
- **Python:** 3.12
- **VLLM:** Port 8000 (LLM for post-processing, 30B+ recommended)
- **uv:** `curl -LsSf https://astral.sh/uv/install.sh | sh`

---

## CLI Commands

| Command | Description |
|---------|-------------|
| `main.py run` | Start ASR daemon (24/7) |
| `main.py process-file input/call.mp3` | Process single file |
| `main.py health` | System diagnostics |
| `main.py analyze-quality` | Quality analysis |
| `main.py telegram-report` | Send Telegram report |
| `main.py sync-sheets` | Sync to Google Sheets |

---

## License

MIT. Copyright (c) 2025–2026 Aleksandr Mordvinov (ScanovichAI).

---

## Links

- **Website:** [scanovich.ai](https://scanovich.ai)
- **Telegram:** [@ScanovichAI](https://t.me/ScanovichAI)
- **GitHub:** [@FUYOH666](https://github.com/FUYOH666)
