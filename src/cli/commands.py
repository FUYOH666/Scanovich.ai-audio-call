"""CLI command implementations (registered on the root Click group)."""

import json
import logging
import sys
from pathlib import Path

import click

from src.utils import ConfigManager, GPUMonitor, setup_logging

logger = logging.getLogger(__name__)


def register(cli: click.Group) -> None:
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
            logger.info("Call Analytics Platform — daemon start")
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
            uv run python main.py process-file input/звонок.mp3
        """
        try:
            # Загрузка конфигурации
            config_manager = ConfigManager(config)
            app_config = config_manager.get()

            # Настройка логирования
            setup_logging(app_config)

            logger.info(f"Обработка файла: {audio_file}")

            from src.pipeline_service import CallAnalysisPipeline

            pipeline = CallAnalysisPipeline(app_config)
            result = pipeline.analyze_file(audio_file, persist=False, analyze_quality=False)
            logger.info(f"ASR завершён: {len(result.raw_transcription)} символов")
            logger.info(
                "Метрики: RTF=%s, время=%ss",
                result.asr_metrics.get("rtf", "N/A"),
                result.asr_metrics.get("elapsed_time"),
            )

            # Вывод результата
            print("\n" + "=" * 60)
            print("РЕЗУЛЬТАТ ТРАНСКРИПЦИИ:")
            print("=" * 60)
            print(result.cleaned_text)
            print("\n" + "=" * 60)

            if result.classification:
                print("КЛАССИФИКАЦИЯ:")
                print("=" * 60)
                print(json.dumps(result.classification, ensure_ascii=False, indent=2))
                print("=" * 60)

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
            print("🏥 HEALTH CHECK — Call Analytics Platform")
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
            if app_config.asr.device == "cuda":
                try:
                    gpu_monitor = GPUMonitor(gpu_index=0)
                    gpu_monitor.check_device(app_config.asr.device)
                    mem_info = gpu_monitor.get_memory_info()
                    temp = gpu_monitor.get_temperature()

                    print(f"   ✓ GPU: {gpu_monitor.gpu_name}")
                    print(f"   ✓ Память: {mem_info['used_mb']} / {mem_info['total_mb']} MB ({mem_info['utilization_percent']}%)")
                    if temp:
                        print(f"   ✓ Температура: {temp}°C")
                except Exception as e:
                    print(f"   ❌ GPU недоступна: {e}")
                    sys.exit(1)
            else:
                print(f"   ✓ Используется {app_config.asr.device.upper()} режим")

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
    @click.option("--host", default=None, help="Host для web UI/API")
    @click.option("--port", default=None, type=int, help="Port для web UI/API")
    @click.option(
        "--allow-insecure-public-bind",
        is_flag=True,
        help="Разрешить запуск на 0.0.0.0 без API key (только если вы точно понимаете риск)",
    )
    def web(config, host, port, allow_insecure_public_bind):
        """
        Запустить browser UI и HTTP API для demo/pilot сценария.

        Пример:
            uv run python main.py web
            uv run python main.py web --host 0.0.0.0 --port 8080
        """
        try:
            config_manager = ConfigManager(config)
            app_config = config_manager.get()
            setup_logging(app_config)

            host = host or app_config.web.host
            port = port or app_config.web.port

            is_public_bind = host not in {"127.0.0.1", "localhost", "::1"}
            if is_public_bind and not app_config.web.require_api_key and not allow_insecure_public_bind:
                raise click.ClickException(
                    "Публичный bind без API key запрещён. "
                    "Включите web.require_api_key и задайте WEB__API_KEY, "
                    "или явно используйте --allow-insecure-public-bind для временного demo."
                )

            from src.web.app import create_app
            import uvicorn

            app = create_app(config)
            logger.info("Запуск web UI/API: host=%s port=%s", host, port)
            if app_config.web.require_api_key:
                logger.info("Защита web слоя включена: требуется X-API-Key")
            elif is_public_bind:
                logger.warning("⚠️ Web слой запущен без API key на публичном адресе")
            else:
                logger.info("Web слой запущен в локальном demo режиме")

            uvicorn.run(
                app,
                host=host,
                port=port,
                log_level=app_config.logging.level.lower(),
            )
        except click.ClickException:
            raise
        except Exception as e:
            logger.error(f"Ошибка запуска web UI/API: {e}", exc_info=True)
            raise click.ClickException(str(e)) from e


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
            print("📊 МЕТРИКИ")
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
    @click.option("--show-reasoning", is_flag=True, help="Показать ход рассуждения модели")
    @click.option("--config", default="config.yaml", help="Путь к config.yaml")
    def analyze_quality(transcription_file, show_reasoning, config):
        """
        Анализ качества обслуживания для одной транскрипции.

        Использует LLM из конфигурации (vLLM или облачный OpenAI-compatible API).

        Пример:
            uv run python main.py analyze-quality output/звонок.txt
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
            uv run python main.py analyze-batch
            uv run python main.py analyze-batch --admin-name "Анастасия"
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
            uv run python main.py report "Анастасия" --period week
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
        A/B тест: облачный LLM (OpenRouter-compatible) vs локальный VLLM на одном звонке.

        Сравнивает качество анализа двух моделей для принятия решения
        о выборе модели для production.

        Пример:
            uv run python main.py compare-models output/звонок.txt
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

        Показывает расход токенов/стоимость при использовании облачного LLM API (если включено).

        Пример:
            uv run python main.py cost-stats
            uv run python main.py cost-stats --period month
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
            uv run python main.py aggregate --period day
            uv run python main.py aggregate --period week
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
            uv run python main.py telegram-report --type daily --chat-id YOUR_ID
            uv run python main.py telegram-report --type weekly
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
            uv run python main.py update-dashboard
            uv run python main.py update-dashboard --date 2025-10-20
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
            uv run python main.py export-csv --period week --output report.csv
            uv run python main.py export-csv --admin "Дарья"
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
            uv run python main.py error-stats
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
            uv run python main.py sync-sheets
            uv run python main.py sync-sheets --dashboard-only
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
            uv run python main.py test-sheets
        """
        try:
            config_manager = ConfigManager(config)
            app_config = config_manager.get()

            if not app_config.google_sheets.enabled:
                print("❌ Google Sheets интеграция отключена в config.yaml")
                sys.exit(1)

            from src.google_sheets_integrator import GoogleSheetsIntegrator

            integrator = GoogleSheetsIntegrator(
                app_config.google_sheets.credentials_path,
                app_config.google_sheets.spreadsheet_id,
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
            uv run python main.py cleanup-sheets           # Dry run
            uv run python main.py cleanup-sheets --apply   # Удалить
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

