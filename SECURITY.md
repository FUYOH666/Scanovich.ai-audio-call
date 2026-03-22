# Security Policy

This project operates in a privacy-sensitive domain. Real calls, transcripts, metadata, and infrastructure details must be treated as sensitive by default.

## What must never enter the repository

Do not commit:

- real audio recordings,
- real transcripts or metadata,
- customer names, branch addresses, or employee names,
- credentials or secrets,
- `.env` files with real values,
- private infrastructure hostnames or API keys,
- logs or databases containing production data.

Examples of sensitive files include:

- `config.yaml` with real secrets,
- `branches.yaml` with real addresses,
- `credentials/google_credentials.json`,
- real `output/`, `metadata/`, or `quality_analysis/` artifacts.

## What is safe to publish

Safe examples include:

- `config.example.yaml`,
- `.env.example`,
- `branches.example.yaml`,
- synthetic sample outputs,
- mock data in tests,
- generic technical documentation.

## Security checklist before opening a PR

Before you push or open a pull request:

1. Check that no real customer data was added.
2. Check that no secrets or private URLs were added.
3. Check that screenshots, logs, and issue text are sanitized.
4. Confirm `.gitignore` still protects runtime and credential paths.
5. Review staged files carefully.

If available in your environment, run:

```bash
./check_before_commit.sh
```

## If you accidentally committed sensitive data

Act immediately:

1. Stop and do not push further.
2. Remove the sensitive content from the working tree and staging area.
3. Rotate any exposed secrets.
4. Contact the maintainer if you need help cleaning up safely.

If sensitive data has already been pushed, treat it as a real incident:

- rotate secrets first,
- assess whether customer data was exposed,
- contact the maintainer immediately,
- coordinate any history cleanup carefully rather than improvising.

## Reporting security issues

Do not open a public GitHub issue for security problems.

Report privately:

- Email: `iamfuyoh@gmail.com`
- Telegram: [`@ScanovichAI`](https://t.me/ScanovichAI)

Please include:

- a short summary,
- affected area or file,
- reproduction steps if safe,
- impact assessment if known,
- any immediate mitigation you already applied.

## Scope

This policy covers:

- repository contents,
- example configs and docs,
- public issue and PR content,
- deployment guidance that could accidentally leak private infrastructure details.
