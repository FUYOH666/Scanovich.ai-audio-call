# Documentation index

Technical documentation for this repository. Use this file as the map for where each type of information lives.

## Start here

- [`../README.md`](../README.md) — **canonical public overview** (quick start, screenshots, doc lanes)
- [`../README_EN.md`](../README_EN.md) — deep CLI / config / troubleshooting reference
- [`../PROJECT_OVERVIEW.md`](../PROJECT_OVERVIEW.md) — Russian overview and doc map
- [`FAQ.md`](FAQ.md) — short answers for common questions

## Reader paths

| I am… | Read in order |
|-------|----------------|
| **Evaluator / buyer** | [EVALUATION_GUIDE.md](EVALUATION_GUIDE.md) → [examples/](examples/README.md) → [../README.md](../README.md) quick start |
| **Operator / DevOps** | [../DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md) → [DEPLOYMENT_PROFILES.md](DEPLOYMENT_PROFILES.md) → [REMOTE_ASR_AND_LLM.md](REMOTE_ASR_AND_LLM.md) |
| **Contributor** | [../CONTRIBUTING.md](../CONTRIBUTING.md) → [ARCHITECTURE.md](ARCHITECTURE.md) → [../CHANGELOG.md](../CHANGELOG.md) |

## Product and evaluation docs

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | Pipeline, shared web/API flow, persisted artifacts, and module map. |
| [EVALUATION_GUIDE.md](EVALUATION_GUIDE.md) | Fast path for first pilots and fit checks before a full deployment. |
| [FAQ.md](FAQ.md) | Common questions for evaluators and operators. |
| [examples/](examples/README.md) | Synthetic sample transcript and JSON outputs plus the live artifact model. |
| [assets/](assets/README.md) | README screenshots and GitHub social preview assets. |
| [../src/web/](../src/web/) | Browser UI and HTTP API for upload, recent analyses, and single-file review. |

## Deployment and operations

| Document | Description |
|----------|-------------|
| [../DEPLOYMENT_GUIDE.md](../DEPLOYMENT_GUIDE.md) | Deployment and 24/7 operations. |
| [REMOTE_ASR_AND_LLM.md](REMOTE_ASR_AND_LLM.md) | Remote OpenAI-compatible LLM support today and HTTP ASR direction. |
| [DEPLOYMENT_PROFILES.md](DEPLOYMENT_PROFILES.md) | Practical local-first deployment profiles and when to use each one. |

## Current planning docs

| Document | Description |
|----------|-------------|
| [ROADMAP.md](ROADMAP.md) | Current shipped product surface and next improvements. |

## Maintainer and founder notes

These are useful, but not required reading for every adopter.

| Document | Description |
|----------|-------------|
| [reviews/STAFF_REVIEW_2026-06.md](reviews/STAFF_REVIEW_2026-06.md) | Staff-level audit before v5.2.0; tech-delta and deferred GPU upgrades. |
| [PRODUCTIZATION_PLAN.md](PRODUCTIZATION_PLAN.md) | Strategic rationale and productization notes. Read as context, not as the live task tracker. |
| [PILOT_OUTREACH_PLAYBOOK.md](PILOT_OUTREACH_PLAYBOOK.md) | Narrow outreach and first pilot conversation playbook. |
| [WORKING_TOGETHER.md](WORKING_TOGETHER.md) | Collaboration paths that preserve the open-source core. |
| [PRODUCT_SURFACES.md](PRODUCT_SURFACES.md) | Boundary between the public website and the deployable product app. |

## Community and governance

- [`../CONTRIBUTING.md`](../CONTRIBUTING.md)
- [`../SECURITY.md`](../SECURITY.md)
- [`../CODE_OF_CONDUCT.md`](../CODE_OF_CONDUCT.md)
- [`../CHANGELOG.md`](../CHANGELOG.md)
- [`../FUNDING.md`](../FUNDING.md)
- [`../LICENSE`](../LICENSE)

Commercial services and extended positioning live on [scanovich.ai](https://scanovich.ai), while the technical source of truth stays in this repository.
