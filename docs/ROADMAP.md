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

- [ ] Optional web UI for browsing results
- [ ] HTTP API for external orchestration
- [ ] CI/CD hardening (already: GitHub Actions)

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

_Last updated: 2026-03-22 (merged from former `next_steps.md`)_
