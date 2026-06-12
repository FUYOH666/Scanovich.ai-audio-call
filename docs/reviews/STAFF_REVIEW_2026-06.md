# Staff review — main @ v5.1.0 (2026-06)

Baseline: full repository on `main` before v5.2.0 release. Scope includes pipeline core, web/API, config, ops, and integrations. Excludes vendored VoIP vendor credentials and production `.env` values.

## Scope

**Goal:** Assess readiness for a maintenance release after ~2 months without pushes; identify safe improvements vs GPU-heavy dependency jumps.

**Modules reviewed:**

| Layer | Paths |
|-------|--------|
| Pipeline | `src/pipeline_service.py`, `src/asr.py`, `src/vllm_postprocessor.py`, `src/quality_analyzer.py` |
| Web/API | `src/web/app.py`, `src/web/static/` |
| Config | `src/config_validation.py`, `config.example.yaml` |
| Ops | `src/daemon_watcher.py`, `Dockerfile`, `.github/workflows/ci.yml` |
| CLI | `src/cli/commands.py` |

**Assumptions:** Local-first deployment; optional Telegram/Sheets; GPU smoke for ASR/torch deferred to a follow-up release.

## Correctness & logic

- Shared pipeline (`CallAnalysisPipeline`) has clear validation for extensions and file size; temp preprocessed audio is cleaned in `finally`.
- Web upload streams in 1 MiB chunks with size cap; temp dir removed after `/analyze`.
- `result_id` path traversal mitigated via `Path(result_id).name` check.
- Quality analysis can run with temporary artifacts when `persist=False` — temp files cleaned in `finally`.
- **Finding:** `config.example.yaml` enables Telegram and Google Sheets by default while Pydantic defaults disable them — newcomers copying the example may think integrations are required (docs gap, not runtime bug).

## Architecture fit

- Single pipeline reused by CLI and web — good separation.
- Web layer is thin over filesystem artifacts for history — appropriate for pilot scope.
- Version string duplicated in `src/__init__.py`, `src/web/app.py` — drift risk (should-fix, fixed in v5.2.0).
- `vllm.base_url` and `quality_analysis.base_url` can diverge — documented in deployment guide; optional env sync left to operators.

## Security & privacy

- Optional `X-API-Key` on `/analyze` and history endpoints when `web.require_api_key=true`.
- Public bind without API key rejected in CLI `web` command.
- 500 responses hide internal exception text; errors logged server-side.
- Upload extension allowlist and rate limiting (in-memory per client IP) present.
- **Nit:** In-memory rate limit does not survive multi-worker uvicorn — acceptable for demo/pilot single process.
- **Nit:** `X-Forwarded-For` trusted for rate limit identity — document reverse-proxy requirement for pilots.

## Reliability & ops

- `/healthz` reports ASR device/model and optional vLLM health.
- Docker HEALTHCHECK hits `/healthz`.
- Structured logging via `setup_logging` on web startup.
- **Should-fix:** `pytest` without `tests/` path collects broken `voip/rostelcom/tests` (import collision) — fixed via `norecursedirs` in v5.2.0.

## Performance

- ASR and LLM run in `asyncio.to_thread` from web handlers — avoids blocking event loop.
- No N+1 on history listing beyond filesystem glob — acceptable for pilot scale.

## Tests & verification

Commands run:

```bash
uv run pytest tests/ -q --tb=short   # 34 passed
uv run ruff check src/web src/pipeline_service.py tests/test_api.py tests/test_cli_web.py
```

Coverage: web API (auth, rate limit, history, safe 500), CLI web launch, config validation, script parser.

**Gap:** No integration test with real GPU ASR — expected for CI; document GPU smoke as release follow-up.

## Docs & DX

- README/ROADMAP strong for product surface; **minimal first-run without Telegram/Sheets missing** — addressed in v5.2.0.
- WSL2 notes absent from `DEPLOYMENT_GUIDE.md` — short section added in v5.2.0 (closes good-first-issue intent for #18).
- Staff review artifact (this file) added for evaluator trust signal.

## Tech-delta matrix (2026-03 → 2026-06)

| Package | Pinned | Available | Tier | v5.2.0 action |
|---------|--------|-----------|------|----------------|
| actions/checkout | v4 | v6 | A | Upgrade CI |
| astral-sh/setup-uv | v5 | v7 | A | Upgrade CI |
| pydantic | 2.10.3 | 2.12.5 | A | Upgrade if tests pass |
| pydantic-settings | 2.6.1 | 2.7.x | A | Upgrade with pydantic |
| faster-whisper | 1.0.3 | 1.2.1 | B | **Deferred** — GPU smoke pending |
| torch/torchaudio | 2.5.1 | 2.10.0 | C | **Not in v5.2.0** — CUDA matrix risk |
| openai SDK | 1.54.0 | 2.29.0 | B | **Deferred** — major API review needed |

## Grand opportunities (max 3)

1. **HTTP ASR adapter** (ROADMAP) — high impact for MacBook + remote GPU; medium effort; not v5.2.0.
2. **torch + faster-whisper bump after GPU smoke** — medium impact on latency/compat; high effort validation.
3. **Multi-worker safe rate limiting** (Redis or proxy-level) — pilot hardening; medium effort.

## Findings summary

| ID | Severity | Location | Recommendation |
|----|----------|----------|----------------|
| SR-01 | should-fix | `pytest.ini` / root pytest | Exclude `voip/` from collection — **fixed v5.2.0** |
| SR-02 | should-fix | `src/__init__.py`, `src/web/app.py` | Single version source — **fixed v5.2.0** |
| SR-03 | should-fix | `README.md`, `README_EN.md` | Document minimal mode — **fixed v5.2.0** |
| SR-04 | nit | `config.example.yaml` | Example enables integrations; docs clarify minimal snippet — **fixed v5.2.0** |
| SR-05 | nit | `src/web/app.py` rate limit | Document proxy/`X-Forwarded-For` in deployment guide — **fixed v5.2.0** |
| SR-06 | defer | `pyproject.toml` torch/faster-whisper/openai | GPU smoke before bump — **CHANGELOG note** |

## Verdict

**Ready for v5.2.0 release after Wave A:** docs, CI actions, patch pydantic, version sync, pytest scope fix. **No blockers** for a documentation and maintenance release. GPU-heavy dependency upgrades explicitly deferred.
