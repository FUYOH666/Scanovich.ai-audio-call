# FAQ

Short answers for evaluators, operators, and contributors. For step-by-step evaluation, see [`EVALUATION_GUIDE.md`](EVALUATION_GUIDE.md).

## Product & fit

### What is this project?

A self-hosted pipeline: phone audio → Whisper transcription → OpenAI-compatible LLM post-processing → optional quality scoring → local files (and optional Telegram / Sheets).

### Who is it not for?

Teams that need instant multi-tenant SaaS, zero setup, real-time agent coaching, or guaranteed speaker diarization on day one.

### How is this different from cloud QA tools?

You run the stack on your infrastructure. Data stays under your control by default. You configure criteria and integrations; there is no mandatory vendor cloud for core processing.

### Will it transcribe every language and every audio quality the same way?

No. This repo is a **demonstration configuration** for a specific telephony profile (language, codecs, noise, domain). Accuracy depends first on the **ASR model** and how well it matches your audio. Another language or a very different recording quality usually needs retuning — see the note in [`README.md`](../README.md#important-this-is-a-demonstration-configuration) and contact in [`FUNDING.md`](../FUNDING.md).

## Setup & hardware

### Do I need a GPU?

Recommended for production ASR on Linux with local Whisper. CPU works for small tests with smaller models. LLM can run on another GPU host via OpenAI-compatible API.

### Can I use a remote LLM?

Yes. Point `vllm.base_url` (and `quality_analysis.base_url` if used) at a gateway on your LAN or VPN. See [`REMOTE_ASR_AND_LLM.md`](REMOTE_ASR_AND_LLM.md).

### Do I need Telegram or Google Sheets?

No. Disable them for minimal first-run — see [`README.md`](../README.md#4-minimal-mode-no-telegram--google-sheets).

### Does it run on Windows?

Production path is Linux. Experimental WSL2 notes: [`DEPLOYMENT_GUIDE.md`](../DEPLOYMENT_GUIDE.md).

## Web UI & API

### How do I try it quickly?

`uv sync` → copy configs → `uv run python main.py web` → open `http://127.0.0.1:8080`.

### What does the recent-analyses list show?

Saved artifacts from `output/`, `metadata/`, and `quality_analysis/individual/` — not a separate database.

### How do I protect a pilot deployment?

Set `WEB__REQUIRE_API_KEY=true` and a strong `WEB__API_KEY`. Clients send `X-API-Key`.

### Why is upload rate-limited?

Default in-memory limit per client IP (`security.rate_limit_per_hour`). Behind a reverse proxy, configure `X-Forwarded-For` correctly or rate-limit at the proxy.

## Data & privacy

### Where is data stored?

On local paths from config: `output/`, `metadata/`, `quality_analysis/`, logs, optional SQLite analytics DB.

### Does the project phone home?

Core pipeline is self-contained. Optional integrations (Telegram, Sheets, cloud LLM providers) only run if you enable and configure them.

### How do I report a security issue?

Follow [`SECURITY.md`](../SECURITY.md). Do not open public issues for vulnerabilities.

## Contributing & support

### Can I send a pull request?

See [`CONTRIBUTING.md`](../CONTRIBUTING.md). Maintainer capacity varies; check open issues before large changes.

### Is commercial help available?

Paid pilot, on-prem setup, and custom criteria: [`FUNDING.md`](../FUNDING.md) and [scanovich.ai](https://scanovich.ai).

## Roadmap

### What is planned next?

[`ROADMAP.md`](ROADMAP.md) — pilot hardening, optional HTTP ASR, GPU-validated dependency upgrades per [`reviews/STAFF_REVIEW_2026-06.md`](reviews/STAFF_REVIEW_2026-06.md).
