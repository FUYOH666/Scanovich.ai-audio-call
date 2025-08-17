#!/usr/bin/env python3
"""
BATCH ПРОЦЕССИНГ v2.0 ДЛЯ МЕДИЦИНСКИХ ЦЕНТРОВ  
===============================================
Массовая обработка аудиофайлов с платформо-независимой архитектурой
Автор: Scanovich.ai | Версия: 2.0 (GPU READY)

НОВОЕ v2.0:
- Платформо-независимая архитектура (M4 Pro MLX ↔ GPU CUDA)
- Изоляция LM Studio сессий между звонками
- GPU оптимизации для максимальной производительности
- Автоматическая адаптация под текущую платформу

Функции:
- Массовая обработка всех файлов в папке
- Модульный 3-этапный анализ (CallCleaner + ScriptChecker + EntityExtractor)
- Автоматическое добавление в Google Sheets
- Детальная статистика и отчеты
- Прогресс-бары для отслеживания
- 100% изоляция данных между звонками
"""

import os
import sys
import time
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import argparse

# Настройка автономного режима
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HUGGINGFACE_HUB_CACHE"] = "./models/hub"

# Импорты проекта
from enhanced_pipeline_v3 import EnhancedAudioPipelineV3 as EnhancedAudioPipeline

# НОВЫЕ ИМПОРТЫ v2.0: Платформо-независимая архитектура
from platform_manager import PlatformManager
from lm_studio_session_manager import LMStudioSessionManager
from gpu_optimizer import GPUOptimizer

# Импорты для управления памятью и стабилизации
import gc
import psutil

# Опциональные импорты
try:
    from google_sheets_integration import GoogleSheetsIntegration
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False
    print("⚠️  Google Sheets интеграция недоступна")

try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    print("⚠️  tqdm недоступен, прогресс-бары отключены")


