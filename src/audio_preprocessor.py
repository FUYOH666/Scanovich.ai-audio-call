"""
Предобработка аудио: wake-signal, нормализация громкости.
"""

import logging
import tempfile
from pathlib import Path
from typing import Optional

import librosa
import numpy as np
import soundfile as sf

from src.config_validation import ASRConfig

logger = logging.getLogger(__name__)


class AudioPreprocessor:
    """Предобработка аудиофайлов для улучшения качества транскрипции."""

    def __init__(self, config: ASRConfig):
        """
        Инициализация препроцессора.

        Args:
            config: ASR конфигурация
        """
        self.config = config
        self.preprocessing_config = config.preprocessing
        self.target_sr = self.preprocessing_config.target_sample_rate

        # Wake-signal: громкий сигнал для улучшения распознавания начала
        if self.preprocessing_config.wake_signal["enabled"]:
            self.wake_signal = self._generate_wake_signal(
                samples=self.preprocessing_config.wake_signal["samples"],
                target_rms=self.preprocessing_config.wake_signal["rms"],
            )
        else:
            self.wake_signal = None

        logger.info(
            f"✓ AudioPreprocessor инициализирован: SR={self.target_sr}, "
            f"wake_signal={'enabled' if self.wake_signal is not None else 'disabled'}"
        )

    def _generate_wake_signal(self, samples: int, target_rms: float) -> np.ndarray:
        """
        Генерация wake-signal (универсальный громкий сигнал).

        Args:
            samples: Количество сэмплов
            target_rms: Целевой RMS

        Returns:
            np.ndarray: Wake-signal
        """
        # Генерация белого шума
        signal = np.random.uniform(-1, 1, samples).astype(np.float32)

        # Нормализация до целевого RMS
        current_rms = np.sqrt(np.mean(signal**2))
        if current_rms > 0:
            signal = signal * (target_rms / current_rms)

        logger.debug(f"Wake-signal сгенерирован: {samples} samples, RMS={target_rms}")
        return signal

    def _normalize_volume(self, audio: np.ndarray) -> np.ndarray:
        """
        Peak normalization (нормализация по пику).

        Args:
            audio: Входной аудиосигнал

        Returns:
            np.ndarray: Нормализованный сигнал
        """
        max_val = np.abs(audio).max()
        if max_val > 0:
            # Нормализуем до 0.95 от максимума (небольшой headroom)
            audio = audio * (0.95 / max_val)
        return audio

    def preprocess(self, input_path: str) -> str:
        """
        Полная предобработка аудиофайла.

        Args:
            input_path: Путь к входному аудиофайлу

        Returns:
            str: Путь к обработанному временному WAV файлу

        Raises:
            FileNotFoundError: Если файл не найден
            ValueError: Если файл некорректен
        """
        input_path_obj = Path(input_path)
        if not input_path_obj.exists():
            raise FileNotFoundError(f"Аудиофайл не найден: {input_path}")

        logger.info(f"Предобработка аудио: {input_path_obj.name}")

        try:
            # Загрузка аудио
            audio, sr = librosa.load(input_path, sr=self.target_sr, mono=True)
            logger.debug(
                f"Загружено: {len(audio)} samples, SR={sr}, длительность={len(audio)/sr:.2f}s"
            )

            # Wake-signal инъекция (в начало)
            if self.wake_signal is not None:
                audio = np.concatenate([self.wake_signal, audio])
                logger.debug("Wake-signal добавлен в начало")

            # Нормализация громкости
            if self.preprocessing_config.normalize_volume:
                audio = self._normalize_volume(audio)
                logger.debug("Громкость нормализована (peak normalization)")

            # Сохранение во временный WAV
            temp_file = tempfile.NamedTemporaryFile(
                suffix=".wav", delete=False, dir=tempfile.gettempdir()
            )
            sf.write(temp_file.name, audio, sr, subtype="PCM_16")
            logger.info(f"✓ Предобработка завершена: {temp_file.name}")

            return temp_file.name

        except Exception as e:
            logger.error(f"Ошибка предобработки аудио {input_path}: {e}")
            raise ValueError(f"Не удалось обработать аудио: {e}") from e

    def get_audio_duration(self, audio_path: str) -> Optional[float]:
        """
        Получить длительность аудиофайла.

        Args:
            audio_path: Путь к аудиофайлу

        Returns:
            float или None: Длительность в секундах
        """
        try:
            audio, sr = librosa.load(audio_path, sr=None, duration=0.1)
            info = sf.info(audio_path)
            return info.duration
        except Exception as e:
            logger.warning(f"Не удалось получить длительность {audio_path}: {e}")
            return None

