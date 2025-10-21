"""
Утилиты: ConfigManager, GPUMonitor, логирование.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

import coloredlogs
import pynvml as nvidia_smi
import yaml

from src.config_validation import AppConfig


class ConfigManager:
    """Менеджер конфигурации с поддержкой YAML и ENV."""

    def __init__(self, config_path: str = "config.yaml"):
        """
        Загрузить конфигурацию из YAML файла.

        Args:
            config_path: Путь к config.yaml

        Raises:
            FileNotFoundError: Если config.yaml не найден
            ValueError: Если конфигурация невалидна
        """
        self.config_path = Path(config_path)
        if not self.config_path.exists():
            raise FileNotFoundError(f"Конфиг не найден: {config_path}")

        # Загрузка YAML
        with open(self.config_path, "r", encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f)

        # Валидация через Pydantic (ENV переопределяет YAML)
        try:
            self.config = AppConfig(**yaml_data)
        except Exception as e:
            raise ValueError(f"Ошибка валидации конфига: {e}") from e

        # Создание директорий
        self.config.ensure_directories()

    def get(self) -> AppConfig:
        """Получить валидированную конфигурацию."""
        return self.config


class GPUMonitor:
    """Мониторинг GPU через nvidia-ml-py."""

    def __init__(self, gpu_index: int = 0):
        """
        Инициализация мониторинга GPU.

        Args:
            gpu_index: Индекс GPU (по умолчанию 0)

        Raises:
            RuntimeError: Если CUDA недоступна
        """
        self.gpu_index = gpu_index
        try:
            nvidia_smi.nvmlInit()
            self.handle = nvidia_smi.nvmlDeviceGetHandleByIndex(gpu_index)
            self.gpu_name = nvidia_smi.nvmlDeviceGetName(self.handle)
        except Exception as e:
            raise RuntimeError(
                f"Не удалось инициализировать GPU {gpu_index}: {e}"
            ) from e

    def get_memory_info(self) -> dict:
        """
        Получить информацию о памяти GPU.

        Returns:
            dict: {total_mb, used_mb, free_mb, utilization_percent}
        """
        try:
            mem_info = nvidia_smi.nvmlDeviceGetMemoryInfo(self.handle)
            return {
                "total_mb": mem_info.total // (1024 * 1024),
                "used_mb": mem_info.used // (1024 * 1024),
                "free_mb": mem_info.free // (1024 * 1024),
                "utilization_percent": round(mem_info.used / mem_info.total * 100, 2),
            }
        except Exception as e:
            logging.error(f"Ошибка получения информации о GPU: {e}")
            return {}

    def get_utilization(self) -> dict:
        """
        Получить утилизацию GPU.

        Returns:
            dict: {gpu_percent, memory_percent}
        """
        try:
            util = nvidia_smi.nvmlDeviceGetUtilizationRates(self.handle)
            return {"gpu_percent": util.gpu, "memory_percent": util.memory}
        except Exception as e:
            logging.error(f"Ошибка получения утилизации GPU: {e}")
            return {}

    def get_temperature(self) -> Optional[int]:
        """
        Получить температуру GPU в °C.

        Returns:
            int или None: Температура
        """
        try:
            return nvidia_smi.nvmlDeviceGetTemperature(
                self.handle, nvidia_smi.NVML_TEMPERATURE_GPU
            )
        except Exception:
            return None

    def check_device(self, required_device: str = "cuda") -> None:
        """
        GPU guard: проверка наличия CUDA.

        Args:
            required_device: Требуемое устройство ('cuda')

        Raises:
            RuntimeError: Если CUDA недоступна (fail-fast, no fallback)
        """
        if required_device == "cuda":
            try:
                import torch

                if not torch.cuda.is_available():
                    raise RuntimeError("CUDA недоступна! Только GPU-режим поддерживается.")
                
                cuda_version = torch.version.cuda
                logging.info(f"✓ CUDA доступна: {cuda_version}")
                logging.info(f"✓ GPU: {self.gpu_name}")
                
                mem_info = self.get_memory_info()
                logging.info(
                    f"✓ GPU память: {mem_info['used_mb']} / {mem_info['total_mb']} MB "
                    f"({mem_info['utilization_percent']}% используется)"
                )
            except ImportError as e:
                raise RuntimeError("PyTorch не установлен!") from e

    def __del__(self):
        """Очистка при удалении объекта."""
        try:
            nvidia_smi.nvmlShutdown()
        except Exception:
            pass


def setup_logging(config: AppConfig) -> None:
    """
    Настройка structured logging с ротацией.

    Args:
        config: Конфигурация приложения
    """
    log_level = getattr(logging, config.logging.level)

    # Корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Очистка существующих handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Console handler с цветами
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    coloredlogs.install(
        level=log_level,
        fmt=config.logging.format,
        logger=root_logger,
        field_styles={
            "asctime": {"color": "cyan"},
            "levelname": {"color": "magenta", "bold": True},
            "name": {"color": "blue"},
        },
        level_styles={
            "debug": {"color": "green"},
            "info": {"color": "white"},
            "warning": {"color": "yellow", "bold": True},
            "error": {"color": "red", "bold": True},
            "critical": {"color": "red", "bold": True, "background": "white"},
        },
    )

    # File handler для основного лога
    main_log_path = Path(config.logging.files["main"])
    main_log_path.parent.mkdir(parents=True, exist_ok=True)
    main_handler = RotatingFileHandler(
        main_log_path,
        maxBytes=config.logging.rotation["max_bytes"],
        backupCount=config.logging.rotation["backup_count"],
        encoding="utf-8",
    )
    main_handler.setLevel(log_level)
    main_handler.setFormatter(logging.Formatter(config.logging.format))
    root_logger.addHandler(main_handler)

    # File handler для ошибок
    error_log_path = Path(config.logging.files["errors"])
    error_handler = RotatingFileHandler(
        error_log_path,
        maxBytes=config.logging.rotation["max_bytes"],
        backupCount=config.logging.rotation["backup_count"],
        encoding="utf-8",
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(config.logging.format))
    root_logger.addHandler(error_handler)

    logging.info(f"✓ Логирование настроено: уровень {config.logging.level}")


def check_cuda_available() -> bool:
    """
    Проверка доступности CUDA.

    Returns:
        bool: True если CUDA доступна
    """
    try:
        import torch

        return torch.cuda.is_available()
    except ImportError:
        return False

