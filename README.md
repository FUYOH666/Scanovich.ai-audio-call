# Call Analytics Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Platform: Linux](https://img.shields.io/badge/platform-Linux%20%7C%20macOS-lightgrey.svg)](https://github.com/FUYOH666/Scanovich.ai-audio-call)

**Turn 100% of your call recordings into actionable quality reports — automatically.**

---

## The Problem

Your QA team listens to 3% of calls. The other 97% are a black box. Bad calls slip through, customers churn, and you find out too late. Cloud solutions cost $100K and send your data elsewhere.

## The Solution

VoIP recordings flow into local Whisper transcription → LLM quality scoring (30 criteria) → dashboards, Telegram reports, Google Sheets. 100% coverage. Your data stays on your servers. No external APIs.

## Results

- **Before:** 3% manual sampling, $51K/year in missed issues, reactive firefighting
- **After:** 100% coverage, $51K/year saved, real-time alerts, PII masking

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

## Deploy This For Your Business

This is open-source. You can run it yourself.

Or I can deploy, customize, and integrate it for your company in **2 weeks**.

**Fixed price: $5,000** — Voice Intelligence package. Includes VoIP integration, customization, deployment, and 30 days of support.

→ **Email:** iamfuyoh@gmail.com  
→ **Telegram:** [@ScanovichAI](https://t.me/ScanovichAI)

---

## Tech Stack

**Architecture:** VoIP Downloaders (Rostelecom, Svyaztransit) → ASR pipeline (Whisper + VLLM) → SQLite, Google Sheets, Telegram reports.

**Features:** Hardware-adaptive Whisper models, 30-criteria quality scoring, PII masking, multi-format (MP3, WAV, M4A). RTF < 0.1, 100K+ calls/month on single GPU.

**Requirements:** NVIDIA 8GB+ VRAM, Python 3.12, VLLM (port 8000), uv.

**CLI:** `main.py run` (daemon), `main.py process-file`, `main.py health`, `main.py telegram-report`, `main.py sync-sheets`.

**License:** MIT. [scanovich.ai](https://scanovich.ai) · [@FUYOH666](https://github.com/FUYOH666)
