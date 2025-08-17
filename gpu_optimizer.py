#!/usr/bin/env python3
"""
🚀 GPU OPTIMIZER v1.0 для WhisperX Pipeline
Автор: Scanovich.ai | Дата: 29.01.2025

Оптимизатор для GPU/CUDA операций:
- Мониторинг GPU ресурсов
- Автоматическая очистка GPU памяти
- CUDA оптимизации для производительности
- Балансировка нагрузки между GPU

ЦЕЛЬ: Максимальная производительность на GPU серверах (RTX 4090/5090)
"""

import os
import logging
import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

# Проверяем доступность GPU библиотек
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    torch = None

try:
    import nvidia_ml_py3 as nvml
    NVML_AVAILABLE = True
except ImportError:
    NVML_AVAILABLE = False
    nvml = None

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

logger = logging.getLogger(__name__)


class GPUOptimizer:
    """
    Оптимизатор для GPU/CUDA операций
    
    Функции:
    - Мониторинг GPU ресурсов (память, температура, утилизация)
    - Автоматическая очистка GPU памяти
    - CUDA оптимизации для максимальной производительности
    - Балансировка нагрузки между несколькими GPU
    """
    
    def __init__(self):
        """Инициализация GPU оптимизатора"""
        
        self.gpu_available = self._check_gpu_availability()
        self.gpu_count = 0
        self.gpu_info = []
        
        if self.gpu_available:
            self._initialize_gpu_monitoring()
            self._apply_cuda_optimizations()
        
        # Статистика
        self.stats = {
            "memory_cleanups": 0,
            "optimization_cycles": 0,
            "start_time": datetime.now(),
            "peak_memory_usage": 0.0,
            "total_processing_time": 0.0
        }
        
        logger.info(f"🚀 GPU Optimizer инициализирован")
        logger.info(f"🎯 GPU доступно: {self.gpu_available}")
        if self.gpu_available:
            logger.info(f"🔢 Количество GPU: {self.gpu_count}")
    
    def _check_gpu_availability(self) -> bool:
        """
        Проверка доступности GPU
        
        Returns:
            bool: Доступны ли GPU для оптимизации
        """
        
        if not TORCH_AVAILABLE:
            logger.warning("⚠️ PyTorch недоступен")
            return False
        
        if not torch.cuda.is_available():
            logger.info("💻 CUDA недоступен, GPU оптимизации отключены")
            return False
        
        self.gpu_count = torch.cuda.device_count()
        if self.gpu_count == 0:
            logger.warning("⚠️ GPU не найдены")
            return False
        
        return True
    
    def _initialize_gpu_monitoring(self):
        """Инициализация мониторинга GPU"""
        
        if NVML_AVAILABLE:
            try:
                nvml.nvmlInit()
                logger.info("✅ NVML мониторинг инициализирован")
            except Exception as e:
                logger.warning(f"⚠️ NVML недоступен: {e}")
        
        # Сбор информации о GPU
        for i in range(self.gpu_count):
            gpu_properties = torch.cuda.get_device_properties(i)
            
            gpu_info = {
                "device_id": i,
                "name": gpu_properties.name,
                "total_memory_gb": gpu_properties.total_memory / (1024**3),
                "compute_capability": f"{gpu_properties.major}.{gpu_properties.minor}",
                "multiprocessor_count": gpu_properties.multi_processor_count,
                "max_threads_per_block": gpu_properties.max_threads_per_block
            }
            
            self.gpu_info.append(gpu_info)
            logger.info(f"🎯 GPU {i}: {gpu_info['name']} ({gpu_info['total_memory_gb']:.1f}GB)")
    
    def _apply_cuda_optimizations(self):
        """Применение CUDA оптимизаций"""
        
        try:
            # Основные CUDA оптимизации
            torch.backends.cudnn.benchmark = True  # Ускорение для фиксированных размеров
            torch.backends.cuda.matmul.allow_tf32 = True  # TF32 для RTX 30xx/40xx
            torch.backends.cudnn.allow_tf32 = True
            
            # Оптимизации памяти
            torch.cuda.empty_cache()  # Очистка кэша при инициализации
            
            # Flash Attention если доступен (для Whisper)
            os.environ["WHISPER_USE_FLASH_ATTENTION"] = "1"
            
            # Оптимизации для производительности
            os.environ["CUDA_LAUNCH_BLOCKING"] = "0"  # Асинхронные операции
            
            logger.info("✅ CUDA оптимизации применены")
            self.stats["optimization_cycles"] += 1
            
        except Exception as e:
            logger.error(f"❌ Ошибка применения CUDA оптимизаций: {e}")
    
    def get_gpu_memory_info(self, device_id: int = 0) -> Dict:
        """
        Получение информации о памяти GPU
        
        Args:
            device_id: ID GPU устройства
            
        Returns:
            Dict: Информация о памяти GPU
        """
        
        if not self.gpu_available or device_id >= self.gpu_count:
            return {}
        
        try:
            torch.cuda.set_device(device_id)
            
            # Память в байтах
            memory_allocated = torch.cuda.memory_allocated(device_id)
            memory_reserved = torch.cuda.memory_reserved(device_id)
            memory_total = torch.cuda.get_device_properties(device_id).total_memory
            
            # Конвертация в GB
            memory_info = {
                "device_id": device_id,
                "allocated_gb": memory_allocated / (1024**3),
                "reserved_gb": memory_reserved / (1024**3),
                "total_gb": memory_total / (1024**3),
                "free_gb": (memory_total - memory_reserved) / (1024**3),
                "utilization_percent": (memory_reserved / memory_total) * 100
            }
            
            # Обновляем пиковое использование
            if memory_info["utilization_percent"] > self.stats["peak_memory_usage"]:
                self.stats["peak_memory_usage"] = memory_info["utilization_percent"]
            
            return memory_info
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения информации о памяти GPU {device_id}: {e}")
            return {}
    
    def get_gpu_temperature(self, device_id: int = 0) -> Optional[int]:
        """
        Получение температуры GPU
        
        Args:
            device_id: ID GPU устройства
            
        Returns:
            int: Температура в градусах Цельсия или None
        """
        
        if not NVML_AVAILABLE or not self.gpu_available:
            return None
        
        try:
            handle = nvml.nvmlDeviceGetHandleByIndex(device_id)
            temperature = nvml.nvmlDeviceGetTemperature(handle, nvml.NVML_TEMPERATURE_GPU)
            return temperature
            
        except Exception as e:
            logger.debug(f"Ошибка получения температуры GPU {device_id}: {e}")
            return None
    
    def get_gpu_utilization(self, device_id: int = 0) -> Optional[int]:
        """
        Получение утилизации GPU
        
        Args:
            device_id: ID GPU устройства
            
        Returns:
            int: Утилизация в процентах или None
        """
        
        if not NVML_AVAILABLE or not self.gpu_available:
            return None
        
        try:
            handle = nvml.nvmlDeviceGetHandleByIndex(device_id)
            utilization = nvml.nvmlDeviceGetUtilizationRates(handle)
            return utilization.gpu
            
        except Exception as e:
            logger.debug(f"Ошибка получения утилизации GPU {device_id}: {e}")
            return None
    
    def cleanup_gpu_memory(self, device_id: Optional[int] = None) -> bool:
        """
        Очистка памяти GPU
        
        Args:
            device_id: ID GPU для очистки (None = все GPU)
            
        Returns:
            bool: Успешность очистки
        """
        
        if not self.gpu_available:
            return False
        
        try:
            if device_id is None:
                # Очистка всех GPU
                for i in range(self.gpu_count):
                    torch.cuda.set_device(i)
                    torch.cuda.empty_cache()
                    torch.cuda.synchronize()
                
                logger.info(f"🧹 Очищена память всех GPU ({self.gpu_count})")
            else:
                # Очистка конкретного GPU
                if device_id < self.gpu_count:
                    torch.cuda.set_device(device_id)
                    torch.cuda.empty_cache()
                    torch.cuda.synchronize()
                    
                    logger.info(f"🧹 Очищена память GPU {device_id}")
                else:
                    logger.warning(f"⚠️ GPU {device_id} не существует")
                    return False
            
            self.stats["memory_cleanups"] += 1
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка очистки памяти GPU: {e}")
            return False
    
    def optimize_for_inference(self) -> bool:
        """
        Оптимизация GPU для инференса (без обучения)
        
        Returns:
            bool: Успешность оптимизации
        """
        
        if not self.gpu_available:
            return False
        
        try:
            # Оптимизации для инференса
            torch.backends.cudnn.deterministic = False  # Быстрее, но не детерминированно
            torch.backends.cudnn.benchmark = True       # Автоматическая оптимизация
            
            # Отключаем градиенты глобально для экономии памяти
            torch.set_grad_enabled(False)
            
            # Режим eval для всех GPU
            for i in range(self.gpu_count):
                torch.cuda.set_device(i)
                torch.cuda.empty_cache()
            
            logger.info("⚡ GPU оптимизированы для инференса")
            return True
            
        except Exception as e:
            logger.error(f"❌ Ошибка оптимизации для инференса: {e}")
            return False
    
    def get_optimal_batch_size(self, device_id: int = 0, model_memory_gb: float = 2.0) -> int:
        """
        Расчет оптимального размера батча для GPU
        
        Args:
            device_id: ID GPU устройства
            model_memory_gb: Размер модели в GB
            
        Returns:
            int: Рекомендуемый размер батча
        """
        
        if not self.gpu_available or device_id >= self.gpu_count:
            return 1  # Минимальный размер для CPU/невалидного GPU
        
        memory_info = self.get_gpu_memory_info(device_id)
        if not memory_info:
            return 1
        
        # Расчет доступной памяти для батчей
        available_memory = memory_info["free_gb"] * 0.8  # 80% от свободной памяти
        
        # Грубая оценка: модель + промежуточные активации + буфер
        memory_per_sample = model_memory_gb * 0.3  # 30% от размера модели на образец
        
        if memory_per_sample <= 0:
            memory_per_sample = 0.5  # Минимальная оценка
        
        optimal_batch_size = max(1, int(available_memory / memory_per_sample))
        
        # Ограничения по размеру батча
        optimal_batch_size = min(optimal_batch_size, 32)  # Максимум 32
        
        logger.info(f"🎯 Оптимальный размер батча для GPU {device_id}: {optimal_batch_size}")
        return optimal_batch_size
    
    def monitor_gpu_health(self) -> Dict:
        """
        Мониторинг здоровья всех GPU
        
        Returns:
            Dict: Статистика здоровья GPU
        """
        
        if not self.gpu_available:
            return {"healthy": False, "reason": "GPU недоступны"}
        
        health_stats = {
            "healthy": True,
            "gpu_count": self.gpu_count,
            "devices": []
        }
        
        for i in range(self.gpu_count):
            memory_info = self.get_gpu_memory_info(i)
            temperature = self.get_gpu_temperature(i)
            utilization = self.get_gpu_utilization(i)
            
            device_stats = {
                "device_id": i,
                "name": self.gpu_info[i]["name"] if i < len(self.gpu_info) else f"GPU {i}",
                "memory_utilization": memory_info.get("utilization_percent", 0),
                "temperature": temperature,
                "utilization": utilization,
                "healthy": True,
                "warnings": []
            }
            
            # Проверки здоровья
            if memory_info.get("utilization_percent", 0) > 95:
                device_stats["warnings"].append("Критическое использование памяти")
                device_stats["healthy"] = False
            
            if temperature and temperature > 85:
                device_stats["warnings"].append(f"Высокая температура: {temperature}°C")
                device_stats["healthy"] = False
            
            if not device_stats["healthy"]:
                health_stats["healthy"] = False
            
            health_stats["devices"].append(device_stats)
        
        return health_stats
    
    def get_optimizer_stats(self) -> Dict:
        """
        Получение статистики оптимизатора
        
        Returns:
            Dict: Статистика работы оптимизатора
        """
        
        runtime = datetime.now() - self.stats["start_time"]
        
        stats = {
            "gpu_available": self.gpu_available,
            "gpu_count": self.gpu_count,
            "memory_cleanups": self.stats["memory_cleanups"],
            "optimization_cycles": self.stats["optimization_cycles"],
            "peak_memory_usage": self.stats["peak_memory_usage"],
            "runtime_hours": runtime.total_seconds() / 3600,
            "gpu_info": self.gpu_info
        }
        
        return stats
    
    def cleanup(self):
        """Очистка ресурсов при завершении"""
        logger.info("🧹 Очистка GPU Optimizer")
        
        if self.gpu_available:
            self.cleanup_gpu_memory()  # Финальная очистка
        
        # Статистика
        stats = self.get_optimizer_stats()
        logger.info(f"📊 Очисток памяти: {stats['memory_cleanups']}")
        logger.info(f"📊 Циклов оптимизации: {stats['optimization_cycles']}")
        logger.info(f"📊 Пиковое использование: {stats['peak_memory_usage']:.1f}%")


