# Deployment Profiles

This document turns the local-first architecture story into practical deployment choices.

## Why this exists

The project can already run in more than one useful way. Writing those modes down reduces confusion during pilots and keeps future HTTP ASR work anchored to real operator needs.

## Profile A: All-local GPU

Best when:

- you have one strong Linux GPU host,
- the same team controls the app and inference stack,
- you want the simplest operational setup.

Shape:

- app runs on the same host,
- Faster-Whisper runs locally,
- LLM runs locally or on the same machine,
- browser UI and API are exposed from the same deployment.

Use this when:

- you want the least moving parts,
- you need a fast internal deployment,
- you are comfortable operating one machine end to end.

## Profile B: CPU worker + remote LLM

Best when:

- the app host should stay lightweight,
- you already have a private LLM inference host,
- you want to keep upload flow and persistence close to operators.

Shape:

- app host runs `main.py web` or the daemon,
- transcripts, metadata, and saved analyses live on the app host,
- `vllm.base_url` and `quality_analysis.base_url` point to a remote OpenAI-compatible endpoint.

Use this when:

- local orchestration matters more than colocating all inference,
- your LLM infrastructure already exists elsewhere,
- you want a practical bridge toward richer local-first deployments.

## Profile C: CPU worker + remote ASR + remote LLM

Best when:

- you want the app host to orchestrate only,
- GPU inference should live on dedicated machines,
- network access over LAN / VPN / Tailscale is stable.

Shape:

- app host remains the operational front end,
- LLM is remote,
- ASR is remote through a future HTTP adapter.

Status:

- this profile is the next architectural direction,
- HTTP ASR is not implemented in the current codebase yet.

## Comparison matrix

| Profile | ASR | LLM | UI/API host | Complexity | Best for |
|---------|-----|-----|-------------|------------|----------|
| A | local | local | same host | low | first pilots, internal deployment |
| B | local | remote | app host | medium | local orchestration with separate LLM infra |
| C | remote | remote | app host | medium-high | later stage, dedicated inference hosts |

## Recommendation order

1. Start with Profile A if you can.
2. Use Profile B when remote LLM is already available and useful.
3. Move toward Profile C only after pilot hardening and only when HTTP ASR solves a real operational problem.

## Decision rule

Choose the simplest profile that:

- keeps data handling acceptable for the customer,
- makes the pilot easy to run,
- does not create support burden you do not need yet.
