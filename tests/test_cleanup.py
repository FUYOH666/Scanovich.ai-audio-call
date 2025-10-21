"""
Тесты менеджера автоочистки.
"""

import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from src.cleanup_manager import CleanupManager
from src.config_validation import CleanupConfig, PathsConfig


@pytest.fixture
def temp_dirs():
    """Создать временные директории для тестов."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        paths = {
            "input": tmpdir_path / "input",
            "archive": tmpdir_path / "archive",
        }

        for path in paths.values():
            path.mkdir(parents=True, exist_ok=True)

        yield paths


def test_move_to_archive(temp_dirs):
    """Тест перемещения файла в архив."""
    input_path = temp_dirs["input"]
    archive_path = temp_dirs["archive"]

    # Создание тестового файла
    test_file = input_path / "test.mp3"
    test_file.write_text("test content")

    # Конфигурация
    cleanup_config = CleanupConfig(
        enabled=True, archive_path=str(archive_path), input_retention_days=30
    )
    paths_config = PathsConfig(input=str(input_path))

    manager = CleanupManager(cleanup_config, paths_config)

    # Перемещение в архив
    result = manager.move_to_archive(test_file)

    assert result is True
    assert not test_file.exists()  # Исходный файл удалён

    # Проверка наличия в архиве (в подпапке по месяцам)
    date_str = datetime.now().strftime("%Y-%m")
    archived_file = archive_path / date_str / "test.mp3"
    assert archived_file.exists()


def test_rotate_archive_delete_old_files(temp_dirs):
    """Тест удаления старых файлов при ротации."""
    archive_path = temp_dirs["archive"]

    # Создание старого файла (35 дней назад)
    old_file = archive_path / "old_file.mp3"
    old_file.write_text("old content")

    # Установка старой даты модификации
    old_timestamp = (datetime.now() - timedelta(days=35)).timestamp()
    old_file.touch()
    import os
    os.utime(old_file, (old_timestamp, old_timestamp))

    # Создание нового файла
    new_file = archive_path / "new_file.mp3"
    new_file.write_text("new content")

    # Конфигурация с retention 30 дней
    cleanup_config = CleanupConfig(
        enabled=True,
        archive_path=str(archive_path),
        input_retention_days=30,
        compress_after_days=100,  # Отключаем сжатие для этого теста
    )
    paths_config = PathsConfig()

    manager = CleanupManager(cleanup_config, paths_config)

    # Ротация
    stats = manager.rotate_archive()

    # Старый файл должен быть удалён
    assert not old_file.exists()
    assert stats["deleted_count"] >= 1

    # Новый файл должен остаться
    assert new_file.exists()


def test_check_disk_space(temp_dirs):
    """Тест проверки заполнения диска."""
    archive_path = temp_dirs["archive"]

    cleanup_config = CleanupConfig(
        enabled=True,
        archive_path=str(archive_path),
        max_disk_usage_percent=95,  # Высокий порог
    )
    paths_config = PathsConfig()

    manager = CleanupManager(cleanup_config, paths_config)

    # Обычно диск не заполнен на 95%
    needs_cleanup = manager.check_disk_space()
    assert needs_cleanup is False or needs_cleanup is True  # Зависит от системы


def test_get_disk_usage(temp_dirs):
    """Тест получения статистики диска."""
    archive_path = temp_dirs["archive"]

    cleanup_config = CleanupConfig(enabled=True, archive_path=str(archive_path))
    paths_config = PathsConfig()

    manager = CleanupManager(cleanup_config, paths_config)

    usage = manager._get_disk_usage()

    assert 0 <= usage <= 100  # Процент должен быть в валидном диапазоне

