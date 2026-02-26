# VoIP Call Downloaders

Automatic recording download from VoIP providers. Integrated with ASR pipeline: set `DOWNLOAD_DIR=../../input` to save directly to ASR input folder.

## Modules

| Module | Provider | Path |
|--------|----------|------|
| **Rostelcom** | CloudPBX Rostelecom | `voip/rostelcom/` |
| **Svyaztransit** | Svyaztransit LK | `voip/svyaztransit/` |

## ASR Integration

1. In `.env`: `DOWNLOAD_DIR=../../input`
2. Run from project root: `cd voip/rostelcom && uv run call_records_watcher.py`
3. ASR daemon monitors `input/` and processes new files automatically

## Quick Start

### Rostelcom

```bash
cd voip/rostelcom
cp .env.example .env
# Edit .env: CLOUDPBX_*, DOWNLOAD_DIR=../../input
uv sync
uv run call_records_watcher.py --once
```

### Svyaztransit

```bash
cd voip/svyaztransit
cp .env.example .env
# Edit .env: STRANZIT_*, DOWNLOAD_DIR=../../input
uv run call_records_watcher.py --once
```

See module-specific READMEs for full configuration.
