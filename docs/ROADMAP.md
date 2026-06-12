# Roadmap

Backlog and direction for [Scanovich.ai-audio-call](https://github.com/FUYOH666/Scanovich.ai-audio-call). Priorities follow maintainer capacity and user issues.

## Near term (1–3 months)

**Performance**

- [ ] Larger batch throughput tuning
- [ ] Multi-GPU parallel processing
- [ ] Transcription result caching for re-runs
- [ ] LLM memory tuning (large local models)

**Features**

- [ ] More languages in quality analysis (e.g. Kazakh, English)
- [ ] Additional industry evaluation templates
- [ ] CRM integrations (AmoCRM, Bitrix24)
- [ ] Optional real-time hints during calls

**Analytics**

- [ ] Peak-hours analysis
- [ ] Voice sentiment (where applicable)
- [ ] BI export hooks (Tableau, Power BI)

**UX / ops**

- [x] Minimal web UI for upload-and-review demos (`src/web/`)
- [x] HTTP API for single-file analysis and orchestration (`/healthz`, `/analyze`)
- [x] Recent analyses page backed by persisted artifacts in `output/`, `metadata/`, and `quality_analysis/`
- [x] Minimal first-run docs (no Telegram / Google Sheets) in README and deployment guide
- [ ] Pilot hardening for web/API: rate limiting, upload quotas, audit-friendly logs, and clearer protected-demo operations
- [x] One-command web launch and clearer deployment path via `main.py web`
- [x] Filtering, pagination, and search for recent analyses
- [ ] Better detail views and export/share actions for saved analyses
- [ ] CI/CD hardening (already: GitHub Actions)
- [x] WSL2 deployment notes in `DEPLOYMENT_GUIDE.md`

**Local-first deployment**

- [ ] Optional HTTP ASR backend for LAN / VPN GPU hosts
- [ ] Clear deployment profiles: all-local GPU, CPU worker + remote ASR, remote LLM
- [ ] Shared config defaults to reduce drift between `vllm` and `quality_analysis`
- [ ] Public website to protected pilot bridge with a clean demo URL strategy and no shared runtime code
- [ ] GPU smoke validation before bumping `torch`, `faster-whisper`, and `openai` SDK (see `docs/reviews/STAFF_REVIEW_2026-06.md`)

## Longer term (3–12 months)

- [ ] Newer ASR when available; smaller LLM fast paths
- [ ] Optional diarization
- [ ] Training material generation from QA gaps
- [ ] Multi-tenant / queue-based scaling (only if product needs it)
- [ ] Compliance hardening (GDPR-style processes, encryption at rest) for enterprise deals

## Research

- [ ] Fine-tuning / RAG on customer scripts (with clear data policy)
- [ ] Call-type classification; early-churn signals from audio

## Contributing

1. Open an issue for non-trivial changes  
2. Follow [CONTRIBUTING.md](../CONTRIBUTING.md) (ruff, tests)  
3. Update docs when behavior or config changes  

_Last updated: 2026-06-12 (v5.2.1 tier-1 README/docs polish)_
