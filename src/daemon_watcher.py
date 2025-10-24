"""
Daemon-watcher для непрерывного мониторинга input/ и обработки файлов.
"""

import logging
import queue
import signal
import sys
import threading
import time
from pathlib import Path
from typing import Optional

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from src.audio_preprocessor import AudioPreprocessor
from src.asr import ASREngine
from src.cleanup_manager import CleanupManager
from src.config_validation import AppConfig
from src.vllm_postprocessor import VLLMPostprocessor

logger = logging.getLogger(__name__)


class AudioFileHandler(FileSystemEventHandler):
    """Handler для событий файловой системы."""

    def __init__(self, file_queue: queue.Queue, allowed_extensions: list):
        """
        Инициализация handler'а.

        Args:
            file_queue: Очередь для обработки файлов
            allowed_extensions: Разрешённые расширения файлов
        """
        super().__init__()
        self.file_queue = file_queue
        self.allowed_extensions = allowed_extensions

    def on_created(self, event):
        """Обработка события создания файла."""
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Проверка расширения
        if file_path.suffix.lower() in self.allowed_extensions:
            logger.info(f"Обнаружен новый файл: {file_path.name}")
            self.file_queue.put(file_path)
        else:
            logger.debug(f"Пропущен файл с неподдерживаемым расширением: {file_path.name}")


