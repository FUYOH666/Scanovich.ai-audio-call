# Remote LLM and future HTTP ASR

The project is local-first, but not single-host only.

Today:

- ASR runs in-process through Faster-Whisper.
- LLM post-processing and quality analysis already support a local or remote OpenAI-compatible HTTP endpoint.

This means a practical deployment can already be:

- one Linux GPU host for everything,
- a CPU worker plus a remote LLM over LAN / VPN / Tailscale,
- or a mixed local/cloud LLM strategy for selected customers.

For the operator-facing comparison, see [DEPLOYMENT_PROFILES.md](DEPLOYMENT_PROFILES.md).

## Deployment profiles

Use these profiles to keep the architecture clear:

### Profile A: all-local GPU

- Faster-Whisper runs on the same machine as the worker
- LLM runs on the same host or another process on the same machine
- best for a single Linux GPU host

### Profile B: CPU worker plus remote LLM

- worker handles file intake, preprocessing, persistence, and web/API
- LLM lives on a separate OpenAI-compatible server
- best when the app host is lightweight but you already have a dedicated inference machine

### Profile C: future CPU worker plus remote ASR and LLM

- worker remains the orchestrator
- ASR and LLM both live on dedicated LAN / VPN / Tailscale services
- this requires an HTTP ASR adapter that is not implemented yet

The public website should describe these as deployment options, but the runtime behaviour and configuration stay owned by this repository.

## Remote OpenAI-compatible LLM

Point the configured URLs at your own server. Do not commit real hostnames or API keys. Use local `config.yaml` or environment overrides from [`.env.example`](../.env.example).

Example `config.yaml`:

```yaml
vllm:
  base_url: "http://your-llm-host:8005/v1"
  model: "your-served-model-name"

quality_analysis:
  provider: "vllm"
  base_url: "http://your-llm-host:8005/v1"
  model: "your-served-model-name"
```

Equivalent env overrides:

```bash
export VLLM__BASE_URL=http://your-llm-host:8005/v1
export VLLM__MODEL=your-served-model-name
export QUALITY_ANALYSIS__PROVIDER=vllm
export QUALITY_ANALYSIS__BASE_URL=http://your-llm-host:8005/v1
export QUALITY_ANALYSIS__MODEL=your-served-model-name
```

Requirements:

- The server must expose `/v1/chat/completions` compatible with the OpenAI client used by this project.
- Increase timeouts and retry settings when the link is slower than localhost.
- Keep `vllm` and `quality_analysis` aligned unless you intentionally want different models or providers.

## ASR today

Transcription is still performed in-process through Faster-Whisper. Practical options right now:

1. Use `device: cpu` with a smaller model for experiments.
2. Run the full worker on a Linux GPU host for production throughput.
3. Use the current web/API layer on the same machine as the worker.

## HTTP ASR direction

Optional HTTP ASR is not implemented in the current codebase yet, but it is the clean next local-first extension.

The intended shape is small and explicit:

- add an ASR backend switch in config,
- keep the same pipeline contract,
- support a remote ASR server over LAN / VPN / Tailscale,
- preserve fail-fast startup and explicit logging of which backend is active.

That would let a lightweight worker reuse a dedicated GPU ASR host without rewriting the rest of the product.

## Website boundary

If you expose the product through a public site, keep that site as a front door only:

- the site links to a separate demo or pilot URL,
- the protected app still runs from this repository,
- the site should not embed private hostnames, secrets, or duplicated runtime logic.

## Telephony audio

Recordings are often 8 kHz mono with heavy compression. The preprocessor normalizes volume and resamples toward 16 kHz mono before ASR via `asr.preprocessing.target_sample_rate`.
