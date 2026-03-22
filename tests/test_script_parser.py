"""Tests for quality script Markdown parsing."""

from pathlib import Path

import pytest

from src.quality_analyzer import ScriptParser


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_parse_template_b_headers_yields_thirty_criteria():
    path = REPO_ROOT / "templates" / "script_evaluation_template_b.md"
    criteria = ScriptParser(str(path)).parse()
    assert len(criteria) == 30
    assert criteria[0]["id"] == 1
    assert criteria[0]["block"] == "main"
    assert criteria[-1]["id"] == 30
    assert criteria[-1]["block"] == "additional"


def test_parse_generic_sales_support():
    path = REPO_ROOT / "templates" / "generic_sales_support.md"
    criteria = ScriptParser(str(path)).parse()
    assert len(criteria) == 10
    assert {c["id"] for c in criteria} == set(range(1, 11))


def test_parse_legacy_section_headers(tmp_path: Path):
    legacy = tmp_path / "legacy.md"
    legacy.write_text(
        """# Legacy

### Основные сущности

1. **One** — first.

### Дополнительные расширенные сущности

2. **Two** — second.
""",
        encoding="utf-8",
    )
    criteria = ScriptParser(str(legacy)).parse()
    assert len(criteria) == 2
    assert criteria[0]["name"] == "One"
    assert criteria[1]["block"] == "additional"
