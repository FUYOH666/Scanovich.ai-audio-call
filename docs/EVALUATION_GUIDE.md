# Evaluation Guide

Use this guide if you want to evaluate the project quickly before committing to a full deployment.

The goal is simple:

- confirm that your call flow fits the product,
- validate transcript and QA output quality,
- decide whether a pilot is worth running.

## Who this guide is for

- QA leads and operations managers
- founders evaluating a self-hosted speech analytics tool
- engineering teams preparing an internal pilot
- potential customers who want to test with their own calls

## Good fit

This project is a good fit if you need:

- self-hosted or controlled-infrastructure processing,
- call transcript and quality analysis in one pipeline,
- configurable scoring criteria,
- reports for managers or QA teams.

## Poor fit

This project is not the best first choice if you need:

- instant one-click SaaS onboarding,
- browser-only usage with no technical setup,
- real-time agent coaching today,
- diarization as a hard requirement from day one.

## Fast evaluation path

### 1. Prepare a small sample

Start with:

- 3 to 5 calls,
- one common call type,
- one clear business goal,
- no need for VoIP integration yet.

If possible, remove or mask sensitive information before sharing outside your environment.

### 2. Define one success question

Pick a narrow question such as:

- Can this spot missed script steps?
- Can this help us review more calls with the same QA team?
- Can this produce a manager-friendly summary?

Do not try to evaluate every future feature in the first session.

### 3. Use the smallest setup

For a first pass:

- copy `config.example.yaml` to `config.yaml`,
- keep optional integrations disabled if you do not need them,
- run `uv run python main.py health`,
- either process one file with `uv run python main.py process-file path/to/call.mp3`,
- or start `uv run python main.py web` and upload one file through the browser UI.

If you are testing with a remote OpenAI-compatible LLM endpoint, review `REMOTE_ASR_AND_LLM.md` first.

### 4. Inspect the outputs

Look at:

- transcript quality,
- whether PII masking is acceptable for your use case,
- whether the score and recommendations are understandable,
- whether the outputs are useful for a supervisor, not just an engineer.

The synthetic examples in `docs/examples/` show the expected output shape.

If you use the web layer, also check whether the recent-analyses list is understandable for a manager or QA lead. The product is now more than a one-shot upload demo: prior saved runs can be reopened from persisted artifacts.

### 5. Decide whether to continue

Move to a pilot if the answer is mostly yes to these questions:

- Are transcripts good enough to support QA, even if they are not perfect?
- Do the criteria and outputs look adaptable to your workflow?
- Can managers understand the report without reading raw logs?
- Would reviewing 100 percent of calls create value for your team?

## Pilot checklist

Before you start a real pilot, confirm these basics:

- one owner on the customer side who will review outputs,
- one business question for the pilot,
- one narrow call type,
- 3 to 10 representative calls,
- a decision deadline for “continue / stop / expand,”
- a deployment path:
  local demo, protected pilot host, or on-prem install.

For protected pilot deployments of the web layer, prefer:

- `WEB__REQUIRE_API_KEY=true`,
- `WEB__API_KEY` set through the environment,
- running the web layer through `uv run python main.py web`.

The current web/API surface for a pilot is:

- `GET /healthz`
- `POST /analyze`
- `GET /analyses`
- `GET /analyses/{result_id}`

## Recommended pilot scope

If the quick test is promising, the next step should be a narrow pilot:

- one team,
- one use case,
- one evaluation template,
- one or two integrations at most.

Good examples:

- sales call QA for one branch,
- appointment-booking quality checks,
- support-call review for one queue.

## Pilot success criteria

Define success before implementation.

Example success criteria:

- transcript quality is acceptable on most calls,
- QA team saves review time,
- report outputs lead to at least one useful coaching action,
- the deployment model matches your privacy requirements.

## Sample report flow

Use this order when presenting a pilot result to a non-technical stakeholder:

1. Start with the cleaned transcript, not raw logs.
2. Show the call classification and explain why it matters for routing or QA review.
3. Show the quality result and overall score.
4. Reopen one earlier analysis from the recent-analyses list to show that results remain reviewable after the original upload.
5. Extract one coaching action and one operational insight.
6. Decide whether the output is useful enough to justify a broader pilot.

The synthetic examples in `docs/examples/` are meant to support exactly this flow.

When presenting to stakeholders remotely, you can also use the README screenshots in [`docs/assets/`](../assets/README.md) (`web-ui-overview.png`, `web-ui-detail.png`) — they show the live UI layout without exposing customer data.

## What to postpone until later

Avoid blocking the first pilot on:

- full CRM integration,
- multi-tenant architecture,
- real-time hints,
- diarization,
- advanced dashboards.

Those features matter only after the core workflow proves valuable.

## If you want help

If you want support with a pilot, deployment, or criteria tuning, see `FUNDING.md` for support paths.

If you want help not only with deployment, but also with the first 2–5 real outreach conversations, use `docs/PILOT_OUTREACH_PLAYBOOK.md` as the lightweight script.
