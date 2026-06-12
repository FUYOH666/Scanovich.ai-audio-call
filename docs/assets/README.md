# Repository assets

Visual materials for the public GitHub README and social preview. **Use synthetic or redacted content only** — no real customer data, phone numbers, hostnames, or API keys.

| File | Purpose |
|------|---------|
| [`web-ui-overview.png`](web-ui-overview.png) | Hero screenshot: upload + recent analyses |
| [`web-ui-detail.png`](web-ui-detail.png) | Detail view: transcript, classification, quality |
| [`github-social-preview.png`](github-social-preview.png) | GitHub Open Graph / social preview (1280×640) |

## Regenerating screenshots

1. Run the web layer locally: `uv run python main.py web`
2. Use **fictional** filenames and sample audio only.
3. Capture the browser at a reasonable width (~1100px).
4. Replace the PNGs in this folder and update [`README.md`](../README.md) if layout changed.

## GitHub social preview

Upload `github-social-preview.png` in the repository **Settings → General → Social preview**.

Do not commit TailScale IPs, internal hostnames, or credentials into images or filenames.
