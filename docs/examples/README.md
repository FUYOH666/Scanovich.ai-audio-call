# Example artifacts (synthetic, no real PII)

These files illustrate the shape of pipeline outputs for newcomers. **All content is fictional.**

| File | Description |
|------|-------------|
| [`sample_transcript.txt`](sample_transcript.txt) | Example ASR-style transcript (RU), short inbound call. |
| [`sample_quality_analysis.json`](sample_quality_analysis.json) | Example JSON structure for per-call quality scoring (field names may vary slightly by version). |

**Audio:** We do not ship audio samples in-repo (size, licensing). Use any 8 kHz mono telephony WAV/MP3 of your own; the preprocessor resamples toward 16 kHz mono for Whisper (see `config.example.yaml` → `asr.preprocessing.target_sample_rate`).
