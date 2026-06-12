# Contributing to Call Analytics Platform

Thank you for considering a contribution.

This repository is public, but it works in a privacy-sensitive domain. Good contributions improve the product without exposing real customer data or adding avoidable operational risk.

## Before you start

Please read:

- [`README.md`](README.md) for the public product overview
- [`docs/README.md`](docs/README.md) for the documentation map and reader paths
- [`docs/FAQ.md`](docs/FAQ.md) for common evaluator questions
- [`SECURITY.md`](SECURITY.md) for responsible reporting and data-handling rules

For non-trivial changes, opening an issue first is the safest path.

## Local setup

```bash
git clone git@github.com:YOUR_USERNAME/Scanovich.ai-audio-call.git
cd Scanovich.ai-audio-call
uv sync
```

Create a feature branch:

```bash
git checkout -b feature/your-change
```

## Development expectations

When you make a change:

- keep the implementation small and clear,
- add or update tests when behavior changes,
- update docs when user-visible behavior or configuration changes,
- prefer `uv run ...` for Python commands,
- avoid introducing hidden fallbacks or silent degradation.

## Safety rules

Never commit:

- real call recordings,
- real transcripts or metadata,
- credentials or secrets,
- customer names or private branch addresses,
- internal hostnames or private infrastructure details.

Use:

- `config.example.yaml`,
- `.env.example`,
- `branches.example.yaml`,
- synthetic examples,
- mock data in tests.

## Recommended checks

Run the checks that match your change.

Common commands:

```bash
uv run pytest tests/
uv run ruff check src tests
uv run ruff format src tests
uv run pyright src
```

If you changed web/API behavior, at minimum run:

```bash
uv run pytest tests/test_api.py tests/test_cli_web.py
```

If you changed script parsing, run:

```bash
uv run pytest tests/test_script_parser.py
```

If your environment supports it, run the repository security helper before opening a PR:

```bash
./check_before_commit.sh
```

## Commit style

Use [Conventional Commits](https://www.conventionalcommits.org/):

```text
feat: add search for recent analyses
fix: reject invalid analysis ids
docs: clarify pilot deployment guide
refactor: simplify shared pipeline helpers
test: add saved-artifact API coverage
```

## Pull requests

Use the pull request template and include:

- what changed,
- why it matters,
- how it was tested,
- whether docs were updated,
- whether any UI screenshots help.

Good PRs are focused and easy to review.

## Documentation and screenshots

When you change user-visible UI or the public README:

- update [`README.md`](README.md) if the product story or quick start changes,
- update [`README_EN.md`](README_EN.md) for CLI/config/troubleshooting details,
- regenerate PNGs in [`docs/assets/`](docs/assets/README.md) with **synthetic data only**,
- add an entry to [`CHANGELOG.md`](CHANGELOG.md) under `[Unreleased]` or the next release section.

Follow the reader paths in [`docs/README.md`](docs/README.md) (Evaluator / Operator / Contributor) so links stay consistent.

## Reporting bugs and proposing features

Use the GitHub issue templates for:

- reproducible bugs,
- workflow improvements,
- feature requests.

Before opening an issue:

1. Check whether it already exists.
2. Confirm it is not a security issue.
3. Remove any PII, secrets, or customer-specific data from logs and screenshots.

## Documentation ownership

Use these rules when docs need updating:

- `README.md` — canonical public entrypoint
- `README_EN.md` — extended guide and command reference
- `docs/ARCHITECTURE.md` — pipeline and module behavior
- `DEPLOYMENT_GUIDE.md` — install, operations, and pilot deployment
- `docs/ROADMAP.md` — current next-step product work
- `CHANGELOG.md` — shipped changes

## Questions

- Website: [scanovich.ai](https://scanovich.ai)
- Email: `iamfuyoh@gmail.com`
- Telegram: [`@ScanovichAI`](https://t.me/ScanovichAI)

Thanks for helping make the project more useful.