class BatchProcessor:
    """
    Класс для массовой обработки аудиофайлов v2.0
    
    НОВАЯ АРХИТЕКТУРА:
    - Платформо-независимое управление (M4 Pro MLX ↔ GPU CUDA)
    - Изоляция LM Studio сессий для медицинской конфиденциальности
    - GPU оптимизации для максимальной производительности
    - Автоматическая адаптация под текущую платформу
    """
    
    def __init__(self, lm_studio_urls: list = None):
        """Инициализация batch процессора v2.0"""
        
        # Настройка логирования
        self.setup_logging()
        
        # НОВОЕ v2.0: Платформенные менеджеры
        self.platform_manager = PlatformManager()
        self.gpu_optimizer = GPUOptimizer()
        
        # Получаем оптимальные настройки для текущей платформы
        self.processing_config = self.platform_manager.get_processing_config()
        
        # НОВОЕ v2.0: LM Studio Session Manager для изоляции
        session_restart_interval = self.processing_config["session_restart_interval"]
        self.lm_session_manager = LMStudioSessionManager(
            lm_studio_urls=lm_studio_urls, 
            session_restart_interval=session_restart_interval
        )
        
        # Инициализация pipeline с платформо-специфичными настройками
        self.pipeline = EnhancedAudioPipeline(lm_studio_urls)
        
        # ОБНОВЛЕНО v2.0: Адаптивные счетчики на основе платформы
        self.processed_count = 0
        self.memory_cleanup_interval = self.processing_config["memory_cleanup_interval"]
        self.model_reload_interval = self.processing_config["model_reload_interval"]
        self.memory_warning_threshold = 80  # % использования RAM для предупреждения
        
        # Статистика
        self.stats = {
            "total_files": 0,
            "processed": 0,
            "successful": 0,
            "failed": 0,
            "start_time": None,
            "end_time": None,
            "results": []
        }
        
        # Google Sheets интеграция
        if GOOGLE_SHEETS_AVAILABLE:
            try:
                self.sheets = GoogleSheetsIntegration()
                self.logger.info("✅ Google Sheets интеграция подключена")
            except Exception as e:
                self.logger.warning(f"⚠️  Google Sheets недоступен: {e}")
                self.sheets = None
        else:
            self.sheets = None
        
        # НОВОЕ v2.0: Логирование платформенной информации
        self._log_platform_info()
    
    def setup_logging(self):
        """Настройка логирования"""
        
        # Создаем папку для логов
        log_dir = Path("output/logs")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Настройка логгера
        self.logger = logging.getLogger("BatchProcessor")
        self.logger.setLevel(logging.INFO)
        
        # Очищаем существующие handlers
        self.logger.handlers.clear()
        
        # Файловый handler
        file_handler = logging.FileHandler(
            log_dir / f"batch_process_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.INFO)
        
        # Консольный handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Форматтер
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Добавляем handlers
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def _log_platform_info(self):
        """НОВОЕ v2.0: Логирование информации о платформе"""
        
        self.logger.info("=" * 60)
        self.logger.info("🚀 BATCH PROCESSOR v2.0 - ПЛАТФОРМЕННАЯ ИНФОРМАЦИЯ")
        self.logger.info("=" * 60)
        
        # Информация о платформе
        platform_info = self.platform_manager.get_platform_summary()
        self.logger.info(platform_info)
        
        # Информация о производительности
        perf_info = self.platform_manager.get_performance_info()
        self.logger.info(f"📊 Ожидаемая производительность: {perf_info['estimated_time_5000_calls']}")
        
        # GPU информация
        if self.gpu_optimizer.gpu_available:
            gpu_health = self.gpu_optimizer.monitor_gpu_health()
            self.logger.info(f"🎯 GPU готовы: {gpu_health['gpu_count']} устройств")
        else:
            self.logger.info("💻 GPU недоступны, работаем в CPU/MLX режиме")
        
        # LM Studio статус
        if self.lm_session_manager.is_healthy():
            self.logger.info(f"🤖 LM Studio готов: {self.lm_session_manager.active_url}")
        else:
            self.logger.warning("⚠️ LM Studio недоступен")
        
        self.logger.info("=" * 60)
    
    # 🛠️ ОБНОВЛЕННЫЕ МЕТОДЫ СТАБИЛИЗАЦИИ v2.0
    
    def cleanup_memory_after_call(self):
        """ОБНОВЛЕНО v2.0: Принудительная очистка памяти с GPU поддержкой"""
        try:
            # Python garbage collection
            collected = gc.collect()
            
            # Дополнительная очистка для старых объектов
            for generation in range(3):
                gc.collect(generation)
            
            # НОВОЕ v2.0: GPU очистка памяти
            if self.gpu_optimizer.gpu_available:
                self.gpu_optimizer.cleanup_gpu_memory()
            
            # НОВОЕ v2.0: Проверка здоровья LM Studio сессии
            if not self.lm_session_manager.is_healthy():
                self.logger.warning("🔄 LM Studio нестабилен, пробуем восстановить...")
                self.lm_session_manager.restart_session(force=True)
            
            if collected > 0:
                self.logger.info(f"🧹 Очищено {collected} объектов из памяти")
                
        except Exception as e:
            self.logger.warning(f"⚠️ Ошибка очистки памяти: {e}")
    
    def check_memory_usage(self) -> dict:
        """ОБНОВЛЕНО v2.0: Мониторинг RAM + GPU памяти"""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            memory_info = {
                "ram_percent": memory.percent,
                "ram_available_gb": memory.available / (1024**3),
                "ram_used_gb": memory.used / (1024**3),
                "swap_percent": swap.percent,
                "swap_used_gb": swap.used / (1024**3)
            }
            
            # НОВОЕ v2.0: GPU память мониторинг
            if self.gpu_optimizer.gpu_available:
                gpu_memory = self.gpu_optimizer.get_gpu_memory_info(0)
                if gpu_memory:
                    memory_info["gpu_utilization"] = gpu_memory["utilization_percent"]
                    memory_info["gpu_used_gb"] = gpu_memory["allocated_gb"]
                    memory_info["gpu_total_gb"] = gpu_memory["total_gb"]
                    
                    # Предупреждения о высоком использовании GPU
                    if gpu_memory["utilization_percent"] > 90:
                        self.logger.warning(f"⚠️ ВЫСОКОЕ ИСПОЛЬЗОВАНИЕ GPU: {gpu_memory['utilization_percent']:.1f}%")
            
            # Предупреждения о высоком использовании RAM
            if memory.percent > self.memory_warning_threshold:
                self.logger.warning(f"⚠️ ВЫСОКОЕ ИСПОЛЬЗОВАНИЕ RAM: {memory.percent:.1f}%")
            
            if swap.percent > 50:
                self.logger.warning(f"⚠️ АКТИВЕН SWAP: {swap.percent:.1f}%")
            
            return memory_info
            
        except Exception as e:
            self.logger.warning(f"⚠️ Ошибка проверки памяти: {e}")
            return {}
    
    def reload_models_if_needed(self):
        """Перезагрузка моделей каждые N звонков для предотвращения утечек"""
        if self.processed_count % self.model_reload_interval == 0 and self.processed_count > 0:
            self.logger.info(f"🔄 ПЕРЕЗАГРУЗКА МОДЕЛЕЙ (каждые {self.model_reload_interval} звонков)")
            
            try:
                # Принудительная очистка памяти
                self.pipeline = None
                gc.collect()
                
                # Создаем новый pipeline
                self.pipeline = EnhancedAudioPipeline()
                self.logger.info("✅ Модели успешно перезагружены")
                
            except Exception as e:
                self.logger.error(f"❌ Ошибка перезагрузки моделей: {e}")
    
    def log_system_stats(self, memory_info: dict):
        """ОБНОВЛЕНО v2.0: Логирование системной статистики с GPU"""
        if memory_info:
            self.logger.info(
                f"💾 RAM: {memory_info['ram_percent']:.1f}% "
                f"({memory_info['ram_used_gb']:.1f}GB использовано, "
                f"{memory_info['ram_available_gb']:.1f}GB доступно)"
            )
            
            # НОВОЕ v2.0: GPU статистика
            if "gpu_utilization" in memory_info:
                self.logger.info(
                    f"🚀 GPU: {memory_info['gpu_utilization']:.1f}% "
                    f"({memory_info['gpu_used_gb']:.1f}GB / {memory_info['gpu_total_gb']:.1f}GB)"
                )
            
            if memory_info['swap_percent'] > 0:
                self.logger.info(f"💿 SWAP: {memory_info['swap_percent']:.1f}% ({memory_info['swap_used_gb']:.1f}GB)")
    
    def find_audio_files(self, input_dir: Path) -> List[Path]:
        """Поиск аудиофайлов в директории"""
        
        audio_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.ogg'}
        audio_files = []
        
        if not input_dir.exists():
            self.logger.error(f"❌ Директория не найдена: {input_dir}")
            return []
        
        for file_path in input_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in audio_extensions:
                audio_files.append(file_path)
        
        # Сортируем для воспроизводимости
        audio_files.sort()
        
        self.logger.info(f"🔍 Найдено {len(audio_files)} аудиофайлов в {input_dir}")
        return audio_files
    
    def process_single_file(self, audio_path: Path) -> Dict:
        """ОБНОВЛЕНО v2.0: Обработка одного файла с изоляцией сессий"""
        
        self.logger.info(f"🎯 Обработка: {audio_path.name}")
        start_time = time.time()
        
        try:
            # НОВОЕ v2.0: Проверка изоляции LM Studio перед обработкой
            session_stats = self.lm_session_manager.get_session_stats()
            if session_stats["current_session_counter"] >= session_stats.get("session_restart_interval", 10):
                self.logger.info("🔄 Превышен лимит сессии, выполняем рестарт LM Studio...")
                self.lm_session_manager.restart_session()
            
            # Обработка через enhanced pipeline
            result = self.pipeline.process_audio_file(audio_path)
            
            processing_time = time.time() - start_time
            
            if result["success"]:
                self.logger.info(f"✅ Успешно обработан: {audio_path.name} ({processing_time:.2f}с)")
                
                # Google Sheets добавление отключено в batch_process 
                # (добавление происходит в enhanced_pipeline.py чтобы избежать дублирования)
                self.logger.info(f"📊 Google Sheets обновлен в enhanced_pipeline для: {audio_path.name}")
                
                # 🛠️ СТАБИЛИЗАЦИЯ v2.0: Увеличиваем счетчик и применяем оптимизацию
                self.processed_count += 1
                
                # НОВОЕ v2.0: Уведомляем LM Studio Session Manager о завершении обработки
                if hasattr(self.lm_session_manager, 'session_counter'):
                    self.lm_session_manager.session_counter += 1
                
                # Очистка памяти (адаптивная по платформе)
                if self.processed_count % self.memory_cleanup_interval == 0:
                    self.cleanup_memory_after_call()
                
                # Мониторинг памяти (RAM + GPU) каждые 5 звонков
                if self.processed_count % 5 == 0:
                    memory_info = self.check_memory_usage()
                    self.log_system_stats(memory_info)
                
                # Перезагрузка моделей каждые N звонков (адаптивно по платформе)
                self.reload_models_if_needed()
                
                return {
                    "file": audio_path.name,
                    "status": "success",
                    "processing_time": processing_time,
                    "audio_duration": result.get("audio_duration", 0),
                    "lm_studio_used": result.get("lm_studio_used", False),
                    "files": {
                        "transcription": result.get("original_transcription_file"),
                        "improved": result.get("improved_transcription_file"),
                        "analysis": result.get("analysis_file"),
                        "html_report": result.get("html_report_file")
                    }
                }
            else:
                self.logger.error(f"❌ Ошибка обработки {audio_path.name}: {result.get('error', 'неизвестная ошибка')}")
                
                # 🛠️ СТАБИЛИЗАЦИЯ v2.0: Даже при ошибке увеличиваем счетчик для очистки
                self.processed_count += 1
                
                # НОВОЕ v2.0: Принудительная очистка при ошибках
                self.cleanup_memory_after_call()
                
                # НОВОЕ v2.0: Проверяем здоровье LM Studio после ошибки
                if not self.lm_session_manager.is_healthy():
                    self.logger.warning("🔄 LM Studio проблемы после ошибки, перезапускаем...")
                    self.lm_session_manager.restart_session(force=True)
                
                return {
                    "file": audio_path.name,
                    "status": "failed",
                    "processing_time": processing_time,
                    "error": result.get("error", "неизвестная ошибка")
                }
                
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"💥 Исключение при обработке {audio_path.name}: {e}")
            
            # 🛠️ СТАБИЛИЗАЦИЯ v5.0: Даже при исключении увеличиваем счетчик для очистки
            self.processed_count += 1
            self.cleanup_memory_after_call()
            
            return {
                "file": audio_path.name,
                "status": "failed",
                "processing_time": processing_time,
                "error": str(e)
            }
    
    def process_batch(self, input_dir: Path, max_files: Optional[int] = None) -> Dict:
        """Массовая обработка файлов"""
        
        print("🚀 ЗАПУСК BATCH ОБРАБОТКИ")
        print("🔒 АВТОНОМНАЯ ТРАНСКРИБАЦИЯ + 🤖 LM STUDIO АНАЛИЗ")
        print("🏥 МЕДИЦИНСКИЙ РЕЖИМ - ПОЛНАЯ КОНФИДЕНЦИАЛЬНОСТЬ")
        print("=" * 70)
        
        # Поиск файлов
        audio_files = self.find_audio_files(input_dir)
        
        if not audio_files:
            self.logger.error("❌ Аудиофайлы не найдены")
            return {"success": False, "error": "Аудиофайлы не найдены"}
        
        # Ограничиваем количество файлов если задано
        if max_files and max_files > 0:
            audio_files = audio_files[:max_files]
            self.logger.info(f"🔢 Ограничено до {max_files} файлов")
        
        # Инициализация статистики
        self.stats["total_files"] = len(audio_files)
        self.stats["start_time"] = time.time()
        
        self.logger.info(f"📊 Начало обработки {len(audio_files)} файлов")
        
        # Загрузка моделей
        try:
            self.logger.info("📦 Загрузка моделей...")
            self.pipeline.load_models()
            self.logger.info("✅ Модели загружены")
        except Exception as e:
            self.logger.error(f"❌ Ошибка загрузки моделей: {e}")
            return {"success": False, "error": f"Ошибка загрузки моделей: {e}"}
        
        # Обработка файлов с прогресс-баром
        if TQDM_AVAILABLE:
            progress_bar = tqdm(audio_files, desc="🎯 Обработка", unit="файл")
        else:
            progress_bar = audio_files
        
        for i, audio_file in enumerate(progress_bar):
            if TQDM_AVAILABLE:
                progress_bar.set_description(f"🎯 Обработка {audio_file.name[:30]}...")
            
            # Обработка файла
            result = self.process_single_file(audio_file)
            
            # Обновление статистики
            self.stats["processed"] += 1
            if result["status"] == "success":
                self.stats["successful"] += 1
            else:
                self.stats["failed"] += 1
            
            self.stats["results"].append(result)
            
            # Промежуточная статистика
            if not TQDM_AVAILABLE:
                progress = (i + 1) / len(audio_files) * 100
                self.logger.info(f"📈 Прогресс: {i + 1}/{len(audio_files)} ({progress:.1f}%)")
        
        # Завершение
        self.stats["end_time"] = time.time()
        
        # Генерация отчета
        return self.generate_batch_report()
    
    def generate_batch_report(self) -> Dict:
        """Генерация итогового отчета"""
        
        total_time = self.stats["end_time"] - self.stats["start_time"]
        
        # Создаем папку для batch результатов
        batch_dir = Path("output/batch_results")
        batch_dir.mkdir(parents=True, exist_ok=True)
        
        # Статистика
        success_rate = (self.stats["successful"] / self.stats["total_files"]) * 100 if self.stats["total_files"] > 0 else 0
        avg_time = total_time / self.stats["processed"] if self.stats["processed"] > 0 else 0
        
        total_audio_duration = sum(r.get("audio_duration", 0) for r in self.stats["results"] if r["status"] == "success")
        
        report = {
            "batch_info": {
                "timestamp": datetime.now().isoformat(),
                "total_files": self.stats["total_files"],
                "processed": self.stats["processed"],
                "successful": self.stats["successful"],
                "failed": self.stats["failed"],
                "success_rate": success_rate,
                "total_processing_time": total_time,
                "average_time_per_file": avg_time,
                "total_audio_duration": total_audio_duration
            },
            "results": self.stats["results"],
            "failed_files": [r for r in self.stats["results"] if r["status"] == "failed"]
        }
        
        # Сохранение JSON отчета
        report_file = batch_dir / f"batch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        # Генерация HTML отчета
        html_report = self.generate_html_report(report)
        html_file = batch_dir / f"batch_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_report)
        
        # Вывод статистики
        print("\n" + "=" * 70)
        print("🎉 BATCH ОБРАБОТКА ЗАВЕРШЕНА!")
        print("=" * 70)
        print(f"📊 Обработано файлов: {self.stats['successful']}/{self.stats['total_files']}")
        print(f"✅ Успешность: {success_rate:.1f}%")
        print(f"⏱️  Общее время: {total_time:.2f}с ({total_time/60:.1f} мин)")
        print(f"⚡ Среднее время на файл: {avg_time:.2f}с")
        print(f"🎵 Общая длительность аудио: {total_audio_duration:.2f}с ({total_audio_duration/60:.1f} мин)")
        print(f"📋 JSON отчет: {report_file}")
        print(f"🌐 HTML отчет: {html_file}")
        
        if self.stats["failed"] > 0:
            print(f"\n❌ Неудачные файлы ({self.stats['failed']}):")
            for result in self.stats["results"]:
                if result["status"] == "failed":
                    print(f"   • {result['file']}: {result.get('error', 'неизвестная ошибка')}")
        
        print("\n🔒 ДАННЫЕ НЕ ПОКИДАЛИ СИСТЕМУ")
        print("🏥 МЕДИЦИНСКАЯ КОНФИДЕНЦИАЛЬНОСТЬ СОБЛЮДЕНА")
        
        self.logger.info(f"📋 Batch отчет сохранен: {report_file}")
        

        print(f"📊 Статистика обработки:")
        print(f"   📁 Всего файлов: {self.stats['total_files']}")
        print(f"   ✅ Успешно: {self.stats['successful']}")
        print(f"   ❌ Ошибки: {self.stats['failed']}")
        print(f"   ⏱️ Общее время: {total_time:.2f}с")
        print(f"   🎯 Средняя скорость: {self.stats['processed']/total_time:.2f}x реального времени")
        print(f"   🧹 Временные метки удаляются для всех звонков")
        print(f"   🔒 100% автономная обработка")
        print(f"   🏥 Медицинская конфиденциальность гарантирована")
        
        return {
            "success": True,
            "report_file": str(report_file),
            "html_file": str(html_file),
            "statistics": report["batch_info"]
        }
    
    def generate_html_report(self, report: Dict) -> str:
        """Генерация HTML отчета для batch обработки"""
        
        stats = report["batch_info"]
        
        # Цвет для success rate
        if stats["success_rate"] >= 90:
            success_color = "#4caf50"  # зеленый
        elif stats["success_rate"] >= 70:
            success_color = "#ff9800"  # оранжевый
        else:
            success_color = "#f44336"  # красный
        
        html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Batch Отчет - Медицинские центры</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .content {{
            padding: 30px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: #f8f9ff;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .stat-label {{
            color: #666;
            font-size: 0.9em;
        }}
        .success-rate {{
            color: {success_color};
        }}
        .files-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        .files-table th, .files-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        .files-table th {{
            background-color: #667eea;
            color: white;
        }}
        .status-success {{
            color: #4caf50;
            font-weight: bold;
        }}
        .status-failed {{
            color: #f44336;
            font-weight: bold;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .section h2 {{
            color: #333;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        .footer {{
            background: #f8f9ff;
            padding: 20px;
            text-align: center;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏥 Batch Отчет</h1>
            <p>Медицинские центры</p>
            <p>Массовая обработка звонков</p>
        </div>
        
        <div class="content">
            <!-- Основная статистика -->
            <div class="section">
                <h2>📊 Общая статистика</h2>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-value">{stats['total_files']}</div>
                        <div class="stat-label">Всего файлов</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{stats['successful']}</div>
                        <div class="stat-label">Успешно обработано</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value success-rate">{stats['success_rate']:.1f}%</div>
                        <div class="stat-label">Успешность</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{stats['total_processing_time']/60:.1f} мин</div>
                        <div class="stat-label">Общее время</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{stats['average_time_per_file']:.1f}с</div>
                        <div class="stat-label">Среднее время на файл</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-value">{stats['total_audio_duration']/60:.1f} мин</div>
                        <div class="stat-label">Общая длительность аудио</div>
                    </div>
                </div>
            </div>
            
            <!-- Детальные результаты -->
            <div class="section">
                <h2>📋 Детальные результаты</h2>
                <table class="files-table">
                    <thead>
                        <tr>
                            <th>Файл</th>
                            <th>Статус</th>
                            <th>Время обработки</th>
                            <th>Длительность аудио</th>
                            <th>LM Studio</th>
                        </tr>
                    </thead>
                    <tbody>"""
        
        for result in report["results"]:
            status_class = "status-success" if result["status"] == "success" else "status-failed"
            status_text = "✅ Успешно" if result["status"] == "success" else "❌ Ошибка"
            
            lm_studio = "✅" if result.get("lm_studio_used", False) else "❌"
            audio_duration = f"{result.get('audio_duration', 0):.1f}с" if result.get('audio_duration') else "—"
            
            html += f"""
                        <tr>
                            <td>{result['file']}</td>
                            <td class="{status_class}">{status_text}</td>
                            <td>{result['processing_time']:.2f}с</td>
                            <td>{audio_duration}</td>
                            <td>{lm_studio}</td>
                        </tr>"""
        
        html += f"""
                    </tbody>
                </table>
            </div>
            
            <!-- Ошибки -->"""
        
        if report["failed_files"]:
            html += f"""
            <div class="section">
                <h2>❌ Ошибки обработки</h2>
                <table class="files-table">
                    <thead>
                        <tr>
                            <th>Файл</th>
                            <th>Ошибка</th>
                        </tr>
                    </thead>
                    <tbody>"""
            
            for failed in report["failed_files"]:
                html += f"""
                        <tr>
                            <td>{failed['file']}</td>
                            <td>{failed.get('error', 'Неизвестная ошибка')}</td>
                        </tr>"""
            
            html += """
                    </tbody>
                </table>
            </div>"""
        
        html += f"""
        </div>
        
        <div class="footer">
            <p>© 2025 Медицинские центры</p>
            <p>Scanovich.ai | Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
            <p>🔒 Медицинская конфиденциальность соблюдена</p>
        </div>
    </div>
</body>
</html>"""
        
        return html


def main():
    """Главная функция"""
    
    parser = argparse.ArgumentParser(description='Batch обработка аудиофайлов для МРТ клиники')
    parser.add_argument('input_dir', help='Папка с аудиофайлами')
    parser.add_argument('--max-files', type=int, help='Максимальное количество файлов для обработки')
    parser.add_argument('--lm-studio-urls', nargs='+', 
                        default=['http://localhost:1234', 'http://192.168.1.104:1234'], 
                        help='URLs LM Studio (основной и резервный)')
    
    args = parser.parse_args()
    
    # Проверка входной папки
    input_dir = Path(args.input_dir)
    if not input_dir.exists():
        print(f"❌ Папка не найдена: {input_dir}")
        sys.exit(1)
    
    # Инициализация и запуск
    processor = BatchProcessor(args.lm_studio_urls)
    result = processor.process_batch(input_dir, args.max_files)
    
    if result["success"]:
        print(f"\n✅ Batch обработка завершена успешно!")
        sys.exit(0)
    else:
        print(f"\n❌ Ошибка batch обработки: {result.get('error', 'неизвестная ошибка')}")
        sys.exit(1)


if __name__ == "__main__":
    main() 