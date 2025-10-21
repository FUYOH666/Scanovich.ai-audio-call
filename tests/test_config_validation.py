"""
Тесты валидации конфигурации.
"""

import tempfile
from pathlib import Path

import pytest
import yaml

from src.config_validation import AppConfig
from src.utils import ConfigManager


def test_valid_config():
    """Тест валидной конфигурации."""
    config_data = {
        "asr": {
            "model": "large-v3",
            "device": "cuda",
            "compute_type": "float16",
        },
        "vllm": {
            "enabled": True,
            "base_url": "http://localhost:8000/v1",
        },
        "cleanup": {"enabled": True, "input_retention_days": 30},
    }

    config = AppConfig(**config_data)
    assert config.asr.model == "large-v3"
    assert config.asr.device == "cuda"
    assert config.vllm.enabled is True


def test_invalid_device():
    """Тест некорректного устройства."""
    config_data = {
        "asr": {"model": "large-v3", "device": "invalid_device"},
    }

    with pytest.raises(ValueError, match="Неподдерживаемое устройство"):
        AppConfig(**config_data)


def test_invalid_log_level():
    """Тест некорректного уровня логирования."""
    config_data = {
        "logging": {"level": "INVALID_LEVEL"},
    }

    with pytest.raises(ValueError, match="Уровень логирования должен быть"):
        AppConfig(**config_data)


def test_config_manager_from_file():
    """Тест загрузки конфига из YAML файла."""
    config_data = {
        "asr": {"model": "large-v3", "device": "cuda"},
        "vllm": {"enabled": False},
    }

    # Создание временного config.yaml
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as tmp_file:
        yaml.dump(config_data, tmp_file)
        tmp_file_path = tmp_file.name

    try:
        # Загрузка через ConfigManager
        manager = ConfigManager(tmp_file_path)
        config = manager.get()

        assert config.asr.model == "large-v3"
        assert config.vllm.enabled is False

    finally:
        Path(tmp_file_path).unlink()


def test_config_ensures_directories():
    """Тест создания необходимых директорий."""
    config = AppConfig()

    with tempfile.TemporaryDirectory() as tmpdir:
        config.paths.output = str(Path(tmpdir) / "output")
        config.paths.metadata = str(Path(tmpdir) / "metadata")
        config.paths.archive = str(Path(tmpdir) / "archive")
        config.paths.logs = str(Path(tmpdir) / "logs")
        config.paths.input = str(Path(tmpdir) / "input")

        config.ensure_directories()

        assert Path(config.paths.output).exists()
        assert Path(config.paths.metadata).exists()
        assert Path(config.paths.archive).exists()
        assert Path(config.paths.logs).exists()
        assert Path(config.paths.input).exists()