def test_gpu_optimizer():
    """Тестирование GPUOptimizer"""
    
    print("🧪 ТЕСТИРОВАНИЕ GPU OPTIMIZER")
    print("=" * 50)
    
    try:
        optimizer = GPUOptimizer()
        
        print(f"🚀 GPU доступно: {optimizer.gpu_available}")
        print(f"🔢 Количество GPU: {optimizer.gpu_count}")
        print()
        
        if optimizer.gpu_available:
            # Информация о GPU
            print("🎯 ИНФОРМАЦИЯ О GPU:")
            for gpu in optimizer.gpu_info:
                print(f"  GPU {gpu['device_id']}: {gpu['name']} ({gpu['total_memory_gb']:.1f}GB)")
            print()
            
            # Мониторинг здоровья
            health = optimizer.monitor_gpu_health()
            print(f"💚 Здоровье системы: {'✅ Здоров' if health['healthy'] else '❌ Проблемы'}")
            
            for device in health["devices"]:
                status = "✅" if device["healthy"] else "❌"
                print(f"  {status} GPU {device['device_id']}: {device['name']}")
                if device.get("temperature"):
                    print(f"    🌡️ Температура: {device['temperature']}°C")
                if device.get("utilization"):
                    print(f"    ⚡ Утилизация: {device['utilization']}%")
                print(f"    💾 Память: {device['memory_utilization']:.1f}%")
                
                if device["warnings"]:
                    for warning in device["warnings"]:
                        print(f"    ⚠️ {warning}")
            print()
            
            # Тест оптимизации
            print("🔧 ТЕСТИРОВАНИЕ ОПТИМИЗАЦИЙ:")
            optimizer.optimize_for_inference()
            optimizer.cleanup_gpu_memory()
            
            # Рекомендации по батчу
            batch_size = optimizer.get_optimal_batch_size(0, model_memory_gb=3.0)
            print(f"📊 Рекомендуемый размер батча: {batch_size}")
        
        else:
            print("💻 GPU недоступны, оптимизатор работает в режиме совместимости")
        
        # Статистика
        print("\n📊 СТАТИСТИКА:")
        stats = optimizer.get_optimizer_stats()
        for key, value in stats.items():
            if key != "gpu_info":  # Пропускаем детальную информацию
                if isinstance(value, float):
                    print(f"  {key}: {value:.2f}")
                else:
                    print(f"  {key}: {value}")
        
        # Очистка
        optimizer.cleanup()
        print("\n✅ Тестирование завершено!")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        raise


if __name__ == "__main__":
    test_gpu_optimizer()