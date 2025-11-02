#!/usr/bin/env python3
"""
ASR-4.5 Production System - CLI Interface
"""

import json
import logging
import sys
from pathlib import Path

import click

# Добавление src/ в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from src.config_validation import AppConfig
from src.utils import ConfigManager, GPUMonitor, setup_logging

logger = logging.getLogger(__name__)


@click.group()
@click.pass_context
def cli(ctx):
    """ASR-4.5 - Production-ready система автоматической транскрипции."""
    ctx.ensure_object(dict)


@cli.command()
@click.option("--config", default="config.yaml", help="Путь к config.yaml")
def run(config):
    """
    Запустить daemon в режиме непрерывного мониторинга input/.

    Daemon будет автоматически обрабатывать новые аудиофайлы,
    отправлять в VLLM для постобработки и архивировать результаты.
    """
    try:
        # Загрузка конфигурации
        config_manager = ConfigManager(config)
        app_config = config_manager.get()

        # Настройка логирования
        setup_logging(app_config)

        logger.info("=" * 60)
        logger.info("ASR-4.5 Production System")
        logger.info("=" * 60)

        # Проверка GPU
        gpu_monitor = GPUMonitor(gpu_index=0)
        gpu_monitor.check_device(app_config.asr.device)

        # Запуск daemon
        from src.daemon_watcher import DaemonWatcher

        daemon = DaemonWatcher(app_config)
        daemon.start()

    except KeyboardInterrupt:
        logger.info("Получен Ctrl+C, остановка...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.argument("audio_file", type=click.Path(exists=True))
@click.option("--config", default="config.yaml", help="Путь к config.yaml")
def process_file(audio_file, config):
    """
    Обработать один аудиофайл.

    Пример:
        ./venv/bin/python main.py process-file input/звонок.mp3
    """
    try:
        # Загрузка конфигурации
        config_manager = ConfigManager(config)
        app_config = config_manager.get()

        # Настройка логирования
        setup_logging(app_config)

        logger.info(f"Обработка файла: {audio_file}")

        # Инициализация компонентов
        from src.audio_preprocessor import AudioPreprocessor
        from src.asr import ASREngine
        from src.vllm_postprocessor import VLLMPostprocessor

        gpu_monitor = GPUMonitor(gpu_index=0)
        gpu_monitor.check_device(app_config.asr.device)

        audio_preprocessor = AudioPreprocessor(app_config.asr)
        asr_engine = ASREngine(app_config.asr, gpu_monitor)
        vllm_postprocessor = VLLMPostprocessor(app_config.vllm)

        # Предобработка
        preprocessed = audio_preprocessor.preprocess(audio_file)
        duration = audio_preprocessor.get_audio_duration(audio_file)

        # ASR
        raw_text, metrics = asr_engine.transcribe(preprocessed, duration)
        logger.info(f"ASR завершён: {len(raw_text)} символов")
        logger.info(f"Метрики: RTF={metrics.get('rtf', 'N/A')}, время={metrics.get('elapsed_time')}s")

        # VLLM постобработка
        cleaned_text, classification = vllm_postprocessor.process(
            raw_text, Path(audio_file).name
        )

        # Вывод результата
        print("\n" + "=" * 60)
        print("РЕЗУЛЬТАТ ТРАНСКРИПЦИИ:")
        print("=" * 60)
        print(cleaned_text)
        print("\n" + "=" * 60)

        if classification:
            print("КЛАССИФИКАЦИЯ:")
            print("=" * 60)
            import json
            print(json.dumps(classification, ensure_ascii=False, indent=2))
            print("=" * 60)

        # Удаление временного файла
        Path(preprocessed).unlink(missing_ok=True)

        logger.info("✓ Обработка завершена успешно")

    except Exception as e:
        logger.error(f"Ошибка обработки файла: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.option("--config", default="config.yaml", help="Путь к config.yaml")
def health(config):
    """
    Диагностика системы: GPU, VLLM, конфиг, диск.

    Проверяет доступность всех компонентов и выводит статус.
    """
    try:
        print("\n" + "=" * 60)
        print("🏥 HEALTH CHECK - ASR-4.5")
        print("=" * 60)

        # 1. Конфигурация
        print("\n1️⃣ Конфигурация...")
        try:
            config_manager = ConfigManager(config)
            app_config = config_manager.get()
            print("   ✓ Config валиден")
        except Exception as e:
            print(f"   ❌ Ошибка конфига: {e}")
            sys.exit(1)

        # 2. GPU
        print("\n2️⃣ GPU...")
        try:
            gpu_monitor = GPUMonitor(gpu_index=0)
            gpu_monitor.check_device("cuda")
            mem_info = gpu_monitor.get_memory_info()
            temp = gpu_monitor.get_temperature()

            print(f"   ✓ GPU: {gpu_monitor.gpu_name}")
            print(f"   ✓ Память: {mem_info['used_mb']} / {mem_info['total_mb']} MB ({mem_info['utilization_percent']}%)")
            if temp:
                print(f"   ✓ Температура: {temp}°C")
        except Exception as e:
            print(f"   ❌ GPU недоступна: {e}")
            sys.exit(1)

        # 3. VLLM
        print("\n3️⃣ VLLM API...")
        try:
            from src.vllm_postprocessor import VLLMPostprocessor

            vllm = VLLMPostprocessor(app_config.vllm)
            if vllm.health_check():
                print(f"   ✓ VLLM доступен: {app_config.vllm.base_url}")
                print(f"   ✓ Модель: {app_config.vllm.model}")
            else:
                print("   ❌ VLLM недоступен")
        except Exception as e:
            print(f"   ❌ Ошибка VLLM: {e}")

        # 4. Диск
        print("\n4️⃣ Дисковое пространство...")
        try:
            import shutil

            stat = shutil.disk_usage(Path(app_config.paths.archive))
            usage = (stat.used / stat.total) * 100
            free_gb = stat.free / (1024**3)

            print(f"   ✓ Использовано: {usage:.1f}%")
            print(f"   ✓ Свободно: {free_gb:.2f} GB")

            if usage >= app_config.cleanup.max_disk_usage_percent:
                print(f"   ⚠️ Диск заполнен! Требуется очистка.")
        except Exception as e:
            print(f"   ⚠️ Ошибка проверки диска: {e}")

        # 5. Директории
        print("\n5️⃣ Директории...")
        for name, path_str in {
            "input": app_config.paths.input,
            "output": app_config.paths.output,
            "metadata": app_config.paths.metadata,
            "archive": app_config.paths.archive,
            "logs": app_config.paths.logs,
        }.items():
            path = Path(path_str)
            if path.exists():
                print(f"   ✓ {name}: {path_str}")
            else:
                print(f"   ⚠️ {name}: {path_str} (не существует)")

        print("\n" + "=" * 60)
        print("✅ Health check завершён")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n❌ Критическая ошибка health check: {e}")
        sys.exit(1)


@cli.command()
@click.option("--config", default="config.yaml", help="Путь к config.yaml")
def cleanup(config):
    """
    Ручной запуск автоочистки архива.

    Удаляет старые файлы и сжимает архивы согласно конфигурации.
    """
    try:
        # Загрузка конфигурации
        config_manager = ConfigManager(config)
        app_config = config_manager.get()

        setup_logging(app_config)

        logger.info("Запуск ручной автоочистки...")

        from src.cleanup_manager import CleanupManager

        cleanup_manager = CleanupManager(app_config.cleanup, app_config.paths)

        # Ротация архива
        stats = cleanup_manager.rotate_archive()

        print("\n" + "=" * 60)
        print("🧹 РЕЗУЛЬТАТ АВТООЧИСТКИ")
        print("=" * 60)
        print(f"Удалено файлов: {stats['deleted_count']}")
        print(f"Освобождено места: {stats['deleted_size_mb']:.2f} MB")
        print(f"Сжато файлов: {stats['compressed_count']}")
        print("=" * 60 + "\n")

        # Проверка диска
        if cleanup_manager.check_disk_space():
            logger.warning("Диск заполнен, запуск экстренной очистки...")
            emergency_stats = cleanup_manager.emergency_cleanup()
            print(f"\n⚠️ Экстренная очистка: удалено {emergency_stats['deleted_count']} файлов")

        logger.info("✓ Автоочистка завершена")

    except Exception as e:
        logger.error(f"Ошибка автоочистки: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.option("--config", default="config.yaml", help="Путь к config.yaml")
def metrics(config):
    """
    Показать статистику обработки файлов.

    Выводит метрики: количество обработанных файлов, средний RTF, ошибки.
    """
    try:
        config_manager = ConfigManager(config)
        app_config = config_manager.get()

        print("\n" + "=" * 60)
        print("📊 МЕТРИКИ ASR-4.5")
        print("=" * 60)

        # Статистика из output/
        output_path = Path(app_config.paths.output)
        transcriptions = list(output_path.glob("*.txt"))

        print(f"\nОбработано файлов: {len(transcriptions)}")

        # Статистика из metadata/
        metadata_path = Path(app_config.paths.metadata)
        if metadata_path.exists():
            metadata_files = list(metadata_path.glob("*.json"))
            print(f"Файлов с метаданными: {len(metadata_files)}")

            # Средний RTF (если есть метаданные)
            if metadata_files:
                import json

                total_rtf = 0
                count = 0
                for meta_file in metadata_files:
                    try:
                        with open(meta_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            rtf = data.get("asr_metrics", {}).get("rtf")
                            if rtf:
                                total_rtf += rtf
                                count += 1
                    except Exception:
                        continue

                if count > 0:
                    avg_rtf = total_rtf / count
                    print(f"Средний RTF: {avg_rtf:.4f}")
                    print(f"Скорость: {1/avg_rtf:.1f}x реального времени")

        # Статистика архива
        archive_path = Path(app_config.paths.archive)
        if archive_path.exists():
            archived_files = [
                f
                for f in archive_path.rglob("*")
                if f.is_file() and not f.name.endswith(".tar.gz")
            ]
            compressed_archives = list(archive_path.rglob("*.tar.gz"))

            print(f"\nАрхивировано файлов: {len(archived_files)}")
            print(f"Сжатых архивов: {len(compressed_archives)}")

        print("\n" + "=" * 60 + "\n")

    except Exception as e:
        print(f"Ошибка получения метрик: {e}")
        sys.exit(1)


@cli.command()
@click.argument("transcription_file", type=click.Path(exists=True))
@click.option("--show-reasoning", is_flag=True, help="Показать ход мышления Commercial-LLM")
@click.option("--config", default="config.yaml", help="Путь к config.yaml")
def analyze_quality(transcription_file, show_reasoning, config):
    """
    Анализ качества обслуживания для одной транскрипции.

    Использует Commercial LLM API для оценки по 30 критериям скрипта.

    Пример:
        ./venv/bin/python main.py analyze-quality output/звонок.txt
    """
    try:
        # Загрузка конфигурации
        config_manager = ConfigManager(config)
        app_config = config_manager.get()

        setup_logging(app_config)

        logger.info(f"Анализ качества: {transcription_file}")

        # Инициализация анализатора
        from src.quality_analyzer import QualityAnalyzer

        analyzer = QualityAnalyzer(app_config.quality_analysis, app_config.vllm)

        # Поиск соответствующего metadata файла
        transcription_path = Path(transcription_file)
        metadata_path = (
            Path(app_config.paths.metadata) / f"{transcription_path.stem}.json"
        )
        metadata_path_str = str(metadata_path) if metadata_path.exists() else None

        # Анализ
        result = analyzer.analyze_call(str(transcription_path), metadata_path_str)

        # Сохранение
        analyzer.save_analysis(result, transcription_path.stem)

        # Вывод результатов
        print("\n" + "=" * 60)
        print("📊 РЕЗУЛЬТАТ АНАЛИЗА КАЧЕСТВА")
        print("=" * 60)
        print(f"Администратор: {result['admin_name']}")
        print(f"Оборудование: {result['equipment_type']}")
        print(f"Итоговый балл: {result['overall_score']:.1f}/100")
        print(f"\nСтоимость анализа: ${result['cost_usd']:.4f}")
        print(f"Токенов использовано: {result['tokens_used']['total']}")

        print(f"\n✅ Сильные стороны:")
        for strength in result["strengths"][:5]:
            print(f"  • {strength}")

        print(f"\n⚠️ Области для улучшения:")
        for weakness in result["weaknesses"][:5]:
            print(f"  • {weakness}")

        if show_reasoning:
            print(f"\n💭 Reasoning:")
            print(result.get("reasoning", "N/A"))

        print("\n" + "=" * 60 + "\n")

        logger.info("✓ Анализ завершён успешно")

    except Exception as e:
        logger.error(f"Ошибка анализа качества: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.option("--admin-name", help="Фильтр по имени администратора")
@click.option("--min-score", type=float, help="Минимальный балл")
@click.option("--config", default="config.yaml", help="Путь к config.yaml")
def analyze_batch(admin_name, min_score, config):
    """
    Пакетный анализ всех транскрипций в output/.

    Обрабатывает все .txt файлы и генерирует оценки качества.

    Пример:
        ./venv/bin/python main.py analyze-batch
        ./venv/bin/python main.py analyze-batch --admin-name "Анастасия"
    """
    try:
        # Загрузка конфигурации
        config_manager = ConfigManager(config)
        app_config = config_manager.get()

        setup_logging(app_config)

        logger.info("Пакетный анализ качества...")

        # Инициализация анализатора
        from src.quality_analyzer import QualityAnalyzer

        analyzer = QualityAnalyzer(app_config.quality_analysis, app_config.vllm)

        # Поиск транскрипций
        output_dir = Path(app_config.paths.output)
        transcriptions = list(output_dir.glob("*.txt"))

        if not transcriptions:
            print("Нет транскрипций для анализа")
            return

        logger.info(f"Найдено транскрипций: {len(transcriptions)}")

        # Анализ каждой транскрипции
        processed = 0
        skipped = 0
        total_cost = 0.0

        for trans_file in transcriptions:
            try:
                # Проверка metadata
                metadata_path = (
                    Path(app_config.paths.metadata) / f"{trans_file.stem}.json"
                )

                # Фильтр по администратору
                if admin_name:
                    if metadata_path.exists():
                        with open(metadata_path, "r", encoding="utf-8") as f:
                            metadata = json.load(f)
                            if (
                                metadata.get("classification", {}).get("admin_name")
                                != admin_name
                            ):
                                skipped += 1
                                continue
                    else:
                        skipped += 1
                        continue

                # Проверка уже проанализированных
                analysis_path = (
                    Path(app_config.quality_analysis.paths["individual"])
                    / f"{trans_file.stem}.json"
                )
                if analysis_path.exists():
                    logger.info(f"Пропущено (уже проанализировано): {trans_file.name}")
                    skipped += 1
                    continue

                # Анализ
                logger.info(f"Анализ {processed + 1}/{len(transcriptions)}: {trans_file.name}")

                result = analyzer.analyze_call(
                    str(trans_file),
                    str(metadata_path) if metadata_path.exists() else None,
                )

                # Сохранение
                analyzer.save_analysis(result, trans_file.stem)

                processed += 1
                total_cost += result.get("cost_usd", 0)

                print(
                    f"✓ {trans_file.name}: {result['overall_score']:.1f}/100 "
                    f"(${result['cost_usd']:.4f})"
                )

            except Exception as e:
                logger.error(f"Ошибка анализа {trans_file.name}: {e}")
                skipped += 1

        # Итоговая статистика
        print("\n" + "=" * 60)
        print("📊 ИТОГИ ПАКЕТНОГО АНАЛИЗА")
        print("=" * 60)
        print(f"Обработано: {processed}")
        print(f"Пропущено: {skipped}")
        print(f"Общая стоимость: ${total_cost:.4f}")
        print(f"Средняя стоимость/звонок: ${total_cost/processed:.4f}" if processed else "")
        print("=" * 60 + "\n")

        logger.info("✓ Пакетный анализ завершён")

    except Exception as e:
        logger.error(f"Ошибка пакетного анализа: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.argument("admin_name")
@click.option("--period", default="week", help="Период: day/week/month")
@click.option("--config", default="config.yaml", help="Путь к config.yaml")
def report(admin_name, period, config):
    """
    Сводный отчёт по администратору.

    Генерирует Markdown отчёт с анализом работы за период.

    Пример:
        ./venv/bin/python main.py report "Анастасия" --period week
    """
    try:
        # Загрузка конфигурации
        config_manager = ConfigManager(config)
        app_config = config_manager.get()

        setup_logging(app_config)

        # Конвертация периода в дни
        period_days = {"day": 1, "week": 7, "month": 30}.get(period, 7)

        logger.info(f"Генерация отчёта для {admin_name} за {period_days} дней...")

        # Генерация отчёта
        from src.report_generator import ReportGenerator

        generator = ReportGenerator(
            app_config.quality_analysis.paths["individual"],
            app_config.quality_analysis.paths["reports"],
        )

        report_path = generator.generate_admin_report(admin_name, period_days)

        if report_path:
            print(f"\n✅ Отчёт сохранён: {report_path}\n")

            # Вывод отчёта в консоль
            with open(report_path, "r", encoding="utf-8") as f:
                print(f.read())
        else:
            print(f"\n⚠️ Нет данных для администратора {admin_name}\n")

    except Exception as e:
        logger.error(f"Ошибка генерации отчёта: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.argument("transcription_file", type=click.Path(exists=True))
@click.option("--config", default="config.yaml", help="Путь к config.yaml")
def compare_models(transcription_file, config):
    """
    A/B тест: Commercial LLM API vs LLM-Model на одном звонке.

    Сравнивает качество анализа двух моделей для принятия решения
    о выборе модели для production.

    Пример:
        ./venv/bin/python main.py compare-models output/звонок.txt
    """
    try:
        # Загрузка конфигурации
        config_manager = ConfigManager(config)
        app_config = config_manager.get()

        setup_logging(app_config)

        logger.info(f"A/B тест моделей: {transcription_file}")

        # Загрузка транскрипции и метаданных
        transcription_path = Path(transcription_file)
        with open(transcription_path, "r", encoding="utf-8") as f:
            transcription = f.read()

        metadata = None
        metadata_path = (
            Path(app_config.paths.metadata) / f"{transcription_path.stem}.json"
        )
        if metadata_path.exists():
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)

        # Инициализация компаратора
        from src.model_comparison import ModelComparator

        comparator = ModelComparator(
            app_config.quality_analysis, app_config.vllm
        )

        # Запуск сравнения
        comparison = comparator.compare(transcription, metadata)

        # Вывод результатов
        comparator.print_comparison(comparison)

        # Сохранение результатов сравнения
        comparison_dir = Path("quality_analysis/comparisons")
        comparison_dir.mkdir(parents=True, exist_ok=True)

        comparison_path = comparison_dir / f"{transcription_path.stem}_comparison.json"
        with open(comparison_path, "w", encoding="utf-8") as f:
            json.dump(comparison, f, ensure_ascii=False, indent=2)

        logger.info(f"✓ Результаты сравнения сохранены: {comparison_path}")

    except Exception as e:
        logger.error(f"Ошибка A/B теста: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.option("--config", default="config.yaml", help="Путь к config.yaml")
@click.option("--period", default="week", help="Период: day/week/month")
def cost_stats(config, period):
    """
    Статистика стоимости API вызовов (токены, расходы).

    Показывает сколько потрачено на анализ качества через Commercial LLM API.

    Пример:
        ./venv/bin/python main.py cost-stats
        ./venv/bin/python main.py cost-stats --period month
    """
    try:
        # Загрузка конфигурации
        config_manager = ConfigManager(config)
        app_config = config_manager.get()

        # Конвертация периода
        period_days = {"day": 1, "week": 7, "month": 30, "all": None}.get(period, 7)

        # Сбор статистики
        from src.cost_tracker import CostTracker

        tracker = CostTracker(app_config.quality_analysis.paths["individual"])
        stats = tracker.collect_stats(period_days)

        # Вывод
        tracker.print_stats(stats)

    except Exception as e:
        print(f"Ошибка получения статистики: {e}")
        sys.exit(1)


@cli.command()
@click.option("--period", default="day", help="Период: day/week")
@click.option("--config", default="config.yaml", help="Путь к config.yaml")
def aggregate(period, config):
    """
    Агрегация аналитики (витрины day/week).

    Генерирует витрины с метриками ERR, MissRate, Top-3 провалов.

    Пример:
        ./venv/bin/python main.py aggregate --period day
        ./venv/bin/python main.py aggregate --period week
    """
    try:
        config_manager = ConfigManager(config)
        app_config = config_manager.get()

        setup_logging(app_config)

        from src.analytics_aggregator import AnalyticsAggregator

        aggregator = AnalyticsAggregator(
            app_config.analytics.db_path,
            "analytics/aggregates"
        )

        if period == "day":
            aggregate = aggregator.aggregate_day()
        elif period == "week":
            aggregate = aggregator.aggregate_week()
        else:
            print(f"Неизвестный период: {period}")
            sys.exit(1)

        print("\n✅ Витрина создана:")
        print(json.dumps(aggregate, ensure_ascii=False, indent=2))

    except Exception as e:
        logger.error(f"Ошибка агрегации: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.option("--type", default="daily", help="Тип: daily/weekly")
@click.option("--chat-id", help="Telegram chat ID (опционально)")
@click.option("--config", default="config.yaml", help="Путь к config.yaml")
def telegram_report(type, chat_id, config):
    """
    Отправка отчёта в Telegram (ручной запуск).

    Пример:
        ./venv/bin/python main.py telegram-report --type daily --chat-id YOUR_ID
        ./venv/bin/python main.py telegram-report --type weekly
    """
    try:
        config_manager = ConfigManager(config)
        app_config = config_manager.get()

        setup_logging(app_config)

        if not app_config.analytics.telegram["enabled"]:
            print("❌ Telegram отчёты отключены в config.yaml")
            sys.exit(1)

        # Агрегация данных
        from src.analytics_aggregator import AnalyticsAggregator
        from src.telegram_reporter import TelegramReporter

        aggregator = AnalyticsAggregator(
            app_config.analytics.db_path,
            "analytics/aggregates"
        )

        # Telegram reporter
        reporter = TelegramReporter(
            app_config.analytics.telegram["bot_token"],
            chat_id or app_config.analytics.telegram.get("chat_id")
        )

        # Отправка отчёта
        import asyncio

        if type == "daily":
            aggregate = aggregator.aggregate_day()
            success = asyncio.run(reporter.send_daily_report(aggregate))
        elif type == "weekly":
            aggregate = aggregator.aggregate_week()
            success = asyncio.run(reporter.send_weekly_report(aggregate))
        else:
            print(f"Неизвестный тип отчёта: {type}")
            sys.exit(1)

        if success:
            print(f"\n✅ Отчёт '{type}' отправлен в Telegram")
        else:
            print(f"\n❌ Не удалось отправить отчёт")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Ошибка отправки Telegram отчёта: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.option("--config", default="config.yaml", help="Путь к config.yaml")
@click.option("--date", default=None, help="Дата в формате YYYY-MM-DD (по умолчанию сегодня)")
def update_dashboard(config, date):
    """
    Обновить Dashboard в Google Sheets за день.
    
    Генерирует витрину дня и обновляет лист "📊 Dashboard" 
    с ключевыми метриками: апсейл, ошибки, рейтинг админов/филиалов.
    
    Пример:
        ./venv/bin/python main.py update-dashboard
        ./venv/bin/python main.py update-dashboard --date 2025-10-20
    """
    try:
        # Загрузка конфигурации
        config_manager = ConfigManager(config)
        app_config = config_manager.get()

        setup_logging(app_config)

        if not app_config.google_sheets.enabled:
            print("❌ Google Sheets интеграция отключена в config.yaml")
            sys.exit(1)

        logger.info("Обновление Dashboard в Google Sheets...")

        # 1. Генерация витрины дня
        from src.analytics_aggregator import AnalyticsAggregator
        from src.google_sheets_integrator import GoogleSheetsIntegrator

        aggregator = AnalyticsAggregator(
            db_path=app_config.analytics.db_path,
            aggregates_path="./analytics/aggregates"
        )

        day_aggregate = aggregator.aggregate_day(date)
        
        print(f"\n✅ Витрина дня создана: {day_aggregate['date']}")
        print(f"   Звонков: {day_aggregate['total_calls']}")
        print(f"   Средний балл: {day_aggregate['avg_score']:.1f}")
        print(f"   ERR: {day_aggregate['err_rate']:.0%}")

        # 2. Обновление Dashboard в Google Sheets
        sheets_integrator = GoogleSheetsIntegrator(
            credentials_path=app_config.google_sheets.credentials_path,
            spreadsheet_id=app_config.google_sheets.spreadsheet_id,
            db_path=app_config.analytics.db_path,
        )

        success = sheets_integrator.update_dashboard(day_aggregate)

        if success:
            print(f"\n✅ Dashboard обновлён в Google Sheets")
            print(f"   Лист: 📊 Dashboard")
            print(f"   URL: https://docs.google.com/spreadsheets/d/{app_config.google_sheets.spreadsheet_id}")
        else:
            print(f"\n❌ Не удалось обновить Dashboard")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Ошибка обновления Dashboard: {e}", exc_info=True)
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)


@cli.command()
@click.option("--period", default="week", help="Период: day/week/month")
@click.option("--output", default="errors_export.csv", help="Путь к выходному CSV")
@click.option("--admin", help="Фильтр по администратору")
@click.option("--config", default="config.yaml", help="Путь к config.yaml")
def export_csv(period, output, admin, config):
    """
    Экспорт ошибок в CSV для Excel-анализа.

    Пример:
        ./venv/bin/python main.py export-csv --period week --output report.csv
        ./venv/bin/python main.py export-csv --admin "Дарья"
    """
    try:
        config_manager = ConfigManager(config)
        app_config = config_manager.get()

        setup_logging(app_config)

        period_days = {"day": 1, "week": 7, "month": 30}.get(period, 7)

        from src.csv_exporter import CSVExporter

        exporter = CSVExporter(app_config.analytics.db_path)

        success = exporter.export_errors(output, period_days, admin)

        if success:
            print(f"\n✅ Экспорт завершён: {output}")
        else:
            print("\n❌ Ошибка экспорта")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Ошибка экспорта CSV: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.option("--config", default="config.yaml", help="Путь к config.yaml")
def error_stats(config):
    """
    Статистика ошибок из аналитической БД.

    Показывает общее количество ошибок, топ-провалы, админов требующих обучения.

    Пример:
        ./venv/bin/python main.py error-stats
    """
    try:
        config_manager = ConfigManager(config)
        app_config = config_manager.get()

        from src.db_manager import DatabaseManager

        db = DatabaseManager(app_config.analytics.db_path)
        stats = db.get_stats()

        print("\n" + "=" * 60)
        print("📊 СТАТИСТИКА АНАЛИТИЧЕСКОЙ БД")
        print("=" * 60)
        print(f"Событий ошибок: {stats['events_count']}")
        print(f"Звонков проанализировано: {stats['calls_count']}")
        print(f"Период: {stats['date_from']} - {stats['date_to']}")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"Ошибка получения статистики: {e}")
        sys.exit(1)


@cli.command()
@click.option("--dashboard-only", is_flag=True, help="Обновить только Dashboard")
@click.option("--config", default="config.yaml", help="Путь к config.yaml")
def sync_sheets(dashboard_only, config):
    """
    Синхронизация данных с Google Sheets (батчами).

    Обновляет все звонки из БД в Google Sheets таблицу.

    Пример:
        ./venv/bin/python main.py sync-sheets
        ./venv/bin/python main.py sync-sheets --dashboard-only
    """
    try:
        config_manager = ConfigManager(config)
        app_config = config_manager.get()

        setup_logging(app_config)

        # Проверка что Google Sheets включен
        if not app_config.google_sheets.enabled:
            print("❌ Google Sheets интеграция отключена в config.yaml")
            sys.exit(1)

        from src.google_sheets_integrator import GoogleSheetsIntegrator

        integrator = GoogleSheetsIntegrator(
            app_config.google_sheets.credentials_path,
            app_config.google_sheets.spreadsheet_id,
            app_config.analytics.db_path,
        )

        if dashboard_only:
            # Только Dashboard
            success = integrator.update_dashboard()
            if success:
                print("\n✅ Dashboard обновлён")
            else:
                print("\n❌ Ошибка обновления Dashboard")
                sys.exit(1)
        else:
            # Полная синхронизация
            rows_added = integrator.batch_update_calls()
            integrator.update_dashboard()

            print(f"\n✅ Синхронизация завершена: {rows_added} звонков добавлено")

    except Exception as e:
        logger.error(f"Ошибка синхронизации Google Sheets: {e}", exc_info=True)
        sys.exit(1)


@cli.command()
@click.option("--config", default="config.yaml", help="Путь к config.yaml")
def test_sheets(config):
    """
    Проверка подключения к Google Sheets.

    Тестирует аутентификацию и доступ к таблице.

    Пример:
        ./venv/bin/python main.py test-sheets
    """
    try:
        config_manager = ConfigManager(config)
        app_config = config_manager.get()

        if not hasattr(app_config, 'google_sheets') or not app_config.google_sheets.get('enabled', False):
            print("❌ Google Sheets интеграция отключена в config.yaml")
            sys.exit(1)

        from src.google_sheets_integrator import GoogleSheetsIntegrator

        integrator = GoogleSheetsIntegrator(
            app_config.google_sheets["credentials_path"],
            app_config.google_sheets["spreadsheet_id"],
            app_config.analytics.db_path,
        )

        if integrator.test_connection():
            print("\n✅ Подключение к Google Sheets работает!")
        else:
            print("\n❌ Проблема с подключением")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        sys.exit(1)


@cli.command()
@click.option("--apply", is_flag=True, help="Применить удаление (без флага - dry run)")
@click.option("--config", default="config.yaml", help="Путь к config.yaml")
def cleanup_sheets(apply, config):
    """
    Удалить дубликаты из Google Sheets.

    По умолчанию запускается в режиме DRY RUN (только показывает дубликаты).
    Используйте --apply для фактического удаления.

    Пример:
        ./venv/bin/python main.py cleanup-sheets           # Dry run
        ./venv/bin/python main.py cleanup-sheets --apply   # Удалить
    """
    try:
        config_manager = ConfigManager(config)
        app_config = config_manager.get()

        setup_logging(app_config)

        if not app_config.google_sheets.enabled:
            print("❌ Google Sheets интеграция отключена в config.yaml")
            sys.exit(1)

        from src.sheets_cleanup import SheetsCleanup

        cleanup = SheetsCleanup(
            app_config.google_sheets.credentials_path,
            app_config.google_sheets.spreadsheet_id,
        )

        # Поиск и удаление дубликатов
        removed = cleanup.remove_duplicates(dry_run=not apply)

        if not apply:
            print(f"\n🔍 Найдено дубликатов: {len(cleanup.find_duplicates())}")
            print("Запустите с флагом --apply для удаления")
        else:
            print(f"\n✅ Удалено строк: {removed}")

    except Exception as e:
        logger.error(f"Ошибка очистки дубликатов: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()

