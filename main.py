#!/usr/bin/env python3
"""Call Analytics Platform — CLI entry (commands live in `src.cli`)."""

import sys
from pathlib import Path

# Репозиторий в PYTHONPATH для `uv run python main.py`
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from src.cli import cli

if __name__ == "__main__":
    cli()
