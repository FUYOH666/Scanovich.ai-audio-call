"""Root Click CLI for Call Analytics Platform."""

from importlib.metadata import PackageNotFoundError, version

import click

from src.cli.commands import register


def _package_version() -> str:
    try:
        return version("call-analytics-platform")
    except PackageNotFoundError:
        return "0.0.0"


def build_cli() -> click.Group:
    @click.group()
    @click.version_option(_package_version(), prog_name="call-analytics")
    @click.pass_context
    def cli(ctx: click.Context) -> None:
        """Call Analytics Platform — транскрипция и анализ качества звонков."""
        ctx.ensure_object(dict)

    register(cli)
    return cli


cli = build_cli()

__all__ = ["build_cli", "cli", "_package_version"]
