# Example artifacts (synthetic, no real PII)

These files illustrate the shape of pipeline outputs for newcomers. **All content is fictional.**

| File | Description |
|------|-------------|
| [`sample_transcript.txt`](sample_transcript.txt) | Example ASR-style transcript (RU), short inbound call. |
| [`sample_quality_analysis.json`](sample_quality_analysis.json) | Example JSON structure for per-call quality scoring (field names may vary slightly by version). |

**Audio:** We do not ship audio samples in-repo (size, licensing). Use any 8 kHz mono telephony WAV/MP3 of your own; the preprocessor resamples toward 16 kHz mono for Whisper (see `config.example.yaml` → `asr.preprocessing.target_sample_rate`).

The live web layer stores analogous artifacts under:

- `output/`
- `metadata/`
- `quality_analysis/individual/`

Those runtime artifacts now power the recent-analyses page and detail view in the browser UI.

## Sample report flow

If you are showing the project to a pilot customer or sponsor, walk through the artifacts in this order:

1. Open `sample_transcript.txt` and show the cleaned conversation text.
2. Open `sample_quality_analysis.json` and point to the overall score, strengths, weaknesses, and recommendations.
3. Show the live browser UI or `/analyses` endpoint and explain that previous runs remain reviewable.
4. Translate the output into one practical coaching action.
5. Ask whether this would help the team review more calls, coach operators faster, or reduce blind spots in QA.

The goal is not to impress with raw JSON. The goal is to make the business value easy to see.

For a visual walkthrough, see [`docs/assets/`](../assets/README.md) and the sample report section in [`docs/EVALUATION_GUIDE.md`](../EVALUATION_GUIDE.md). For quick answers, see [`docs/FAQ.md`](../FAQ.md).
