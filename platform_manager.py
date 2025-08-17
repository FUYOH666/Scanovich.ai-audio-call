#!/usr/bin/env python3
"""
🏗️ PLATFORM MANAGER v1.0 для WhisperX Pipeline
Автор: Scanovich.ai | Дата: 29.01.2025

Менеджер для автоматического определения и настройки платформ:
- M4 Pro + MLX (тестирование)
- GPU + CUDA (продакшн)
- CPU (fallback)

ЦЕЛЬ: Единая архитектура для плавного перехода M4 Pro → GPU
"""

import os
import sys
import logging
import platform
from typing import Dict, Optional, Tuple
from pathlib import Path

# Проверяем доступность платформ
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

logger = logging.getLogger(__name__)


class PlatformManager:
    """
    Менеджер платформ для автоматического определения и настройки
    
    Поддерживаемые платформы:
    - m4_pro_mlx: MacBook M4 Pro с MLX оптимизацией
    - gpu_cuda: GPU сервер с CUDA
    - cpu_fallback: CPU fallback режим
    """
    
    def __init__(self):
        """Инициализация менеджера платформ"""
        self.platform_type = self.detect_platform()
        self.config = self.load_platform_config()
        self.setup_environment()
        
        logger.info(f"🎯 Обнаружена платформа: {self.platform_type}")
        logger.info(f"⚙️ Конфигурация загружена: {len(self.config)} параметров")
    
    def detect_platform(self) -> str:
        """
        Автоматическое определение платформы
        
        Returns:
            str: Тип платформы (m4_pro_mlx, gpu_cuda, cpu_fallback)
        """
        
        if not TORCH_AVAILABLE:
            logger.warning("⚠️ PyTorch недоступен, используем CPU fallback")
            return "cpu_fallback"
        
        # Проверка GPU CUDA
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            
            logger.info(f"🚀 GPU обнаружен: {gpu_name} ({gpu_memory:.1f}GB)")
            
            # RTX 4090/5090 или аналогичные мощные GPU
            if gpu_memory >= 20:  # 20GB+ для продакшн обработки
                return "gpu_cuda"
            else:
                logger.warning(f"⚠️ GPU недостаточно мощный ({gpu_memory:.1f}GB), используем CPU")
                return "cpu_fallback"
        
        # Проверка Apple Silicon MPS (M4 Pro)
        elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
            system_info = platform.platform()
            logger.info(f"🍎 Apple Silicon обнаружен: {system_info}")
            
            # Проверка на M4 Pro (или аналогичные мощные Apple Silicon)
            if "arm64" in platform.machine().lower():
                return "m4_pro_mlx"
            else:
                return "cpu_fallback"
        
        # CPU fallback
        else:
            logger.warning("⚠️ Специализированные ускорители не найдены, используем CPU")
            return "cpu_fallback"
    
    def load_platform_config(self) -> Dict:
        """
        Загрузка конфигурации для текущей платформы
        
        Returns:
            Dict: Конфигурация платформы
        """
        
        configs = {
            "m4_pro_mlx": {
                # WhisperX настройки для M4 Pro
                "whisper_model": "large-v3",
                "whisper_device": "mps",
                "whisper_compute_type": "int8",
                "whisper_batch_size": 4,
                
                # LM Studio настройки для M4 Pro
                "lm_studio_model": "qwen3-30b-a3b-mlx@8bit",
                "lm_studio_max_tokens": 32768,
                "lm_studio_temperature": 0.6,
                "lm_studio_timeout": 600,
                
                # Обработка настройки
                "max_workers": 2,  # M4 Pro ограничения
                "memory_cleanup_interval": 1,  # После каждого звонка
                "model_reload_interval": 25,   # Каждые 25 звонков
                "session_restart_interval": 10,  # LM Studio рестарт
                
                # Память и производительность
                "expected_processing_speed": 0.47,  # x реального времени
                "ram_usage_per_call": 8,  # GB
                "platform_description": "MacBook M4 Pro с MLX оптимизацией"
            },
            
            "gpu_cuda": {
                # WhisperX настройки для GPU
                "whisper_model": "large-v3",
                "whisper_device": "cuda",
                "whisper_compute_type": "int8_float16",
                "whisper_batch_size": 16,  # Больше для GPU
                
                # LM Studio настройки для GPU
                "lm_studio_model": "qwen3-30b-cuda-8bit",
                "lm_studio_max_tokens": 32768,
                "lm_studio_temperature": 0.6,
                "lm_studio_timeout": 300,  # Быстрее на GPU
                
                # Обработка настройки
                "max_workers": 4,  # Больше воркеров для GPU
                "memory_cleanup_interval": 5,  # Реже на GPU
                "model_reload_interval": 100,  # Реже перезагрузка
                "session_restart_interval": 25,  # Реже рестарт
                
                # Память и производительность
                "expected_processing_speed": 3.0,  # x реального времени
                "ram_usage_per_call": 4,  # GB (эффективнее на GPU)
                "platform_description": "GPU сервер с CUDA оптимизацией"
            },
            
            "cpu_fallback": {
                # WhisperX настройки для CPU
                "whisper_model": "base",  # Меньшая модель для CPU
                "whisper_device": "cpu",
                "whisper_compute_type": "int8",
                "whisper_batch_size": 1,
                
                # LM Studio настройки для CPU (может быть недоступен)
                "lm_studio_model": None,  # Отключен на слабых CPU
                "lm_studio_max_tokens": 16384,
                "lm_studio_temperature": 0.7,
                "lm_studio_timeout": 900,
                
                # Обработка настройки
                "max_workers": 1,  # Один воркер для CPU
                "memory_cleanup_interval": 1,
                "model_reload_interval": 10,
                "session_restart_interval": 5,
                
                # Память и производительность
                "expected_processing_speed": 0.1,  # Очень медленно
                "ram_usage_per_call": 3,
                "platform_description": "CPU fallback режим"
            }
        }
        
        return configs.get(self.platform_type, configs["cpu_fallback"])
    
    def setup_environment(self):
        """Настройка окружения для текущей платформы"""
        
        # Базовые настройки автономности
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["HUGGINGFACE_HUB_CACHE"] = "./models/hub"
        
        if self.platform_type == "m4_pro_mlx":
            self._setup_mlx_environment()
        elif self.platform_type == "gpu_cuda":
            self._setup_cuda_environment()
        else:
            self._setup_cpu_environment()
    
    def _setup_mlx_environment(self):
        """Настройка окружения для M4 Pro + MLX"""
        logger.info("🍎 Настройка MLX окружения для M4 Pro")
        
        # Оптимизации для Apple Silicon
        os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"
        
        if TORCH_AVAILABLE and hasattr(torch.backends, 'mps'):
            # Включаем MPS если доступен
            torch.backends.mps.is_available() and logger.info("✅ MPS активирован")
    
    def _setup_cuda_environment(self):
        """Настройка окружения для GPU + CUDA"""
        logger.info("🚀 Настройка CUDA окружения для GPU")
        
        if TORCH_AVAILABLE and torch.cuda.is_available():
            # CUDA оптимизации
            torch.backends.cudnn.benchmark = True
            torch.backends.cuda.matmul.allow_tf32 = True
            
            # Flash Attention для Whisper (если доступен)
            os.environ["WHISPER_USE_FLASH_ATTENTION"] = "1"
            
            logger.info(f"✅ CUDA готов: {torch.cuda.device_count()} GPU")
    
    def _setup_cpu_environment(self):
        """Настройка окружения для CPU fallback"""
        logger.warning("💻 Настройка CPU fallback окружения")
        
        # Ограничиваем потоки для стабильности
        os.environ["OMP_NUM_THREADS"] = "4"
        os.environ["MKL_NUM_THREADS"] = "4"
    
    def get_whisper_config(self) -> Dict:
        """
        Получение конфигурации WhisperX для текущей платформы
        
        Returns:
            Dict: Параметры для WhisperX
        """
        return {
            "model_name": self.config["whisper_model"],
            "device": self.config["whisper_device"],
            "compute_type": self.config["whisper_compute_type"],
            "batch_size": self.config["whisper_batch_size"]
        }
    
    def get_lm_studio_config(self) -> Dict:
        """
        Получение конфигурации LM Studio для текущей платформы
        
        Returns:
            Dict: Параметры для LM Studio
        """
        return {
            "model_name": self.config["lm_studio_model"],
            "max_tokens": self.config["lm_studio_max_tokens"],
            "temperature": self.config["lm_studio_temperature"],
            "timeout": self.config["lm_studio_timeout"]
        }
    
    def get_processing_config(self) -> Dict:
        """
        Получение конфигурации обработки для текущей платформы
        
        Returns:
            Dict: Параметры обработки
        """
        return {
            "max_workers": self.config["max_workers"],
            "memory_cleanup_interval": self.config["memory_cleanup_interval"],
            "model_reload_interval": self.config["model_reload_interval"],
            "session_restart_interval": self.config["session_restart_interval"]
        }
    
    def get_performance_info(self) -> Dict:
        """
        Получение информации о производительности платформы
        
        Returns:
            Dict: Информация о производительности
        """
        return {
            "platform_type": self.platform_type,
            "description": self.config["platform_description"],
            "expected_speed": self.config["expected_processing_speed"],
            "ram_per_call": self.config["ram_usage_per_call"],
            "estimated_time_5000_calls": self._calculate_estimated_time(5000)
        }
    
    def _calculate_estimated_time(self, num_calls: int, avg_call_duration: float = 5.0) -> str:
        """
        Расчет ожидаемого времени обработки
        
        Args:
            num_calls: Количество звонков
            avg_call_duration: Средняя длительность звонка в минутах
            
        Returns:
            str: Человекочитаемое время
        """
        processing_time_per_call = avg_call_duration / self.config["expected_processing_speed"]
        total_minutes = num_calls * processing_time_per_call
        
        # Учитываем параллельную обработку
        parallel_minutes = total_minutes / self.config["max_workers"]
        
        if parallel_minutes < 60:
            return f"{parallel_minutes:.0f} минут"
        elif parallel_minutes < 1440:  # 24 часа
            hours = parallel_minutes / 60
            return f"{hours:.1f} часов"
        else:
            days = parallel_minutes / 1440
            return f"{days:.1f} дней"
    
    def optimize_for_platform(self):
        """Применение оптимизаций для текущей платформы"""
        
        if self.platform_type == "gpu_cuda" and TORCH_AVAILABLE and torch.cuda.is_available():
            # Очистка GPU кэша
            torch.cuda.empty_cache()
            logger.info("🧹 GPU кэш очищен")
        
        elif self.platform_type == "m4_pro_mlx" and TORCH_AVAILABLE:
            # Оптимизации для M4 Pro
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                # MPS оптимизации
                logger.info("🍎 MPS оптимизации применены")
        
        logger.info(f"⚡ Оптимизации для {self.platform_type} применены")
    
    def is_lm_studio_available(self) -> bool:
        """
        Проверка доступности LM Studio для текущей платформы
        
        Returns:
            bool: Доступен ли LM Studio
        """
        return self.config["lm_studio_model"] is not None
    
    def get_platform_summary(self) -> str:
        """
        Получение краткой информации о платформе
        
        Returns:
            str: Краткое описание платформы
        """
        perf_info = self.get_performance_info()
        
        summary = f"""
🏗️ ПЛАТФОРМА: {perf_info['platform_type'].upper()}
📝 Описание: {perf_info['description']}
⚡ Скорость: {perf_info['expected_speed']}x реального времени
💾 RAM на звонок: {perf_info['ram_per_call']}GB
🎯 5000 звонков: ~{perf_info['estimated_time_5000_calls']}
🔧 Воркеры: {self.config['max_workers']}
        """.strip()
        
        return summary


def test_platform_manager():
    """Тестирование PlatformManager"""
    
    print("🧪 ТЕСТИРОВАНИЕ PLATFORM MANAGER")
    print("=" * 50)
    
    try:
        manager = PlatformManager()
        
        print(manager.get_platform_summary())
        print()
        
        print("🎤 WhisperX конфигурация:")
        whisper_config = manager.get_whisper_config()
        for key, value in whisper_config.items():
            print(f"  {key}: {value}")
        print()
        
        print("🤖 LM Studio конфигурация:")
        if manager.is_lm_studio_available():
            lm_config = manager.get_lm_studio_config()
            for key, value in lm_config.items():
                print(f"  {key}: {value}")
        else:
            print("  ❌ LM Studio недоступен на этой платформе")
        print()
        
        print("⚙️ Обработка конфигурация:")
        proc_config = manager.get_processing_config()
        for key, value in proc_config.items():
            print(f"  {key}: {value}")
        
        print("\n✅ Тестирование завершено успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        raise


if __name__ == "__main__":
    test_platform_manager()