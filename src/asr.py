"""
ASR модуль на базе Faster-Whisper Large V3.

GPU-оптимизированная транскрипция с метриками производительности.
"""

import logging
import time
from pathlib import Path
from typing import Optional, Tuple

from faster_whisper import WhisperModel

from src.config_validation import ASRConfig
from src.utils import GPUMonitor

logger = logging.getLogger(__name__)


class ASREngine:
    """Движок автоматического распознавания речи (Whisper Large V3)."""

    def __init__(self, config: ASRConfig, gpu_monitor: Optional[GPUMonitor] = None):
        """
        Инициализация ASR движка.

        Args:
            config: ASR конфигурация
            gpu_monitor: Монитор GPU (опционально)

        Raises:
            RuntimeError: Если GPU недоступна при device='cuda'
        """
        self.config = config
        self.gpu_monitor = gpu_monitor
        self.model = None

        # GPU guard: проверка устройства
        if config.device == "cuda":
            if gpu_monitor:
                gpu_monitor.check_device("cuda")
            else:
                import torch

                if not torch.cuda.is_available():
                    raise RuntimeError(
                        "CUDA недоступна! Только GPU-режим поддерживается."
                    )

        # Загрузка модели при инициализации (как в рабочем проекте)
        self._load_model()

        logger.info(f"✓ ASR движок инициализирован с моделью {config.model}")

    def _load_model(self):
        """Загрузить модель Whisper в GPU память (один раз при старте)."""
        if self.model is not None:
            return  # Модель уже загружена

        logger.info(f"Загрузка модели Whisper: {self.config.model}")
        start_time = time.time()

        try:
            # Параметры загрузки модели (точно как в рабочем ASR-time)
            model_kwargs = {
                "model_size_or_path": self.config.model,  # КЛЮЧЕВОЕ: первый параметр!
                "device": self.config.device,
                "compute_type": self.config.compute_type,
                "cpu_threads": self.config.cpu_threads,
            }
            
            # Для GPU указываем индекс устройства
            if self.config.device == "cuda":
                model_kwargs["device_index"] = getattr(self.config, "device_index", 0)
            
            self.model = WhisperModel(**model_kwargs)
            load_time = time.time() - start_time
            logger.info(
                f"✓ Модель загружена за {load_time:.2f}s: "
                f"device={self.config.device}, compute_type={self.config.compute_type}"
            )

            if self.gpu_monitor and self.config.device == "cuda":
                mem_info = self.gpu_monitor.get_memory_info()
                logger.info(
                    f"GPU память после загрузки: {mem_info['used_mb']} MB "
                    f"({mem_info['utilization_percent']}%)"
                )

        except Exception as e:
            logger.error(f"Ошибка загрузки модели Whisper: {e}")
            raise RuntimeError(f"Не удалось загрузить модель: {e}") from e

    def transcribe(
        self, audio_path: str, audio_duration: Optional[float] = None
    ) -> Tuple[str, dict]:
        """
        Транскрибация аудиофайла.

        Args:
            audio_path: Путь к аудиофайлу
            audio_duration: Длительность аудио (для расчета RTF)

        Returns:
            Tuple[str, dict]: (текст транскрипции, метрики)

        Raises:
            FileNotFoundError: Если файл не найден
            ValueError: Если транскрипция не удалась
        """
        audio_path_obj = Path(audio_path)
        if not audio_path_obj.exists():
            raise FileNotFoundError(f"Аудиофайл не найден: {audio_path}")

        logger.info(f"Транскрипция: {audio_path_obj.name}")

        # Начальные метрики GPU
        gpu_mem_before = None
        if self.gpu_monitor and self.config.device == "cuda":
            gpu_mem_before = self.gpu_monitor.get_memory_info()

        start_time = time.time()

        try:
            # Параметры транскрипции (оптимизировано для экономии памяти)
            transcribe_params = {
                "beam_size": self.config.beam_size,
                "temperature": self.config.temperature,
                "vad_filter": self.config.vad_filter,
                "language": self.config.language,
                "word_timestamps": False,  # КРИТИЧНО: экономия памяти
                "condition_on_previous_text": False,  # КРИТИЧНО: каждый сегмент независим
            }

            # Initial prompt (если указан)
            if self.config.initial_prompt:
                transcribe_params["initial_prompt"] = self.config.initial_prompt

            # Транскрипция
            segments, info = self.model.transcribe(audio_path, **transcribe_params)

            # Сбор текста из сегментов
            transcription_text = ""
            segment_count = 0
            for segment in segments:
                transcription_text += segment.text + " "
                segment_count += 1

            transcription_text = transcription_text.strip()

            # Метрики
            elapsed_time = time.time() - start_time
            rtf = elapsed_time / audio_duration if audio_duration else None

            metrics = {
                "elapsed_time": round(elapsed_time, 2),
                "audio_duration": round(audio_duration, 2) if audio_duration else None,
                "rtf": round(rtf, 4) if rtf else None,
                "segment_count": segment_count,
                "language": info.language,
                "language_probability": round(info.language_probability, 4),
            }

            # Финальные метрики GPU
            if self.gpu_monitor and self.config.device == "cuda":
                gpu_mem_after = self.gpu_monitor.get_memory_info()
                metrics["gpu_memory_mb"] = gpu_mem_after["used_mb"]
                metrics["gpu_memory_delta_mb"] = (
                    gpu_mem_after["used_mb"] - gpu_mem_before["used_mb"]
                    if gpu_mem_before
                    else 0
                )

            logger.info(
                f"✓ Транскрипция завершена: {len(transcription_text)} символов, "
                f"{elapsed_time:.2f}s"
                + (f", RTF={rtf:.4f}" if rtf else "")
            )
            logger.debug(f"Метрики: {metrics}")

            if not transcription_text:
                logger.warning(f"Пустая транскрипция для {audio_path_obj.name}")

            # Очистка GPU кэша после транскрипции (критично для стабильности!)
            if self.config.device == "cuda":
                import torch
                import gc
                torch.cuda.empty_cache()
                gc.collect()
            
            return transcription_text, metrics

        except Exception as e:
            # Очистка GPU даже при ошибке
            if self.config.device == "cuda":
                import torch
                import gc
                torch.cuda.empty_cache()
                gc.collect()
                
            logger.error(
                f"Ошибка транскрипции {audio_path_obj.name}: {e}", exc_info=True
            )
            raise ValueError(f"Транскрипция не удалась: {e}") from e

