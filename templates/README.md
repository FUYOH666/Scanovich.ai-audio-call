# Evaluation script templates

| File | Purpose |
|------|---------|
| `script_evaluation_template_a.md` | Full 30-criteria template (extended; example domain-specific wording). |
| `script_evaluation_template_b.md` | Full 30-criteria template (standard). |
| `generic_sales_support.md` | **Starter pack:** 8 + 2 criteria for generic sales/support calls. Use with [`config.generic.example.yaml`](../config.generic.example.yaml) for matching `analytics.required_criteria` / `optional_criteria`. |

Scripts are Markdown files parsed by `src/quality_analyzer.py` (`ScriptParser`). Criteria lines must follow:

`N. **Title** — description.`

Section headers must be either the legacy titles (`### Основные сущности`, `### Дополнительные расширенные сущности`) or the human-readable titles (`### Основные критерии оценки …`, `### Дополнительные критерии …`).
