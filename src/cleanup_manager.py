"""
Менеджер автоочистки: ротация архивов, сжатие, emergency cleanup.
"""

import logging
import os
import shutil
import tarfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

from src.config_validation import CleanupConfig

logger = logging.getLogger(__name__)


class CleanupManager:
    """Управление автоочисткой обработанных файлов."""

    def __init__(self, config: CleanupConfig, paths_config):
        """
        Инициализация менеджера автоочистки.

        Args:
            config: Конфигурация автоочистки
            paths_config: Конфигурация путей
        """
        self.config = config
        self.paths = paths_config

        self.archive_path = Path(config.archive_path)
        self.input_path = Path(paths_config.input)

        # Создание директории архива
        self.archive_path.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"✓ CleanupManager инициализирован: retention={config.input_retention_days}d, "
            f"compress_after={config.compress_after_days}d"
        )

    def move_to_archive(self, audio_file: Path) -> bool:
        """
        Переместить обработанный файл в архив.

        Args:
            audio_file: Путь к аудиофайлу

        Returns:
            bool: True если успешно
        """
        if not audio_file.exists():
            logger.warning(f"Файл для архивирования не найден: {audio_file}")
            return False

        try:
            # Создание подпапки по дате (YYYY-MM)
            date_str = datetime.now().strftime("%Y-%m")
            archive_subdir = self.archive_path / date_str
            archive_subdir.mkdir(parents=True, exist_ok=True)

            # Перемещение файла
            destination = archive_subdir / audio_file.name
            shutil.move(str(audio_file), str(destination))

            logger.info(f"✓ Файл перемещён в архив: {audio_file.name} → {date_str}/")
            return True

        except Exception as e:
            logger.error(f"Ошибка перемещения в архив {audio_file.name}: {e}")
            return False

    def rotate_archive(self) -> dict:
        """
        Ротация архива: удаление старых файлов и сжатие.

        Returns:
            dict: Статистика {deleted_count, deleted_size_mb, compressed_count}
        """
        if not self.config.enabled:
            logger.info("Автоочистка отключена в конфиге")
            return {"deleted_count": 0, "deleted_size_mb": 0, "compressed_count": 0}

        logger.info("Запуск ротации архива...")

        stats = {"deleted_count": 0, "deleted_size_mb": 0, "compressed_count": 0}

        try:
            # 1. Удаление файлов старше retention_days
            deleted = self._delete_old_files()
            stats["deleted_count"] = deleted["count"]
            stats["deleted_size_mb"] = deleted["size_mb"]

            # 2. Сжатие файлов старше compress_after_days
            compressed = self._compress_old_files()
            stats["compressed_count"] = compressed

            logger.info(
                f"✓ Ротация архива завершена: удалено {stats['deleted_count']} файлов "
                f"({stats['deleted_size_mb']:.2f} MB), сжато {stats['compressed_count']} файлов"
            )

        except Exception as e:
            logger.error(f"Ошибка ротации архива: {e}", exc_info=True)

        return stats

    def _delete_old_files(self) -> dict:
        """
        Удалить файлы старше retention_days.

        Returns:
            dict: {count, size_mb}
        """
        cutoff_date = datetime.now() - timedelta(days=self.config.input_retention_days)
        deleted_count = 0
        deleted_size = 0

        for root, dirs, files in os.walk(self.archive_path):
            for filename in files:
                file_path = Path(root) / filename

                # Пропуск tar.gz архивов (они уже сжаты)
                if filename.endswith(".tar.gz"):
                    continue

                try:
                    # Проверка возраста файла
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mtime < cutoff_date:
                        file_size = file_path.stat().st_size
                        file_path.unlink()
                        deleted_count += 1
                        deleted_size += file_size
                        logger.debug(f"Удалён старый файл: {filename}")

                except Exception as e:
                    logger.warning(f"Ошибка удаления {filename}: {e}")

        deleted_size_mb = deleted_size / (1024 * 1024)
        logger.info(
            f"Удалено старых файлов: {deleted_count} ({deleted_size_mb:.2f} MB)"
        )

        return {"count": deleted_count, "size_mb": deleted_size_mb}

    def _compress_old_files(self) -> int:
        """
        Сжать файлы старше compress_after_days в tar.gz архивы.

        Returns:
            int: Количество сжатых файлов
        """
        cutoff_date = datetime.now() - timedelta(days=self.config.compress_after_days)
        compressed_count = 0

        # Группировка файлов по месяцам
        files_by_month = {}

        for root, dirs, files in os.walk(self.archive_path):
            for filename in files:
                file_path = Path(root) / filename

                # Пропуск уже сжатых
                if filename.endswith(".tar.gz"):
                    continue

                try:
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if mtime < cutoff_date:
                        month_key = mtime.strftime("%Y-%m")
                        if month_key not in files_by_month:
                            files_by_month[month_key] = []
                        files_by_month[month_key].append(file_path)

                except Exception as e:
                    logger.warning(f"Ошибка проверки {filename}: {e}")

        # Сжатие файлов по месяцам
        for month_key, files in files_by_month.items():
            if not files:
                continue

            archive_name = self.archive_path / f"{month_key}_archive.tar.gz"

            try:
                with tarfile.open(archive_name, "w:gz") as tar:
                    for file_path in files:
                        tar.add(file_path, arcname=file_path.name)
                        compressed_count += 1

                # Удаление исходных файлов после сжатия
                for file_path in files:
                    file_path.unlink()

                logger.info(
                    f"Сжат архив {archive_name.name}: {len(files)} файлов"
                )

            except Exception as e:
                logger.error(f"Ошибка сжатия архива {month_key}: {e}")

        return compressed_count

    def emergency_cleanup(self) -> dict:
        """
        Экстренная очистка при заполнении диска.

        Returns:
            dict: Статистика очистки
        """
        logger.warning("⚠️ Запуск экстренной очистки (диск заполнен)")

        stats = {"deleted_count": 0, "deleted_size_mb": 0}

        try:
            # Получение списка файлов с датами
            files_with_dates = []

            for root, dirs, files in os.walk(self.archive_path):
                for filename in files:
                    file_path = Path(root) / filename
                    try:
                        mtime = file_path.stat().st_mtime
                        size = file_path.stat().st_size
                        files_with_dates.append((file_path, mtime, size))
                    except Exception:
                        continue

            # Сортировка по возрасту (старые первые)
            files_with_dates.sort(key=lambda x: x[1])

            # Удаление пока не освободим достаточно места
            disk_usage = self._get_disk_usage()
            target_usage = 70  # Целевое заполнение 70%

            for file_path, mtime, size in files_with_dates:
                if disk_usage <= target_usage:
                    break

                try:
                    file_path.unlink()
                    stats["deleted_count"] += 1
                    stats["deleted_size_mb"] += size / (1024 * 1024)
                    disk_usage = self._get_disk_usage()
                    logger.debug(f"Удалён файл: {file_path.name}")

                except Exception as e:
                    logger.warning(f"Ошибка удаления {file_path.name}: {e}")

            logger.warning(
                f"✓ Экстренная очистка завершена: удалено {stats['deleted_count']} файлов "
                f"({stats['deleted_size_mb']:.2f} MB), заполнение диска: {disk_usage}%"
            )

        except Exception as e:
            logger.error(f"Ошибка экстренной очистки: {e}", exc_info=True)

        return stats

    def _get_disk_usage(self) -> float:
        """
        Получить заполнение диска в процентах.

        Returns:
            float: Процент заполнения
        """
        try:
            stat = shutil.disk_usage(self.archive_path)
            return (stat.used / stat.total) * 100
        except Exception as e:
            logger.error(f"Ошибка получения статистики диска: {e}")
            return 0.0

    def check_disk_space(self) -> bool:
        """
        Проверить, нужна ли экстренная очистка.

        Returns:
            bool: True если нужна очистка
        """
        usage = self._get_disk_usage()
        if usage >= self.config.max_disk_usage_percent:
            logger.warning(
                f"⚠️ Диск заполнен на {usage:.1f}% (лимит: {self.config.max_disk_usage_percent}%)"
            )
            return True
        return False

