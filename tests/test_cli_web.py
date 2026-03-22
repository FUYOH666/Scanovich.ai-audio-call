import uvicorn
import yaml
from click.testing import CliRunner

from src.cli import cli


def write_test_config(
    tmp_path,
    *,
    require_api_key=False,
    api_key="",
):
    config_path = tmp_path / "config.yaml"
    logs_path = tmp_path / "logs"
    config = {
        "asr": {
            "model": "tiny",
            "device": "cpu",
            "compute_type": "int8",
        },
        "vllm": {
            "enabled": False,
        },
        "paths": {
            "input": str(tmp_path / "input"),
            "output": str(tmp_path / "output"),
            "metadata": str(tmp_path / "metadata"),
            "archive": str(tmp_path / "archive"),
            "logs": str(logs_path),
        },
        "logging": {
            "files": {
                "main": str(logs_path / "main.log"),
                "errors": str(logs_path / "errors.log"),
            }
        },
        "quality_analysis": {
            "enabled": False,
        },
        "web": {
            "host": "127.0.0.1",
            "port": 8080,
            "require_api_key": require_api_key,
            "api_key": api_key,
        },
    }
    config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    return config_path


def test_web_command_runs_uvicorn(monkeypatch, tmp_path):
    config_path = write_test_config(tmp_path)
    runner = CliRunner()
    calls = {}

    def fake_run(app, host, port, log_level):
        calls["host"] = host
        calls["port"] = port
        calls["log_level"] = log_level

    monkeypatch.setattr(uvicorn, "run", fake_run)

    result = runner.invoke(
        cli,
        ["web", "--config", str(config_path), "--host", "127.0.0.1", "--port", "9090"],
    )

    assert result.exit_code == 0
    assert calls == {"host": "127.0.0.1", "port": 9090, "log_level": "info"}


def test_web_command_rejects_public_bind_without_api_key(tmp_path):
    config_path = write_test_config(tmp_path, require_api_key=False, api_key="")
    runner = CliRunner()

    result = runner.invoke(
        cli,
        ["web", "--config", str(config_path), "--host", "0.0.0.0", "--port", "8080"],
    )

    assert result.exit_code != 0
    assert "Публичный bind без API key запрещён" in result.output
