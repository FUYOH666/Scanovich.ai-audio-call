"""
Тесты модуля конфигурации (pydantic-settings)

Автор: Aleksandr Mordvinov
Проект: CloudPBX Calls Downloader
"""

import pytest
import os
from pathlib import Path
from pydantic import ValidationError

from config import (
    CloudPBXConfig,
    DownloadConfig,
    FilterConfig,
    DatabaseConfig,
    LoggingConfig,
    AppConfig,
    get_config,
)


def test_cloudpbx_config_defaults():
    """Тест значений по умолчанию для CloudPBXConfig"""
    config = CloudPBXConfig()
    
    assert config.base_url == "https://p2.cloudpbx.rt.ru/webapi"
    assert config.login is None
    assert config.password is None
    assert config.domain is None


def test_cloudpbx_config_from_env(monkeypatch):
    """Тест загрузки CloudPBXConfig из переменных окружения"""
    monkeypatch.setenv("CLOUDPBX_LOGIN", "test_user")
    monkeypatch.setenv("CLOUDPBX_PASSWORD", "test_pass")
    monkeypatch.setenv("CLOUDPBX_DOMAIN", "test.rt.ru")
    
    config = CloudPBXConfig()
    
    assert config.login == "test_user"
    assert config.password == "test_pass"
    assert config.domain == "test.rt.ru"


def test_download_config_defaults(tmp_path):
    """Тест значений по умолчанию для DownloadConfig"""
    config = DownloadConfig()
    
    assert config.download_dir.exists()
    assert config.check_interval == 300
    assert config.lookback_hours == 24


def test_download_config_creates_dir(tmp_path):
    """Тест автоматического создания директории для загрузок"""
    download_dir = tmp_path / "test_downloads"
    
    config = DownloadConfig(download_dir=str(download_dir))
    
    assert download_dir.exists()
    assert download_dir.is_dir()


def test_filter_config_defaults():
    """Тест значений по умолчанию для FilterConfig"""
    config = FilterConfig()
    
    assert config.min_duration_seconds == 180
    assert config.only_incoming is True
    assert config.records_per_page == 100


def test_filter_config_validation():
    """Тест валидации FilterConfig"""
    # Валидные значения
    config = FilterConfig(min_duration_seconds=60, only_incoming=False)
    assert config.min_duration_seconds == 60
    assert config.only_incoming is False
    
    # Невалидные значения должны вызывать ошибку
    with pytest.raises(ValidationError):
        FilterConfig(min_duration_seconds=-1)


def test_database_config_defaults(tmp_path):
    """Тест значений по умолчанию для DatabaseConfig"""
    config = DatabaseConfig()
    
    assert config.database_path.name == "cloudpbx_calls.db"


def test_logging_config_defaults():
    """Тест значений по умолчанию для LoggingConfig"""
    config = LoggingConfig()
    
    assert config.level == "INFO"
    assert "pathname" in config.format
    assert "lineno" in config.format


def test_logging_config_validation():
    """Тест валидации уровня логирования"""
    # Валидные уровни
    for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        config = LoggingConfig(level=level)
        assert config.level == level
    
    # Невалидный уровень должен вызывать ошибку
    with pytest.raises(ValidationError):
        LoggingConfig(level="INVALID")


def test_app_config_initialization(monkeypatch, tmp_path):
    """Тест инициализации AppConfig"""
    # Устанавливаем минимальные переменные окружения
    monkeypatch.setenv("CLOUDPBX_LOGIN", "test")
    monkeypatch.setenv("CLOUDPBX_PASSWORD", "test")
    monkeypatch.setenv("CLOUDPBX_DOMAIN", "test.rt.ru")
    
    config = AppConfig()
    
    assert config.cloudpbx.login == "test"
    assert config.download.check_interval == 300
    assert config.filters.min_duration_seconds == 180


def test_get_config_singleton():
    """Тест что get_config возвращает синглтон"""
    config1 = get_config()
    config2 = get_config()
    
    assert config1 is config2


def test_config_validation_fail_fast(monkeypatch):
    """Тест что невалидная конфигурация вызывает ошибку при старте"""
    # Устанавливаем невалидное значение
    monkeypatch.setenv("LOG_LEVEL", "INVALID_LEVEL")
    
    with pytest.raises(ValidationError):
        LoggingConfig()

