# Remote LLM and local ASR (developer setups)

The stack is **on-prem first**: Faster-Whisper runs on the same machine as the worker by default, and the post-processor / quality analyzer talk to an **OpenAI-compatible HTTP API** (vLLM, llama.cpp server, Foundry, etc.).

## Remote OpenAI-compatible LLM (no local GPU for inference)

Point both URLs at your server (VPN/Tailscale is fine). **Do not commit real hostnames or API keys** — use environment-specific `config.yaml` or `.env` (see `.env.example`).

In `config.yaml`:

```yaml
vllm:
  base_url: "https://your-llm-host.example/v1"
  model: "your-served-model-name"

quality_analysis:
  base_url: "https://your-llm-host.example/v1"
  model: "your-served-model-name"
```

Requirements:

- The server must expose `/v1/chat/completions` compatible with the OpenAI client used in this project (`openai` Python SDK).
- Latency and timeouts: increase `timeout` / `retry_*` in config if the link is slow.

You can run **Whisper on a GPU workstation** and **LLM on another host**; only the HTTP endpoint must be reachable from the worker process.

## ASR (Whisper) without a local NVIDIA GPU

Today, transcription uses **faster-whisper** in-process (not HTTP). Practical options:

1. **`device: cpu`** with a **smaller** model (`tiny`, `base`, `small`) for experiments — slow but works on laptops.
2. **Run the full worker on a Linux box with CUDA** (recommended for production throughput).
3. **Future improvement:** optional HTTP ASR backend is not implemented in this repo; track or open an issue if you need it.

## Telephony audio

Recordings are often **8 kHz mono** with heavy compression. The preprocessor normalizes volume and resamples toward **16 kHz mono** before ASR (`asr.preprocessing.target_sample_rate`), which is the usual input shape for Whisper-based pipelines.