class DaemonWatcher:
    """Daemon для непрерывного мониторинга и обработки аудиофайлов."""

    def __init__(self, config: AppConfig):
        """
        Инициализация daemon.

        Args:
            config: Конфигурация приложения
        """
        self.config = config
        self.running = False
        self.file_queue = queue.Queue()

        # Инициализация компонентов
        from src.utils import GPUMonitor

        self.gpu_monitor = GPUMonitor(gpu_index=0)
        self.audio_preprocessor = AudioPreprocessor(config.asr)
        self.asr_engine = ASREngine(config.asr, self.gpu_monitor)
        self.vllm_postprocessor = VLLMPostprocessor(config.vllm)
        self.cleanup_manager = CleanupManager(config.cleanup, config.paths)
        
        # Анализатор качества (опционально)
        self.quality_analyzer = None
        if config.quality_analysis.enabled and config.quality_analysis.auto_analyze:
            from src.quality_analyzer import QualityAnalyzer
            self.quality_analyzer = QualityAnalyzer(config.quality_analysis, config.vllm)
            logger.info("✓ Автоанализ качества включен")
        
        # Аналитика ошибок (опционально)
        self.error_extractor = None
        if config.analytics.enabled and self.quality_analyzer:
            from src.error_extractor import ErrorExtractor
            self.error_extractor = ErrorExtractor(config.analytics.db_path)
            logger.info("✓ Аналитика ошибок включена")
        
        # Google Sheets интегратор (опционально)
        self.sheets_integrator = None
        if config.google_sheets.enabled:
            from src.google_sheets_integrator import GoogleSheetsIntegrator
            self.sheets_integrator = GoogleSheetsIntegrator(
                config.google_sheets.credentials_path,
                config.google_sheets.spreadsheet_id,
                config.analytics.db_path,
            )
            logger.info("✓ Google Sheets интеграция включена (real-time)")

        # Watchdog observer
        self.observer = Observer()
        handler = AudioFileHandler(
            self.file_queue, config.security.allowed_extensions
        )
        self.observer.schedule(handler, str(config.paths.input), recursive=False)

        # Graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        # Статистика
        self.stats = {
            "processed_count": 0,
            "error_count": 0,
            "total_audio_duration": 0.0,
            "total_processing_time": 0.0,
            "start_time": time.time(),
        }

        logger.info("✓ DaemonWatcher инициализирован")

    def _signal_handler(self, signum, frame):
        """Обработка сигналов для graceful shutdown."""
        logger.warning(f"Получен сигнал {signum}, начинаю graceful shutdown...")
        self.stop()

    def start(self):
        """Запустить daemon в режиме непрерывного мониторинга."""
        if self.running:
            logger.warning("Daemon уже запущен")
            return

        logger.info("🚀 Запуск daemon watcher...")

        # Проверка VLLM
        if self.config.vllm.enabled:
            if not self.vllm_postprocessor.health_check():
                logger.error("VLLM недоступен! Проверьте, запущен ли сервер на порту 8000")
                sys.exit(1)

        self.running = True

        # Запуск watchdog
        self.observer.start()
        logger.info(f"✓ Мониторинг директории: {self.config.paths.input}")

        # Обработка существующих файлов в input/
        self._process_existing_files()

        # Запуск worker thread для обработки очереди
        worker_thread = threading.Thread(target=self._worker, daemon=False)
        worker_thread.start()

        # Запуск планировщика автоочистки
        cleanup_thread = threading.Thread(target=self._cleanup_scheduler, daemon=True)
        cleanup_thread.start()

        # Запуск планировщика ежедневной синхронизации Dashboard (23:00)
        if self.config.google_sheets.enabled:
            sync_thread = threading.Thread(target=self._daily_sync_scheduler, daemon=True)
            sync_thread.start()
            logger.info("✓ Планировщик ежедневной синхронизации Dashboard: 23:00")

        logger.info("✓ Daemon watcher запущен успешно")

        try:
            # Основной цикл (ожидание)
            while self.running:
                time.sleep(1)

        except KeyboardInterrupt:
            logger.warning("Получен Ctrl+C, остановка daemon...")
            self.stop()

        finally:
            worker_thread.join(timeout=30)

    def stop(self):
        """Остановить daemon (graceful shutdown)."""
        if not self.running:
            return

        logger.info("Остановка daemon watcher...")
        self.running = False

        # Остановка watchdog
        self.observer.stop()
        self.observer.join()

        # Ожидание завершения обработки оставшихся файлов
        logger.info(f"Ожидание завершения обработки ({self.file_queue.qsize()} файлов в очереди)...")
        time.sleep(2)

        # Вывод финальной статистики
        self._print_stats()

        logger.info("✓ Daemon остановлен")

    def _process_existing_files(self):
        """Обработать существующие файлы в input/ при старте."""
        input_path = Path(self.config.paths.input)
        output_path = Path(self.config.paths.output)
        
        existing_files = [
            f
            for f in input_path.iterdir()
            if f.is_file() and f.suffix.lower() in self.config.security.allowed_extensions
        ]

        if existing_files:
            logger.info(f"Обнаружено {len(existing_files)} файлов в input/")
            
            # Фильтрация: пропускаем уже обработанные файлы
            new_files = []
            skipped = 0
            
            for file_path in existing_files:
                # Проверка: существует ли транскрипция в output/
                transcription_file = output_path / f"{file_path.stem}.txt"
                
                if transcription_file.exists():
                    logger.info(f"Пропущено (уже обработано): {file_path.name}")
                    skipped += 1
                else:
                    new_files.append(file_path)
            
            if new_files:
                logger.info(f"Новых файлов для обработки: {len(new_files)}")
                for file_path in new_files:
                    self.file_queue.put(file_path)
            else:
                logger.info(f"Все файлы уже обработаны (пропущено: {skipped})")

    def _worker(self):
        """Worker thread для обработки очереди файлов."""
        logger.info("✓ Worker thread запущен")

        while self.running or not self.file_queue.empty():
            try:
                # Получение файла из очереди (таймаут 1 сек)
                try:
                    file_path = self.file_queue.get(timeout=1)
                except queue.Empty:
                    continue

                # Обработка файла
                self._process_file(file_path)
                self.file_queue.task_done()

            except Exception as e:
                logger.error(f"Ошибка в worker thread: {e}", exc_info=True)
                self.stats["error_count"] += 1

        logger.info("Worker thread завершён")

    def _process_file(self, file_path: Path):
        """
        Полная обработка одного аудиофайла.

        Args:
            file_path: Путь к аудиофайлу
        """
        logger.info(f"━━━━ Обработка файла: {file_path.name} ━━━━")
        start_time = time.time()

        try:
            # 1. Проверка размера файла
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            if file_size_mb > self.config.security.max_file_size_mb:
                logger.error(
                    f"Файл слишком большой: {file_size_mb:.2f} MB "
                    f"(лимит: {self.config.security.max_file_size_mb} MB)"
                )
                self._move_to_quarantine(file_path, "TOO_LARGE")
                return

            # 2. Предобработка аудио
            try:
                preprocessed_audio = self.audio_preprocessor.preprocess(str(file_path))
                audio_duration = self.audio_preprocessor.get_audio_duration(str(file_path))
            except ValueError as e:
                # Битый/повреждённый аудиофайл
                if "CORRUPTED_AUDIO" in str(e):
                    logger.warning(f"⚠️ Битый аудиофайл, перемещаю в карантин: {file_path.name}")
                    self._move_to_quarantine(file_path, "CORRUPTED")
                    return
                else:
                    raise  # Другие ValueError пробрасываем дальше

            # 3. ASR транскрипция
            raw_transcription, asr_metrics = self.asr_engine.transcribe(
                preprocessed_audio, audio_duration
            )

            # Удаление временного файла
            Path(preprocessed_audio).unlink(missing_ok=True)

            if not raw_transcription:
                logger.warning(f"Пустая транскрипция для {file_path.name}")
                return

            # 4. VLLM постобработка
            cleaned_text, classification = self.vllm_postprocessor.process(
                raw_transcription, file_path.name
            )

            # 5. Сохранение результатов
            self._save_results(file_path, cleaned_text, classification, asr_metrics)

            # 5.5. Анализ качества (если включен автоанализ)
            if self.quality_analyzer:
                try:
                    # Пути к сохранённым файлам
                    output_path = Path(self.config.paths.output) / f"{file_path.stem}.txt"
                    metadata_path = Path(self.config.paths.metadata) / f"{file_path.stem}.json"
                    
                    # Анализ качества
                    quality_result = self.quality_analyzer.analyze_call(
                        str(output_path),
                        str(metadata_path) if metadata_path.exists() else None
                    )
                    
                    # Сохранение
                    self.quality_analyzer.save_analysis(quality_result, file_path.stem)
                    
                    logger.info(
                        f"✓ Анализ качества: {quality_result['overall_score']:.1f}/100"
                    )
                    
                    # 5.6. Извлечение и сохранение ошибок в аналитику
                    if self.error_extractor:
                        try:
                            events = self.error_extractor.extract_errors(
                                quality_result, cleaned_text
                            )
                            self.error_extractor.save_to_db(events)
                            self.error_extractor.save_call_summary(quality_result)
                            
                            if events:
                                logger.info(f"✓ Ошибок зафиксировано: {len(events)}")
                        except Exception as e:
                            logger.error(f"Ошибка сохранения ошибок в аналитику: {e}")
                    
                    # 5.7. Real-time обновление Google Sheets (если включено)
                    if self.sheets_integrator:
                        try:
                            # Подготовка данных для Google Sheets
                            call_row = self._prepare_sheets_row(
                                file_path, quality_result, asr_metrics, cleaned_text
                            )
                            self.sheets_integrator.add_call_realtime(call_row)
                        except Exception as e:
                            logger.error(f"Ошибка обновления Google Sheets: {e}")
                    
                except Exception as e:
                    logger.error(f"Ошибка анализа качества для {file_path.name}: {e}")

            # 6. Автоочистка: перемещение в архив
            if self.config.cleanup.enabled:
                self.cleanup_manager.move_to_archive(file_path)

            # Статистика
            elapsed = time.time() - start_time
            self.stats["processed_count"] += 1
            self.stats["total_processing_time"] += elapsed
            if audio_duration:
                self.stats["total_audio_duration"] += audio_duration

            logger.info(
                f"✅ Файл обработан успешно за {elapsed:.2f}s: {file_path.name}"
            )

        except Exception as e:
            logger.error(f"❌ Ошибка обработки {file_path.name}: {e}", exc_info=True)
            self.stats["error_count"] += 1
            # Перемещаем проблемный файл в карантин, чтобы не блокировать очередь
            self._move_to_quarantine(file_path, "ERROR")

    def _move_to_quarantine(self, file_path: Path, reason: str):
        """
        Переместить файл в карантин.

        Args:
            file_path: Путь к файлу
            reason: Причина (CORRUPTED, TOO_LARGE, ERROR)
        """
        try:
            quarantine_dir = Path("quarantine")
            quarantine_dir.mkdir(exist_ok=True)
            
            # Добавляем причину в имя файла
            quarantine_file = quarantine_dir / f"{reason}_{file_path.name}"
            
            # Перемещение
            import shutil
            shutil.move(str(file_path), str(quarantine_file))
            
            logger.warning(f"🗑️ Файл перемещён в карантин: {quarantine_file}")
            
        except Exception as e:
            logger.error(f"Не удалось переместить в карантин {file_path.name}: {e}")

    def _save_results(
        self, file_path: Path, text: str, classification: Optional[dict], metrics: dict
    ):
        """
        Сохранить результаты обработки.

        Args:
            file_path: Исходный путь к файлу
            text: Очищенный текст транскрипции
            classification: Классификация звонка
            metrics: Метрики ASR
        """
        import json

        # Имя файла без расширения
        base_name = file_path.stem

        # 1. Сохранение текста транскрипции
        output_path = Path(self.config.paths.output) / f"{base_name}.txt"
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        logger.info(f"Транскрипция сохранена: {output_path.name}")

        # 2. Сохранение метаданных (если есть классификация)
        if classification:
            metadata = {
                "filename": file_path.name,
                "processed_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "classification": classification,
                "asr_metrics": metrics,
            }

            metadata_path = Path(self.config.paths.metadata) / f"{base_name}.json"
            with open(metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            logger.info(f"Метаданные сохранены: {metadata_path.name}")

    def _cleanup_scheduler(self):
        """Планировщик автоочистки (ежедневно в указанное время)."""
        logger.info(
            f"✓ Планировщик автоочистки запущен: {self.config.cleanup.schedule_hour:02d}:00"
        )

        while self.running:
            current_hour = int(time.strftime("%H"))

            # Запуск очистки в указанный час
            if current_hour == self.config.cleanup.schedule_hour:
                logger.info("⏰ Запуск плановой автоочистки...")
                stats = self.cleanup_manager.rotate_archive()
                logger.info(f"Автоочистка завершена: {stats}")

                # Проверка заполнения диска
                if self.cleanup_manager.check_disk_space():
                    self.cleanup_manager.emergency_cleanup()

                # Спим до следующего дня
                time.sleep(3600)

            time.sleep(60)  # Проверка каждую минуту

    def _daily_sync_scheduler(self):
        """Планировщик ежедневной синхронизации Dashboard (23:00)."""
        logger.info("✓ Планировщик ежедневной синхронизации Dashboard запущен: 23:00")
        
        last_sync_date = None

        while self.running:
            current_hour = int(time.strftime("%H"))
            current_date = time.strftime("%Y-%m-%d")

            # Запуск синхронизации в 23:00 (только один раз в день)
            if current_hour == 23 and last_sync_date != current_date:
                logger.info("⏰ Запуск ежедневной синхронизации Dashboard...")
                
                try:
                    # 1. Генерация витрины дня
                    from src.analytics_aggregator import AnalyticsAggregator
                    
                    aggregator = AnalyticsAggregator(
                        db_path=self.config.analytics.db_path,
                        aggregates_path="./analytics/aggregates"
                    )
                    
                    day_aggregate = aggregator.aggregate_day()
                    logger.info(f"✓ Витрина дня создана: {day_aggregate['total_calls']} звонков")
                    
                    # 2. Обновление Dashboard в Google Sheets
                    if self.sheets_integrator:
                        self.sheets_integrator.update_dashboard(day_aggregate)
                        logger.info("✓ Dashboard в Google Sheets обновлён")
                    
                    last_sync_date = current_date
                    logger.info("✓ Ежедневная синхронизация Dashboard завершена")
                    
                except Exception as e:
                    logger.error(f"Ошибка ежедневной синхронизации Dashboard: {e}", exc_info=True)
                
                # Спим до следующего дня (чтобы не запускать повторно)
                time.sleep(3600)

            time.sleep(60)  # Проверка каждую минуту

    def _prepare_sheets_row(self, file_path, quality_result, asr_metrics, transcription):
        """
        Подготовить строку данных для Google Sheets.

        Args:
            file_path: Путь к аудиофайлу
            quality_result: Результат анализа качества
            asr_metrics: Метрики ASR
            transcription: Текст транскрипции

        Returns:
            Dict: Данные для Google Sheets
        """
        from datetime import datetime

        # Подсчёт ошибок
        critical_errors_count = 0
        optional_errors_count = 0
        
        for criterion in quality_result.get("criteria_evaluations", []):
            param_id = criterion.get("id")
            score = criterion.get("score")
            relevant = criterion.get("relevant", True)
            
            is_error = (relevant and score is not None and score < 1.0) or (not relevant and score is None)
            
            if is_error:
                if param_id <= 20:  # required
                    critical_errors_count += 1
                else:  # optional
                    optional_errors_count += 1
        
        # Длительность (защита от None)
        audio_duration = asr_metrics.get("audio_duration") or 0
        if audio_duration and audio_duration > 0:
            minutes = int(audio_duration // 60)
            seconds = int(audio_duration % 60)
            duration_str = f"{minutes}:{seconds:02d}"
        else:
            duration_str = "N/A"
        
        # Timestamp
        dt = datetime.now()
        
        # Базовые данные
        row_data = [
            dt.strftime("%d.%m.%Y"),  # Дата
            dt.strftime("%H:%M"),  # Время
            quality_result.get("admin_name") or "Неизвестен",  # Админ
            quality_result.get("clinic_address") or "N/A",  # Филиал
            quality_result.get("equipment_type") or "Type-A",  # Оборудование
            duration_str,  # Длительность
            quality_result.get("overall_score", 0),  # Общий балл
            critical_errors_count + optional_errors_count,  # Ошибок всего
        ]
        
        # Добавляем все 30 критериев (балл + комментарий в скобках)
        # Сортируем по id
        criteria_map = {}
        for criterion in quality_result.get("criteria_evaluations", []):
            criteria_map[criterion.get("id")] = criterion
        
        # Заполняем все 30 критериев по порядку
        for i in range(1, 31):
            if i in criteria_map:
                criterion = criteria_map[i]
                score = criterion.get("score")
                comment = criterion.get("comment", "")
                
                # Формат: "балл (комментарий)" или "N/A (комментарий)" если неприменимо
                relevant = criterion.get("relevant", True)
                
                # Комментарий до 250 символов (полные комментарии для анализа)
                short_comment = comment[:250] + "..." if len(comment) > 250 else comment
                
                if not relevant:
                    # Неприменимый критерий - показываем комментарий с пометкой N/A
                    cell_value = f"N/A ({short_comment})" if comment else "N/A"
                elif score is None:
                    # Score отсутствует, но критерий применим - показываем комментарий
                    cell_value = f"- ({short_comment})" if comment else "-"
                else:
                    # Обычный критерий с баллом
                    cell_value = f"{score:.1f} ({short_comment})" if comment else f"{score:.1f}"
                
                row_data.append(cell_value)
            else:
                row_data.append("-")  # Критерий не найден
        
        # Добавляем пути к файлам в конце
        row_data.append(f"output/{file_path.stem}.txt")  # Транскрипция
        row_data.append(f"quality_analysis/individual/{file_path.stem}.json")  # JSON
        
        return {
            "call_id": quality_result.get("call_id"),
            "row_data": row_data
        }

    def _print_stats(self):
        """Вывести статистику работы daemon."""
        uptime = time.time() - self.stats["start_time"]
        avg_rtf = (
            self.stats["total_processing_time"] / self.stats["total_audio_duration"]
            if self.stats["total_audio_duration"] > 0
            else 0
        )

        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        logger.info("📊 Статистика работы:")
        logger.info(f"  Uptime: {uptime/3600:.2f} часов")
        logger.info(f"  Обработано файлов: {self.stats['processed_count']}")
        logger.info(f"  Ошибок: {self.stats['error_count']}")
        logger.info(
            f"  Общая длительность аудио: {self.stats['total_audio_duration']/60:.2f} минут"
        )
        logger.info(
            f"  Общее время обработки: {self.stats['total_processing_time']:.2f} сек"
        )
        logger.info(f"  Средний RTF: {avg_rtf:.4f}")
        logger.info("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

