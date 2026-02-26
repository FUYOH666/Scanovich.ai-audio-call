"""
Тесты health check функциональности

Автор: Aleksandr Mordvinov
Проект: CloudPBX Calls Downloader
"""

import pytest
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from call_records_watcher import CallRecordsDownloader


def test_health_check_structure(tmp_path, monkeypatch):
    """Тест структуры ответа health check"""
    # Настройка окружения
    monkeypatch.setenv("CLOUDPBX_LOGIN", "test")
    monkeypatch.setenv("CLOUDPBX_PASSWORD", "test")
    monkeypatch.setenv("CLOUDPBX_DOMAIN", "test.rt.ru")
    monkeypatch.setenv("DOWNLOAD_DIR", str(tmp_path / "downloads"))
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    
    downloader = CallRecordsDownloader()
    health = downloader.health_check()
    
    # Проверка структуры
    assert "status" in health
    assert "timestamp" in health
    assert "versions" in health
    assert "configuration" in health
    assert "checks" in health
    
    # Проверка версий
    assert "python" in health["versions"]
    assert "requests" in health["versions"]
    
    # Проверка конфигурации
    assert "city_name" in health["configuration"]
    assert "domain" in health["configuration"]
    assert "download_dir" in health["configuration"]


def test_health_check_database(tmp_path, monkeypatch):
    """Тест проверки базы данных в health check"""
    db_path = tmp_path / "test.db"
    
    # Создаем базу данных
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS downloaded_records (
                id TEXT PRIMARY KEY,
                file_name TEXT,
                start_time TEXT,
                call_direction TEXT,
                duration_seconds INTEGER,
                downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                local_path TEXT
            )
        """)
        conn.commit()
    
    monkeypatch.setenv("CLOUDPBX_LOGIN", "test")
    monkeypatch.setenv("CLOUDPBX_PASSWORD", "test")
    monkeypatch.setenv("CLOUDPBX_DOMAIN", "test.rt.ru")
    monkeypatch.setenv("DOWNLOAD_DIR", str(tmp_path / "downloads"))
    monkeypatch.setenv("DATABASE_PATH", str(db_path))
    
    downloader = CallRecordsDownloader()
    health = downloader.health_check()
    
    assert health["checks"]["database"]["status"] == "ok"
    assert "total_records" in health["checks"]["database"]


def test_health_check_download_dir(tmp_path, monkeypatch):
    """Тест проверки директории загрузок в health check"""
    download_dir = tmp_path / "downloads"
    download_dir.mkdir()
    
    monkeypatch.setenv("CLOUDPBX_LOGIN", "test")
    monkeypatch.setenv("CLOUDPBX_PASSWORD", "test")
    monkeypatch.setenv("CLOUDPBX_DOMAIN", "test.rt.ru")
    monkeypatch.setenv("DOWNLOAD_DIR", str(download_dir))
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    
    downloader = CallRecordsDownloader()
    health = downloader.health_check()
    
    assert health["checks"]["download_dir"]["status"] == "ok"
    assert health["checks"]["download_dir"]["writable"] is True


def test_health_check_missing_download_dir(monkeypatch):
    """Тест health check с отсутствующей директорией загрузок"""
    monkeypatch.setenv("CLOUDPBX_LOGIN", "test")
    monkeypatch.setenv("CLOUDPBX_PASSWORD", "test")
    monkeypatch.setenv("CLOUDPBX_DOMAIN", "test.rt.ru")
    monkeypatch.setenv("DOWNLOAD_DIR", "/nonexistent/path")
    monkeypatch.setenv("DATABASE_PATH", "/tmp/test.db")
    
    downloader = CallRecordsDownloader()
    health = downloader.health_check()
    
    # Директория должна быть создана автоматически
    assert health["checks"]["download_dir"]["status"] == "ok"


def test_health_check_auth_status(monkeypatch, tmp_path):
    """Тест проверки статуса аутентификации в health check"""
    monkeypatch.setenv("CLOUDPBX_LOGIN", "test")
    monkeypatch.setenv("CLOUDPBX_PASSWORD", "test")
    monkeypatch.setenv("CLOUDPBX_DOMAIN", "test.rt.ru")
    monkeypatch.setenv("DOWNLOAD_DIR", str(tmp_path / "downloads"))
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "test.db"))
    
    downloader = CallRecordsDownloader()
    
    # Мокируем аутентификацию как неуспешную
    downloader.auth.is_authenticated = False
    downloader.authenticate = Mock(return_value=False)
    
    health = downloader.health_check()
    
    # Статус должен быть unhealthy если аутентификация не удалась
    assert health["checks"]["cloudpbx_auth"]["status"] == "error"
    assert health["status"] == "unhealthy"

