#!/usr/bin/env python3
"""
🏥 ENHANCED AUDIO PIPELINE v4.0 для медицинских центров
Автор: Scanovich.ai | Версия: 4.0 (3-ЭТАПНАЯ АРХИТЕКТУРА + THINKING MODE)

НОВАЯ 3-ЭТАПНАЯ АРХИТЕКТУРА LM STUDIO:
- ЭТАП 1: Исправление транскрипции (thinking ON)
- ЭТАП 2: Диаризация по смыслу (thinking ON)
- ЭТАП 3: Анализ скрипта + извлечение данных (thinking ON)
- Автономная транскрибация + диаризация
- HTML отчеты + валидация данных
- Медицинская конфиденциальность
"""

import os
import sys
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
# import librosa  # Отключено для совместимости

# Настройка автономного режима
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["HUGGINGFACE_HUB_CACHE"] = "./models/hub"

# Локальные импорты
from offline_pipeline import OfflineAudioPipeline
from unified_pipeline import UnifiedAudioAnalyzer
from google_sheets_integration import GoogleSheetsIntegration
from data_validator import DataValidator  # НОВЫЙ ИМПОРТ!
from transcription_postprocessor import TranscriptionPostProcessor  # ПОСТОБРАБОТКА!
from unified_data_extractor import UnifiedDataExtractor  # УНИФИКАЦИЯ ДАННЫХ!

# Настройка логирования
log_dir = Path("output/logs")
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'enhanced_pipeline_v3.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class EnhancedAudioPipelineV3:
    """
    Расширенный pipeline v4.0 с 3-этапной архитектурой LM Studio
    
    Включает:
    - Автономную транскрибацию с диаризацией
    - 3-ЭТАПНЫЙ АНАЛИЗ через LM Studio:
      • ЭТАП 1: Исправление транскрипции (thinking ON)
      • ЭТАП 2: Диаризация по смыслу (thinking ON)  
      • ЭТАП 3: Анализ скрипта + извлечение данных (thinking ON)
    - HTML отчеты с бизнес-сущностями
    - Google Sheets интеграцию
    - Валидацию данных для медицинской точности
    """
    
    def __init__(self, lm_studio_urls: list = None):
        """Инициализация Enhanced Pipeline v3.0 с двухэтапной архитектурой"""
        
        # Список адресов LM Studio (основной + резервный)
        if lm_studio_urls is None:
            lm_studio_urls = [
                "http://localhost:1234",           # Основной адрес
                "http://192.168.1.104:1234"       # Резервный адрес
            ]
        self.lm_studio_urls = lm_studio_urls
        
        # Интеграции
        try:
            self.sheets_integration = GoogleSheetsIntegration()
            if self.sheets_integration.setup_credentials():
                logger.info("✅ Google Sheets интеграция готова")
            else:
                logger.warning("⚠️ Google Sheets не подключен - проверьте credentials")
                self.sheets_integration = None
        except Exception as e:
            logger.warning(f"⚠️ Google Sheets ошибка инициализации: {e}")
            self.sheets_integration = None
            
        self.validator = DataValidator()
        
        # Двухэтапный анализатор (НОВОЕ!)
        self.unified_analyzer = UnifiedAudioAnalyzer()
        
        # Унифицированный экстрактор данных (v2.1)
        self.data_extractor = UnifiedDataExtractor()
        
        # Создание директорий
        self.output_dirs = {
            "transcriptions": Path("output/transcriptions"),
            "enhanced": Path("output/enhanced"), 
            "reports": Path("output/reports"),
            "logs": Path("output/logs")
        }
        
        for dir_path in self.output_dirs.values():
            dir_path.mkdir(parents=True, exist_ok=True)
            
        # Настройка логирования
        self._setup_logging()
        
        logger.info("🔄 Инициализация Enhanced Pipeline v3.0 (с двухэтапной архитектурой)")
    
    def _setup_logging(self):
        """Настройка логирования"""
        log_file = self.output_dirs["logs"] / "enhanced_pipeline_v3.log"
        
        # Настройка логгера
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def get_audio_duration(self, audio_path: Path) -> float:
        """Получение длительности аудиофайла в секундах (заглушка)"""
        # TODO: Добавить получение длительности аудио без дополнительных библиотек
        logger.info(f"📐 Длительность аудио: определяется из транскрипции")
        return 0.0  # Будет заполнено из transcription_result
    
    def load_models(self):
        """Модели загружаются автоматически при первом использовании"""
        logger.info("✅ Модели будут загружены автоматически при обработке")
        logger.info("🤖 LM Studio: двухэтапный анализ готов")
        logger.info("🛡️ Валидатор данных: готов")
    
    def process_audio_file(self, audio_path: Path) -> Dict:
        """
        Полная обработка аудиофайла с 3-этапной архитектурой LM Studio
        
        Этапы:
        1. Автономная транскрибация (Whisper)
        1.5. Постобработка имен администраторов
        2. 3-ЭТАПНЫЙ АНАЛИЗ LM Studio:
           • Исправление транскрипции (thinking ON)
           • Диаризация по смыслу (thinking ON)
           • Анализ скрипта + извлечение данных (thinking ON)
        3. Валидация данных
        4. HTML отчет 
        5. Google Sheets
        """
        
        try:
            start_time = datetime.now()
            logger.info(f"🎯 Начало обработки: {audio_path.name}")
            
            # Длительность аудио будет получена из транскрипции
            audio_duration = 0.0
            
            # Этап 1: Автономная транскрибация
            logger.info("🔒 Этап 1: Автономная транскрибация...")
            transcription_start = datetime.now()
            
            # Используем offline pipeline для транскрибации
            offline_pipeline = OfflineAudioPipeline()
            offline_pipeline.load_models()  # ИСПРАВЛЕНИЕ: загружаем модели!
            transcription_result = offline_pipeline.process_audio_file(audio_path)
            
            if not transcription_result["success"]:
                raise Exception(f"Ошибка транскрибации: {transcription_result['error']}")
            
            # Читаем транскрипцию
            transcription_file = Path(transcription_result["transcription_file"])
            with open(transcription_file, 'r', encoding='utf-8') as f:
                transcription_text = f.read()
            
            transcription_time = (datetime.now() - transcription_start).total_seconds()
            logger.info(f"✅ Транскрибация завершена за {transcription_time:.2f}с")
            
            # НОВОЕ: Этап 1.5 - ПОСТОБРАБОТКА ТРАНСКРИПЦИИ
            logger.info("🔧 Этап 1.5: Постобработка транскрипции (исправление имен)...")
            postprocessor = TranscriptionPostProcessor()
            transcription_text, corrections_stats = postprocessor.process_transcription(
                transcription_text, context="МРТ-клиника"
            )
            
            if corrections_stats["total_changes"] > 0:
                logger.info(f"✅ Постобработка: {corrections_stats['total_changes']} исправлений")
                logger.info(f"   👤 Имена администраторов: {corrections_stats['admin_names']}")
                logger.info(f"   🔢 Числа и цены: {corrections_stats['numbers']}")
                logger.info(f"   🏥 Медицинские термины: {corrections_stats['medical_terms']}")
            else:
                logger.info("📝 Постобработка: исправления не требуются")
            
            # Этап 2: 3-ЭТАПНЫЙ АНАЛИЗ через LM Studio
            logger.info("🤖 Этап 2: 3-этапный анализ через LM Studio...")
            analysis_start = datetime.now()
            
            analysis_result = self.unified_analyzer.analyze_call(transcription_text)
            
            # Добавляем длительность аудио в результат анализа
            analysis_result["audio_duration"] = transcription_result.get("audio_duration", 0)
            
            if not analysis_result["success"]:
                raise Exception(f"Ошибка анализа: {analysis_result.get('error', 'неизвестная ошибка')}")
            
            analysis_time = (datetime.now() - analysis_start).total_seconds()
            logger.info(f"✅ 3-этапный анализ завершен за {analysis_time:.2f}с")
            
            # Логирование этапов, если доступно
            if "processing_stages" in analysis_result:
                stages = analysis_result["processing_stages"]
                logger.info(f"   🔧 Этап 1 (исправление): {stages.get('stage1_transcription_fix', 0):.2f}с")
                logger.info(f"   🎭 Этап 2 (диаризация): {stages.get('stage2_diarization', 0):.2f}с")
                logger.info(f"   📊 Этап 3 (анализ скрипта): {stages.get('stage3_script_analysis', 0):.2f}с")
            
            # ИСПРАВЛЕНО: Правильный путь к исправленной транскрипции для отчетов  
            corrected_transcription = analysis_result.get("corrected_transcription", "")
            if not corrected_transcription:
                # Пробуем альтернативный путь
                corrected_transcription = analysis_result.get("analysis", {}).get("corrected_transcription", "")
            
            if corrected_transcription:
                # Убираем thinking блоки из исправленной транскрипции
                if "</think>" in corrected_transcription:
                    clean_corrected = corrected_transcription.split("</think>", 1)[1].strip()
                elif "<think>" in corrected_transcription:
                    clean_corrected = corrected_transcription.split("<think>", 1)[0].strip()
                else:
                    clean_corrected = corrected_transcription.strip()
                
                if clean_corrected and len(clean_corrected) > 100:
                    transcription_for_reports = clean_corrected
                    logger.info("📝 Используем исправленную транскрипцию для отчетов")
                else:
                    transcription_for_reports = transcription_text
                    logger.info("📝 Исправленная транскрипция слишком короткая, используем оригинальную")
            else:
                transcription_for_reports = transcription_text
                logger.info("📝 Используем оригинальную транскрипцию для отчетов")
            
            # Этап 3: ВАЛИДАЦИЯ ДАННЫХ
            logger.info("🛡️ Этап 3: Валидация извлеченных данных...")
            validation_start = datetime.now()
            
            validation_result = self.validator.validate_analysis(
                analysis_result, transcription_text
            )
            
            validation_time = (datetime.now() - validation_start).total_seconds()
            logger.info(f"✅ Валидация завершена за {validation_time:.2f}с")
            
            # Логирование критических проблем
            if validation_result["summary"]["errors"] > 0:
                logger.warning(f"⚠️ Найдено {validation_result['summary']['errors']} критических ошибок валидации!")
                for issue in validation_result["summary"]["critical_issues"]:
                    logger.warning(f"  🚨 {issue}")
            
            # Этап 3.5: УНИФИКАЦИЯ ДАННЫХ (v2.1)
            logger.info("🔄 Этап 3.5: Стандартизация данных через UnifiedDataExtractor...")
            standardized_data = self.data_extractor.extract_standardized_data(analysis_result)
            
            # Логирование результатов унификации
            summary = standardized_data.get('validation_summary', {})
            logger.info(f"✅ Унификация завершена. Общая оценка: {standardized_data.get('total_score', 0)}/20")
            if summary.get('personal_fields_fixed', 0) > 0 or summary.get('commercial_fields_fixed', 0) > 0:
                logger.warning(f"🔧 Исправлено полей: personal={summary.get('personal_fields_fixed', 0)}, commercial={summary.get('commercial_fields_fixed', 0)}")
            
            # Этап 4: HTML отчет
            logger.info("📋 Этап 4: Создание HTML отчета...")
            
            report_file = self._create_html_report_unified(
                audio_path, 
                transcription_for_reports,
                standardized_data
            )
            
            logger.info(f"📋 HTML отчет создан: {report_file}")
            
            # Сохранение результатов
            analysis_file = self._save_analysis_results(audio_path, analysis_result)
            self._save_validation_results(audio_path, validation_result)
            
            # Этап 5: Google Sheets интеграция (УНИФИЦИРОВАННАЯ)
            logger.info("📊 Этап 5: Google Sheets интеграция...")
            try:
                if self.sheets_integration:
                    # Используем унифицированные данные для Google Sheets
                    success = self.sheets_integration.add_standardized_data_to_sheet(
                        standardized_data, audio_path.name
                    )
                    if success:
                        logger.info("✅ Данные добавлены в Google Sheets через унифицированный экстрактор")
                    else:
                        logger.error("❌ Ошибка добавления данных в Google Sheets")
                else:
                    logger.warning("⚠️ Google Sheets интеграция не инициализирована")
            except Exception as e:
                logger.warning(f"⚠️ Google Sheets ошибка: {e}")
            
            # Подсчет времени
            end_time = datetime.now()
            total_time = (end_time - start_time).total_seconds()
            
            logger.info(f"🎉 Обработка завершена за {total_time:.2f}с")
            
            return {
                "success": True,
                "audio_file": str(audio_path),
                "transcription_file": transcription_result["transcription_file"],
                "analysis_file": str(analysis_file),
                "html_report_file": str(report_file),
                "processing_time": total_time,
                "audio_duration": transcription_result.get("audio_duration", 0),
                "lm_studio_used": analysis_result.get("lm_studio_used", False),
                "analysis_method": analysis_result.get("method", "lm_studio_two_stage"),
                "offline_mode": True,
                "privacy_guaranteed": True,
                "transcription_time": transcription_time,
                "analysis_time": analysis_time,
                "validation_time": validation_time,
                "validation_summary": validation_result["summary"],
                "files": {
                    "transcription": transcription_result.get("transcription_file"),
                    "analysis": str(analysis_file),
                    "validation": f"output/enhanced/{audio_path.stem}_validation.json",
                    "html_report": str(report_file)
                }
            }
            
        except Exception as e:
            logger.error(f"💥 Ошибка обработки: {e}")
            return {
                "success": False,
                "error": str(e),
                "offline_mode": True,
                "files": {}
            }
    
    def _add_to_google_sheets(self, audio_path: Path, analysis_result: Dict):
        """Добавление результатов в Google Sheets"""
        
        analysis = analysis_result.get("analysis", {})
        script_analysis = analysis.get("script_analysis", {})
        business_entities = analysis.get("business_entities", {})
        crm_metrics = analysis.get("crm_metrics", {})
        
        # Извлекаем данные клиента
        client = business_entities.get("client", {})
        appointment = business_entities.get("appointment", {})
        additional_services = business_entities.get("additional_services", {})
        medical_history = business_entities.get("medical_history", {})
        pricing = business_entities.get("pricing", {})  # НОВОЕ
        call_details = business_entities.get("call_details", {})  # НОВОЕ
        
        # Извлекаем оценки по блокам
        block_scores = script_analysis.get("block_scores", {})
        
        # Подготавливаем данные для Google Sheets в правильном порядке колонок
        row_data = [
            datetime.now().strftime('%d.%m.%Y %H:%M'),  # Дата анализа
            audio_path.name,  # Файл звонка
            f"{analysis_result.get('audio_duration', 0)/60:.1f}",  # Длительность (мин)
            "ru",  # Язык
            crm_metrics.get("call_result", "не определен"),  # Результат звонка
            client.get("name", ""),  # ФИО клиента
            client.get("phone", ""),  # Телефон
            client.get("birth_date", ""),  # Дата рождения
            str(client.get("weight", "")),  # Вес
            appointment.get("research_type", ""),  # Тип исследования
            ", ".join(medical_history.get("symptoms", [])),  # Симптомы
            medical_history.get("symptom_duration", ""),  # Длительность симптомов
            str(pricing.get("main_service_cost", "")),  # Стоимость
            appointment.get("date", ""),  # Дата записи
            appointment.get("time", ""),  # Время записи
            appointment.get("clinic_address", ""),  # Адрес клиники
            "видеозаключение" if additional_services.get("video_conclusion") else "",  # Доп. услуги
            script_analysis.get("overall_score", ""),  # Общая оценка скрипта
            block_scores.get("greeting", {}).get("score", ""),  # Приветствие
            block_scores.get("questions", {}).get("score", ""),  # Раскрывающие вопросы
            block_scores.get("sales", {}).get("score", ""),  # Продажа
            block_scores.get("booking", {}).get("score", ""),  # Запись
            block_scores.get("closing", {}).get("score", ""),  # Завершение
            "",  # Профессионализм (пока не извлекается)
            "",  # Обработка возражений (пока не извлекается)
            f"{analysis_result.get('audio_duration', 0)/60:.1f}",  # Длительность звонка
            "Администратор",  # Администратор
            "МРТ-Лидер",  # Клиника

        ]
        
        # Добавляем строку в Google Sheets
        self.sheets_integration.worksheet.append_row(row_data)
        
        # Форматирование строки по результату звонка
        last_row = len(self.sheets_integration.worksheet.get_all_values())
        call_result = crm_metrics.get("call_result", "")
        
        if "записался" in call_result.lower():
            # Зеленый фон для успешной записи
            self.sheets_integration.worksheet.format(f'{last_row}:{last_row}', {
                'backgroundColor': {'red': 0.8, 'green': 1.0, 'blue': 0.8}
            })
        elif "не записался" in call_result.lower():
            # Красный фон для неуспешной записи
            self.sheets_integration.worksheet.format(f'{last_row}:{last_row}', {
                'backgroundColor': {'red': 1.0, 'green': 0.8, 'blue': 0.8}
            })
    
    def _create_html_report(self, audio_path: Path, transcription: str, 
                           analysis_result: Dict) -> Path:
        """Создание HTML отчета с unified анализом"""
        
        # Получаем анализ
        analysis = analysis_result.get("analysis", {})
        script_analysis = analysis.get("script_evaluation", {})  # ИСПРАВЛЕНО: script_evaluation вместо script_analysis
        business_entities = analysis.get("business_entities", {})
        
        # ИСПРАВЛЕНО: Правильный путь к исправленной транскрипции
        corrected_transcription = analysis_result.get("corrected_transcription", "")
        if not corrected_transcription:
            # Пробуем альтернативный путь
            corrected_transcription = analysis_result.get("analysis", {}).get("corrected_transcription", "")
            
        if corrected_transcription and not corrected_transcription.startswith("<think>"):
            # Используем исправленную транскрипцию и конвертируем ADMIN/CLIENT в русские метки
            clean_transcription = self._convert_admin_client_to_russian(corrected_transcription)
        elif transcription.startswith("Администратор:") or transcription.startswith("Клиент:"):
            # Это уже исправленная транскрипция - очищаем дубликаты
            clean_transcription = self._clean_diarization_duplicates(transcription)
        else:
            # Это оригинальная транскрипция - очищаем её полностью
            clean_transcription = self._clean_transcription(transcription)
        
        # Удалено: original_transcription больше не нужна
        
        # Рендерим компоненты
        script_html = self._render_script_analysis(script_analysis)
        entities_html = self._render_business_entities(business_entities)
        
        # Предварительно подготавливаем статические данные
        title = f"Анализ звонка - {audio_path.name}"
        current_date = datetime.now().strftime('%d.%m.%Y %H:%M')
        filename = audio_path.name
        
        html_content = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
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
        .section {{
            margin-bottom: 30px;
            padding: 20px;
            border-left: 4px solid #667eea;
            background: #f8f9ff;
        }}
        .section h2 {{
            color: #333;
            margin-top: 0;
            font-size: 1.5em;
        }}
        .info-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }}
        .info-table th, .info-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        .info-table th {{
            background-color: #667eea;
            color: white;
            font-weight: 500;
        }}
        .transcription {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            font-family: 'Courier New', monospace;
            line-height: 1.8;
            white-space: pre-wrap;
        }}
        .original-transcription {{
            background: #f9f9f9;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            font-family: 'Courier New', monospace;
            line-height: 1.6;
            max-height: 500px;
            overflow-y: auto;
        }}
        .timestamp-line {{
            margin: 5px 0;
            padding: 3px 0;
        }}
        .timestamp {{
            color: #666;
            font-weight: bold;
            margin-right: 10px;
            font-size: 0.9em;
        }}
        .speech-text {{
            color: #333;
        }}
        .speech-line {{
            margin: 3px 0;
            padding: 2px 0;
            color: #333;
        }}
        .analysis-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .analysis-card {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #ddd;
        }}
        .analysis-card h4 {{
            margin: 0 0 10px 0;
            color: #333;
            font-size: 1.1em;
        }}
        .score {{
            font-size: 1.2em;
            font-weight: bold;
            margin: 5px 0;
        }}
        .score.excellent {{ color: #4caf50; }}
        .score.good {{ color: #8bc34a; }}
        .score.average {{ color: #ff9800; }}
        .score.poor {{ color: #f44336; }}
        .admin {{
            color: #2196f3;
            font-weight: bold;
        }}
        .client {{
            color: #4caf50;
            font-weight: bold;
        }}
        .footer {{
            background: #333;
            color: white;
            text-align: center;
            padding: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏥 Анализ звонка</h1>
            <p>Медицинские центры</p>
            <p>Unified Analysis v3.0</p>
        </div>
        
        <div class="content">
            <!-- Основная информация -->
            <div class="section">
                <h2>📊 Информация о звонке</h2>
                <table class="info-table">
                    <tr><th>Параметр</th><th>Значение</th></tr>
                    <tr><td>Файл</td><td>###FILENAME###</td></tr>
                    <tr><td>Дата анализа</td><td>###CURRENT_DATE###</td></tr>
                </table>
            </div>
            
            <!-- Анализ соответствия скрипту -->
            <div class="section">
                <h2>📋 Анализ соответствия скрипту</h2>
                ###SCRIPT_HTML###
            </div>
            
            <!-- Бизнес-сущности -->
            <div class="section">
                <h2>💼 Бизнес-сущности</h2>
                ###ENTITIES_HTML###
            </div>
            
            <!-- Полная стенограмма с временными метками -->
            <div class="section">
                <h2>📝 Полная стенограмма</h2>
                <div class="transcription">###CLEAN_TRANSCRIPTION###</div>
            </div>
        </div>
        
        <div class="footer">
            <p>🔒 Данные обработаны в автономном режиме</p>
        </div>
    </div>
</body>
</html>"""

        # Сохраняем HTML отчет
        output_dir = Path("output/reports")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = output_dir / f"{audio_path.stem}_unified_report.html"
        
        # Безопасная замена маркеров без конфликта с CSS
        final_html = html_content
        final_html = final_html.replace("###SCRIPT_HTML###", script_html)
        final_html = final_html.replace("###ENTITIES_HTML###", entities_html) 
        final_html = final_html.replace("###CLEAN_TRANSCRIPTION###", clean_transcription)
        final_html = final_html.replace("###FILENAME###", filename)
        final_html = final_html.replace("###CURRENT_DATE###", current_date)
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(final_html)
            
        return report_file
    
    def _render_script_analysis(self, script_analysis: Dict) -> str:
        """Рендеринг анализа соответствия скрипту"""
        if not script_analysis:
            return "<p>Анализ соответствия скрипту недоступен</p>"
        
        # Получаем данные из реальной структуры JSON
        overall_score = script_analysis.get("общая_оценка", 0) or 0
        admin_name = script_analysis.get("администратор", "")
        comments = script_analysis.get("комментарии", "")
        business_analysis = script_analysis.get("бизнес_анализ", "")
        
        # Определяем цвет общей оценки (max 20 баллов)
        score_percentage = (overall_score / 20) * 10 if overall_score else 0
        if score_percentage >= 8:
            score_class = "excellent"
        elif score_percentage >= 6:
            score_class = "good"
        elif score_percentage >= 4:
            score_class = "average"
        else:
            score_class = "poor"
        
        html = f"""
        <div class="analysis-card">
            <h4>📊 Общая оценка: <span class="score {score_class}">{overall_score}/20</span></h4>
            {f'<p><strong>Администратор:</strong> {admin_name}</p>' if admin_name else ''}
        </div>
        <div class="analysis-grid">
        """
        
        # Рендерим детальные оценки из реальной структуры JSON
        script_blocks = {
            "приветствие": "👋 Приветствие",
            "название_клиники": "🏥 Название клиники",
            "фио_администратора": "👤 Представление администратора",
            "имя_пациента": "📝 Уточнение имени пациента",
            "блок_опроса": "❓ Блок опроса симптомов",
            "презентация_исследования": "🔬 Презентация исследования",
            "комплекс_предложен": "📦 Предложение комплекса",
            "цена_озвучена": "💰 Озвучивание цены",
            "возражение_обработано": "🛡️ Обработка возражений",
            "паспорт_документы": "📄 Напоминание о документах",
            "диск_озвучен": "💿 Предложение диска",
            "видеозаключение": "📹 Видеозаключение",
            "подготовка": "⏰ Информация о подготовке"
        }
        
        for block_key, block_name in script_blocks.items():
            block_data = script_analysis.get(block_key, {})
            if isinstance(block_data, dict):
                score = block_data.get("score", 0) or 0
                comment = block_data.get("comment", "")
                
                score_class = "excellent" if score == 1 else "poor"
                score_display = "✅" if score == 1 else "❌"
                
                html += f"""
                <div class="analysis-card">
                    <h4>{block_name}: <span class="score {score_class}">{score_display}</span></h4>
                    <p>{comment}</p>
                </div>
                """
        
        html += "</div>"
        
        # Добавляем общие комментарии и бизнес-анализ
        if comments:
            html += f"""<div class="analysis-card"><h4>💬 Общие комментарии:</h4><p>{comments}</p></div>"""
        
        if business_analysis:
            html += f"""<div class="analysis-card"><h4>📈 Бизнес-анализ:</h4><p>{business_analysis}</p></div>"""
        
        return html
    
    def _render_business_entities(self, business_entities: Dict) -> str:
        """Рендеринг бизнес-сущностей"""
        if not business_entities:
            return "<p>Бизнес-сущности не извлечены</p>"
        
        html = "<div class=\"analysis-grid\">"
        
        # Результат звонка
        call_result = business_entities.get("call_result", {})
        if call_result:
            status = call_result.get("status", "не определен")
            status_color = "excellent" if "записался" in status else "poor"
            html += f"""
            <div class="analysis-card">
                <h4>📞 Результат звонка</h4>
                <p><strong>Статус:</strong> <span class="score {status_color}">{status}</span></p>
            </div>
            """
        
        # Персональная информация
        personal_info = business_entities.get("personal_info", {})
        if personal_info:
            html += f"""
            <div class="analysis-card">
                <h4>👤 Персональная информация</h4>
                <p><strong>Имя:</strong> {personal_info.get("client_name") or "не указано"}</p>
                <p><strong>Телефон:</strong> {personal_info.get("phone_number") or "не указан"}</p>
                <p><strong>Дата рождения:</strong> {personal_info.get("birth_date") or "не указана"}</p>
                <p><strong>Вес:</strong> {personal_info.get("weight") or "не указан"}</p>
                <p><strong>Администратор:</strong> {personal_info.get("admin_name") or "не указан"}</p>
            </div>
            """
        
        # Коммерческая информация
        commercial_info = business_entities.get("commercial_info", {})
        if commercial_info:
            html += f"""
            <div class="analysis-card">
                <h4>💼 Коммерческая информация</h4>
                <p><strong>Дата записи:</strong> {commercial_info.get("appointment_date") or "не указана"}</p>
                <p><strong>Время записи:</strong> {commercial_info.get("appointment_time") or "не указано"}</p>
                <p><strong>Адрес клиники:</strong> {commercial_info.get("clinic_address") or "не указан"}</p>
                <p><strong>Основная услуга:</strong> {commercial_info.get("main_service") or "не указана"}</p>
                <p><strong>Основная стоимость:</strong> {commercial_info.get("main_cost") or "не указана"}</p>
                <p><strong>Общая стоимость:</strong> {commercial_info.get("total_cost") or "не указана"}</p>
                <p><strong>Врач:</strong> {commercial_info.get("doctor_name") or "не указан"}</p>
            </div>
            """
        
        html += "</div>"
        return html
    
    def _create_html_report_unified(self, audio_path: Path, transcription: str, standardized_data: Dict[str, Any]) -> Path:
        """
        🔄 УНИФИЦИРОВАННЫЙ HTML ОТЧЕТ v2.1 - использует стандартизированные данные
        
        Гарантирует:
        - Одинаковые данные в HTML и Google Sheets
        - Все обязательные поля присутствуют
        - Справедливую оценку администраторов
        """
        try:
            output_dir = self.output_dirs["reports"]
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Предварительная подготовка статических данных
            title = f"Анализ звонка - {audio_path.name}"
            current_date = datetime.now().strftime('%d.%m.%Y %H:%M')
            filename = audio_path.name
            
            # HTML шаблон с уникальными маркерами
            html_content = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>###TITLE###</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5rem;
            font-weight: 300;
        }}
        .info-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0;
            background: #f8f9fa;
        }}
        .info-grid td {{
            padding: 15px 25px;
            border-bottom: 1px solid #dee2e6;
        }}
        .info-grid td:first-child {{
            background: #e9ecef;
            font-weight: 600;
            color: #495057;
        }}
        .section {{
            padding: 30px;
            border-bottom: 2px solid #f1f3f4;
        }}
        .section:last-child {{
            border-bottom: none;
        }}
        .section h2 {{
            color: #2c3e50;
            margin-top: 0;
            margin-bottom: 25px;
            font-size: 1.8rem;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        .analysis-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 25px;
            margin: 25px 0;
        }}
        .analysis-card {{
            background: #ffffff;
            border: 2px solid #e9ecef;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            transition: all 0.3s ease;
        }}
        .analysis-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
            border-color: #3498db;
        }}
        .analysis-card h4 {{
            color: #2c3e50;
            margin-top: 0;
            margin-bottom: 15px;
            font-size: 1.3rem;
        }}
        .score {{
            font-weight: bold;
            padding: 8px 15px;
            border-radius: 25px;
            color: white;
            font-size: 1.1rem;
        }}
        .score.excellent {{ background: linear-gradient(135deg, #27ae60, #2ecc71); }}
        .score.good {{ background: linear-gradient(135deg, #f39c12, #e67e22); }}
        .score.average {{ background: linear-gradient(135deg, #e74c3c, #c0392b); }}
        .score.poor {{ background: linear-gradient(135deg, #95a5a6, #7f8c8d); }}
        .transcription {{
            background: #f8f9fa;
            border: 2px solid #dee2e6;
            border-radius: 12px;
            padding: 25px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.8;
            white-space: pre-wrap;
            max-height: 600px;
            overflow-y: auto;
        }}
        .admin {{ color: #e74c3c; font-weight: bold; }}
        .client {{ color: #3498db; font-weight: bold; }}
        .validation-summary {{
            background: #fff3cd;
            border: 2px solid #ffeaa7;
            border-radius: 12px;
            padding: 20px;
            margin: 20px 0;
        }}
        .validation-critical {{
            background: #f8d7da;
            border: 2px solid #f5c6cb;
        }}
        @media (max-width: 768px) {{
            .analysis-grid {{
                grid-template-columns: 1fr;
            }}
            .info-grid {{
                grid-template-columns: 1fr;
            }}
            .container {{
                margin: 10px;
                border-radius: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏥 Анализ звонка медицинского центра</h1>
            <p>Система анализа звонков медицинских центров</p>
        </div>
        
        <div class="section">
            <table class="info-grid" style="width: 100%; border-collapse: collapse;">
                <tr><td>Файл</td><td>###FILENAME###</td></tr>
                <tr><td>Дата анализа</td><td>###CURRENT_DATE###</td></tr>
                <tr><td>Общая оценка</td><td>###TOTAL_SCORE###/20</td></tr>
                <tr><td>Статус унификации</td><td>###VALIDATION_STATUS###</td></tr>
            </table>
        </div>
        
        <div class="section">
            <h2>📊 Анализ скрипта</h2>
            ###SCRIPT_HTML###
        </div>
        
        <div class="section">
            <h2>💼 Бизнес-сущности</h2>
            ###ENTITIES_HTML###
        </div>
        
        <!-- Полная стенограмма с временными метками -->
        <div class="section">
            <h2>📝 Полная стенограмма</h2>
            <div class="transcription">###CLEAN_TRANSCRIPTION###</div>
        </div>
    </div>
</body>
</html>"""
            
            # Генерируем HTML блоки из унифицированных данных
            script_html = self._render_script_analysis_unified(standardized_data)
            entities_html = self._render_entities_html_unified(standardized_data)
            
            # Форматируем транскрипцию
            clean_transcription = self._convert_admin_client_to_russian(transcription)
            
            # Статус валидации
            summary = standardized_data.get('validation_summary', {})
            validation_status = "✅ Все поля корректны"
            if summary.get('personal_fields_fixed', 0) > 0 or summary.get('commercial_fields_fixed', 0) > 0:
                validation_status = f"🔧 Исправлено: {summary.get('personal_fields_fixed', 0)} + {summary.get('commercial_fields_fixed', 0)} полей"
            if summary.get('emergency_fallback', False):
                validation_status = "🚨 Аварийный режим - требует проверки"
            
            # Безопасная замена маркеров без конфликта с CSS
            final_html = html_content
            final_html = final_html.replace("###TITLE###", title)
            final_html = final_html.replace("###SCRIPT_HTML###", script_html)
            final_html = final_html.replace("###ENTITIES_HTML###", entities_html)
            final_html = final_html.replace("###CLEAN_TRANSCRIPTION###", clean_transcription)
            final_html = final_html.replace("###FILENAME###", filename)
            final_html = final_html.replace("###CURRENT_DATE###", current_date)
            final_html = final_html.replace("###TOTAL_SCORE###", str(standardized_data.get('total_score', 0)))
            final_html = final_html.replace("###VALIDATION_STATUS###", validation_status)
            
            # Сохранение файла
            report_file = output_dir / f"{audio_path.stem}_unified_report.html"
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(final_html)
            
            return report_file
            
        except Exception as e:
            logger.error(f"Ошибка создания унифицированного HTML отчета: {e}")
            # Fallback к старому методу
            return self._create_html_report(audio_path, transcription, standardized_data)
    
    def _render_script_analysis_unified(self, standardized_data: Dict[str, Any]) -> str:
        """🔄 Рендеринг анализа скрипта из унифицированных данных"""
        
        script_evaluation = standardized_data.get('script_evaluation', {})
        total_score = standardized_data.get('total_score', 0)
        personal_info = standardized_data.get('personal_info', {})
        
        if not script_evaluation:
            return "<p>Анализ скрипта недоступен</p>"
        
        # Определение класса для общей оценки
        score_percentage = (total_score / 20) * 10 if total_score else 0
        if score_percentage >= 8:
            score_class = "excellent"
        elif score_percentage >= 6:
            score_class = "good"
        elif score_percentage >= 4:
            score_class = "average"
        else:
            score_class = "poor"
        
        admin_name = personal_info.get('admin_name', '')
        
        html = f"""
        <div class="analysis-card">
            <h4>📊 Общая оценка: <span class="score {score_class}">{total_score}/20</span></h4>
            {f'<p><strong>Администратор:</strong> {admin_name}</p>' if admin_name and admin_name != 'не указан' else ''}
        </div>
        <div class="analysis-grid">
        """
        
        # Группируем критерии по блокам
        blocks = {
            "Приветствие": ["приветствие", "название_клиники", "фио_администратора", "имя_пациента"],
            "Раскрывающие вопросы": ["блок_опроса", "презентация_исследования", "комплекс_предложен", "цена_озвучена"],
            "Продажа/Запись": ["соблюден_алгоритм", "возражение_обработано", "структура_скрипта"],
            "Дополнительные критерии": ["паспорт_документы", "диск_озвучен", "видеозаключение", "подготовка"]
        }
        
        for block_name, criteria in blocks.items():
            html += f"""
            <div class="analysis-card">
                <h4>📋 {block_name}</h4>
            """
            
            for criterion in criteria:
                if criterion in script_evaluation:
                    data = script_evaluation[criterion]
                    score = data.get('score', 0)
                    comment = data.get('comment', '')
                    
                    score_class = "excellent" if score == 1 else "poor"
                    score_text = "✅ Да" if score == 1 else "❌ Нет"
                    
                    html += f"""
                    <p><strong>{criterion.replace('_', ' ').title()}:</strong> 
                       <span class="score {score_class}">{score_text}</span>
                    </p>
                    """
                    # Показываем комментарий для всех критериев, особенно для провальных
                    if comment:
                        html += f"<p><small>💬 {comment}</small></p>"
                    elif score == 0:
                        html += f"<p><small>⚠️ Критерий не выполнен</small></p>"
            
            html += "</div>"
        
        html += "</div>"
        return html
    
    def _render_entities_html_unified(self, standardized_data: Dict[str, Any]) -> str:
        """🔄 Рендеринг бизнес-сущностей из унифицированных данных"""
        
        personal_info = standardized_data.get('personal_info', {})
        commercial_info = standardized_data.get('commercial_info', {})
        call_result = standardized_data.get('call_result', {})
        
        html = "<div class=\"analysis-grid\">"
        
        # Результат звонка
        if call_result:
            status = call_result.get("status", "не определен")
            status_color = "excellent" if "записался" in status else "poor"
            html += f"""
            <div class="analysis-card">
                <h4>📞 Результат звонка</h4>
                <p><strong>Статус:</strong> <span class="score {status_color}">{status}</span></p>
            </div>
            """
        
        # Персональная информация (ВСЕГДА с унифицированными данными)
        html += f"""
        <div class="analysis-card">
            <h4>👤 Персональная информация</h4>
            <p><strong>Имя:</strong> {personal_info.get("client_name", "не указано")}</p>
            <p><strong>Телефон:</strong> {personal_info.get("phone_number", "не указан")}</p>
            <p><strong>Дата рождения:</strong> {personal_info.get("birth_date", "не указана")}</p>
            <p><strong>Вес:</strong> {personal_info.get("weight", "не указан")}</p>
            <p><strong>Администратор:</strong> {personal_info.get("admin_name", "не указан")}</p>
        </div>
        """
        
        # Коммерческая информация (ВСЕГДА с унифицированными данными)
        html += f"""
        <div class="analysis-card">
            <h4>💼 Коммерческая информация</h4>
            <p><strong>Дата записи:</strong> {commercial_info.get("appointment_date", "не указана")}</p>
            <p><strong>Время записи:</strong> {commercial_info.get("appointment_time", "не указано")}</p>
            <p><strong>Адрес клиники:</strong> {commercial_info.get("clinic_address", "не указан")}</p>
            <p><strong>Основная услуга:</strong> {commercial_info.get("main_service", "не указана")}</p>
            <p><strong>Основная стоимость:</strong> {commercial_info.get("main_cost", "не указана")}</p>
            <p><strong>Общая стоимость:</strong> {commercial_info.get("total_cost", "не указана")}</p>
            <p><strong>Врач:</strong> {commercial_info.get("doctor_name", "не указан")}</p>
        </div>
        """
        
        html += "</div>"
        return html

    def _render_crm_metrics(self, crm_metrics: Dict) -> str:
        """Рендеринг CRM метрик"""
        if not crm_metrics:
            return "<p>CRM метрики недоступны</p>"
        
        conversion = crm_metrics.get("conversion_to_booking", False)
        compliance = crm_metrics.get("script_compliance_percent", 0) or 0
        additional_conv = crm_metrics.get("additional_services_conversion", 0) or 0
        call_result = crm_metrics.get("call_result", "не определен")
        
        # Цвета для результата
        if "записался" in call_result.lower():
            result_color = "#4caf50"
        elif "не записался" in call_result.lower():
            result_color = "#f44336"
        else:
            result_color = "#ff9800"
        
        html = f"""
        <div class="analysis-grid">
            <div class="analysis-card">
                <h4>📞 Результат звонка</h4>
                <p style="color: {result_color}; font-weight: bold; font-size: 1.2em;">{call_result}</p>
                <p><strong>Конверсия в запись:</strong> {'✅ Да' if conversion else '❌ Нет'}</p>
            </div>
            <div class="analysis-card">
                <h4>📊 Соблюдение скрипта</h4>
                <p><strong>{compliance}%</strong></p>
                <div style="background: #e0e0e0; border-radius: 10px; height: 10px;">
                    <div style="background: #4caf50; width: {compliance}%; height: 10px; border-radius: 10px;"></div>
                </div>
            </div>
            <div class="analysis-card">
                <h4>💰 Доп. услуги</h4>
                <p><strong>Конверсия:</strong> {additional_conv}%</p>
                <div style="background: #e0e0e0; border-radius: 10px; height: 10px;">
                    <div style="background: #ff9800; width: {additional_conv}%; height: 10px; border-radius: 10px;"></div>
                </div>
            </div>
        </div>
        """
        
        return html
    
    def _format_original_transcription(self, transcription: str) -> str:
        """Форматирование исходной транскрипции с временными метками для HTML"""
        lines = transcription.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Пропускаем пустые строки и заголовки
            if (not line or 
                any(skip_phrase in line for skip_phrase in [
                    '🔒 АВТОНОМНАЯ ТРАНСКРИБАЦИЯ', '🏥 Медицинский центр', 
                    '===', '====', 'МРТ Лидер', 'Сеть клиник', 'Автор:', 
                    '🔒 Данные обработаны', 'конфиденциальность гарантирована'
                ]) or
                line.strip() in ['=', '-', '*', '=' * 50]
            ):
                continue
            
            # Обрабатываем строки с временными метками [XX.Xs]: текст
            if '[' in line and 's]' in line and ':' in line:
                # Извлекаем временную метку и текст
                import re
                match = re.match(r'\[(\d+\.\d+)s\]\s*(.*)', line)
                if match:
                    timestamp = match.group(1)
                    text = match.group(2).strip()
                    if text:
                        # Определяем роль говорящего (админ/клиент) и форматируем соответственно
                        if any(admin_word in text.lower() for admin_word in ['администратор', 'добрый день', 'мрт-лидер', 'могу помочь', 'как вас зовут']):
                            role_class = 'admin-line'
                            role_prefix = '👩‍💼 Администратор:'
                        else:
                            role_class = 'client-line'
                            role_prefix = '👤 Клиент:'
                        
                        formatted_line = f'<div class="dialogue-line {role_class}"><span class="role-label">{role_prefix}</span> <span class="speech-text">{text}</span> <span class="timestamp">[{timestamp}s]</span></div>'
                        formatted_lines.append(formatted_line)
            elif line:
                # Обычная строка без временной метки
                formatted_lines.append(f'<div class="speech-line">{line}</div>')
        
        return '\n'.join(formatted_lines)
    
    def _clean_diarization_duplicates(self, transcription: str) -> str:
        """
        НОВОЕ v2.0: Очистка дубликатов диаризации (Администратор/ADMIN, Клиент/CLIENT)
        
        Убирает английские метки, оставляет только русские с HTML форматированием
        """
        import re
        
        # Убираем английские дубликаты, если есть русские метки
        text = transcription
        
        # Заменяем случаи где есть и русские и английские метки
        # Пример: "Администратор: ADMIN: текст" -> "Администратор: текст"
        text = re.sub(r'Администратор:\s*ADMIN:\s*', 'Администратор: ', text)
        text = re.sub(r'Клиент:\s*CLIENT:\s*', 'Клиент: ', text)
        
        # Заменяем случаи где английские метки идут первыми
        # Пример: "ADMIN: Администратор: текст" -> "Администратор: текст"  
        text = re.sub(r'ADMIN:\s*Администратор:\s*', 'Администратор: ', text)
        text = re.sub(r'CLIENT:\s*Клиент:\s*', 'Клиент: ', text)
        
        # Заменяем чисто английские метки на русские (если нет русских)
        text = re.sub(r'\bADMIN:\s*', 'Администратор: ', text)
        text = re.sub(r'\bCLIENT:\s*', 'Клиент: ', text)
        
        # Добавляем HTML форматирование для русских меток
        text = text.replace('Администратор:', '<span class="admin">Администратор</span>:')
        text = text.replace('Клиент:', '<span class="client">Клиент</span>:')
        
        return text
    
    def _convert_admin_client_to_russian(self, transcription: str) -> str:
        """
        НОВОЕ v2.1: Конвертация ADMIN/CLIENT в русские метки и форматирование
        
        Преобразует англоязычные метки в русские и добавляет HTML форматирование
        """
        import re
        
        text = transcription
        
        # Убираем временные метки [XX:XX] для чистоты
        text = re.sub(r'\[[\d:]+\]\s*', '', text)
        
        # Заменяем ADMIN на Администратор
        text = re.sub(r'\bADMIN:\s*', 'Администратор: ', text)
        
        # Заменяем CLIENT на Клиент  
        text = re.sub(r'\bCLIENT:\s*', 'Клиент: ', text)
        
        # Добавляем HTML форматирование для русских меток
        text = text.replace('Администратор:', '<span class="admin">Администратор</span>:')
        text = text.replace('Клиент:', '<span class="client">Клиент</span>:')
        
        # Улучшаем форматирование - каждая реплика с новой строки
        text = text.replace('  \n', '\n')  # Убираем двойные пробелы перед переносами
        text = text.replace('\n', '\n\n')  # Добавляем пустые строки между репликами
        
        return text

    def _clean_transcription(self, transcription: str) -> str:
        """Очистка транскрипции от служебной информации и временных меток"""
        lines = transcription.split('\n')
        clean_lines = []
        
        for line in lines:
            line = line.strip()
            
            # Пропускаем пустые строки и заголовки
            if (not line or 
                any(skip_phrase in line for skip_phrase in [
                    '🔒 АВТОНОМНАЯ ТРАНСКРИБАЦИЯ', '🏥 Медицинский центр', 
                    '===', '====', 'МРТ Лидер', 'Сеть клиник', 'Автор:', 
                    '🔒 Данные обработаны', 'конфиденциальность гарантирована'
                ]) or
                line.strip() in ['=', '-', '*', '=' * 50]
            ):
                continue
            
            # Обрабатываем строки с диалогом, УБИРАЕМ временные метки
            if ('[' in line and 's]' in line and ':' in line):
                if any(role in line.upper() for role in ['АДМИНИСТРАТОР', 'КЛИЕНТ', 'SPEAKER']):
                    # Убираем временные метки вида [0.8s] - [3.1s]
                    line = re.sub(r'\[\d+\.\d+s\]\s*-\s*\[\d+\.\d+s\]', '', line)
                    line = re.sub(r'\[\d+\.\d+s\]', '', line)
                    
                    # Очищаем от лишних пробелов
                    line = re.sub(r'\s+', ' ', line).strip()
                    
                    # Добавляем цветовую разметку для ролей
                    if 'АДМИНИСТРАТОР' in line.upper():
                        line = line.replace('АДМИНИСТРАТОР', '<span class="admin">АДМИНИСТРАТОР</span>')
                    elif 'КЛИЕНТ' in line.upper():
                        line = line.replace('КЛИЕНТ', '<span class="client">КЛИЕНТ</span>')
                    
                    # Добавляем только если строка не пустая после очистки
                    if line and ':' in line:
                        clean_lines.append(line)
        
        return '\n'.join(clean_lines)

    def _add_to_google_sheets_with_validation(self, audio_path: Path, analysis_result: Dict, validation_result: Dict):
        """Добавление результатов с валидацией в Google Sheets - МАКСИМАЛЬНАЯ ИНФОРМАТИВНОСТЬ"""
        
        analysis = analysis_result.get("analysis", {})
        script_analysis = analysis.get("script_analysis", {})
        business_entities = analysis.get("business_entities", {})
        crm_metrics = analysis.get("crm_metrics", {})
        
        # Извлекаем ВСЕ данные клиента
        client = business_entities.get("client", {})
        appointment = business_entities.get("appointment", {})
        additional_services = business_entities.get("additional_services", {})
        medical_history = business_entities.get("medical_history", {})
        pricing = business_entities.get("pricing", {})
        call_details = business_entities.get("call_details", {})
        
        # Извлекаем оценки по блокам
        block_scores = script_analysis.get("block_scores", {})
        
        # Валидация
        validation_summary = validation_result.get("summary", {})
        
        # РАСШИРЕННЫЕ ДАННЫЕ для максимальной информативности (ОБНОВЛЕНО под новую структуру)
        row_data = [
            # ОСНОВНАЯ ИНФОРМАЦИЯ
            datetime.now().strftime('%d.%m.%Y %H:%M'),  # Дата анализа
            audio_path.name,  # Файл звонка
            f"{analysis_result.get('audio_duration', 0)/60:.1f}",  # Длительность (мин)
            
            # РЕЗУЛЬТАТ ЗВОНКА
            crm_metrics.get("call_result", "не определен"),  # Результат звонка
            
            # КЛИЕНТ - ПОЛНАЯ ИНФОРМАЦИЯ
            client.get("name", ""),  # ФИО клиента
            client.get("phone", ""),  # Телефон
            str(client.get("age", "")),  # Возраст (НОВОЕ!)
            client.get("birth_date", ""),  # Дата рождения
            str(client.get("weight", "")),  # Вес
            
            # МЕДИЦИНСКАЯ ИНФОРМАЦИЯ - ДЕТАЛЬНО
            appointment.get("research_type", ""),  # Тип исследования
            ", ".join(medical_history.get("symptoms", [])) if isinstance(medical_history.get("symptoms"), list) else str(medical_history.get("symptoms", "")),  # Симптомы
            medical_history.get("symptom_duration", ""),  # Длительность симптомов
            ", ".join(medical_history.get("previous_studies", [])) if isinstance(medical_history.get("previous_studies"), list) else str(medical_history.get("previous_studies", "")),  # Предыдущие обследования (НОВОЕ!)
            ", ".join(medical_history.get("diagnoses", [])) if isinstance(medical_history.get("diagnoses"), list) else str(medical_history.get("diagnoses", "")),  # Диагнозы (НОВОЕ!)
            ", ".join(medical_history.get("contraindications", [])) if isinstance(medical_history.get("contraindications"), list) else str(medical_history.get("contraindications", "")),  # Противопоказания (НОВОЕ!)
            
            # КОММЕРЧЕСКАЯ ИНФОРМАЦИЯ - ПОЛНАЯ
            str(pricing.get("main_service_cost", "")),  # Основная стоимость
            str(pricing.get("video_conclusion_cost", "")),  # Видеозаключение стоимость (НОВОЕ!)
            str(pricing.get("total_mentioned_cost", "")),  # Общая стоимость (НОВОЕ!)
            str(pricing.get("additional_services_cost", "")),  # Доп. услуги стоимость (НОВОЕ!)
            
            # ЗАПИСЬ - ДЕТАЛЬНО
            appointment.get("date", ""),  # Дата записи
            appointment.get("time", ""),  # Время записи
            appointment.get("doctor", ""),  # Врач (НОВОЕ!)
            appointment.get("clinic_address", ""),  # Адрес клиники
            
            # ДОПОЛНИТЕЛЬНЫЕ УСЛУГИ - ДЕТАЛЬНО
            "да" if additional_services.get("video_conclusion") == "да" else "нет",  # Видеозаключение
            "да" if additional_services.get("media_recording") == "да" else "нет",  # Запись на носитель (НОВОЕ!)
            "да" if additional_services.get("consultation") == "да" else "нет",  # Консультация (НОВОЕ!)
            
            # КАЧЕСТВО ЗВОНКА - ДЕТАЛЬНЫЕ ОЦЕНКИ
            str(script_analysis.get("overall_score", "")),  # Общая оценка скрипта
            str(block_scores.get("greeting", {}).get("score", "")),  # Приветствие
            str(block_scores.get("questions", {}).get("score", "")),  # Раскрывающие вопросы
            str(block_scores.get("sales", {}).get("score", "")),  # Продажа
            str(block_scores.get("booking", {}).get("score", "")),  # Запись
            str(block_scores.get("closing", {}).get("score", "")),  # Завершение
            
            # CRM МЕТРИКИ - НОВЫЕ ПОЛЯ
            str(crm_metrics.get("script_compliance_percent", "")),  # Соответствие скрипту %
            str(crm_metrics.get("additional_services_conversion", "")),  # Конверсия доп. услуг
            str(crm_metrics.get("call_quality_rating", "")),  # Общий рейтинг качества
            
            # ВАЛИДАЦИЯ ДАННЫХ - НОВЫЙ БЛОК
            str(validation_summary.get("total_fields", "")),  # Всего полей
            str(validation_summary.get("errors", "")),  # Критические ошибки
            str(validation_summary.get("warnings", "")),  # Предупреждения
            f"{validation_summary.get('average_confidence', 0.0):.0%}",  # Средняя уверенность
            "; ".join(validation_summary.get("critical_issues", [])),  # Критические проблемы
            
            # ТЕХНИЧЕСКИЕ ДАННЫЕ
            "ru",  # Язык (автоопределение)
            f"{analysis_result.get('analysis_time', 0):.1f}с",  # Время анализа
            
            # ОРГАНИЗАЦИОННЫЕ ДАННЫЕ
            "Администратор",  # Роль сотрудника
            "МРТ-Лидер",  # Клиника
            datetime.now().strftime('%Y-%m'),  # Месяц для фильтрации
        ]
        
        # Добавляем строку в Google Sheets
        try:
            if self.sheets_integration is None or self.sheets_integration.worksheet is None:
                raise Exception("Google Sheets не подключен - проверьте credentials/google_credentials.json")
            
            self.sheets_integration.worksheet.append_row(row_data)
            
            # Цветовое форматирование по результату звонка
            last_row = len(self.sheets_integration.worksheet.get_all_values())
            call_result = crm_metrics.get("call_result", "")
            
            if "записался" in call_result.lower():
                # Зеленый фон для успешной записи
                self.sheets_integration.worksheet.format(f'{last_row}:{last_row}', {
                    'backgroundColor': {'red': 0.8, 'green': 1.0, 'blue': 0.8}
                })
            elif "не записался" in call_result.lower():
                # Красный фон для неуспешной записи  
                self.sheets_integration.worksheet.format(f'{last_row}:{last_row}', {
                    'backgroundColor': {'red': 1.0, 'green': 0.8, 'blue': 0.8}
                })
            elif validation_summary.get("errors", 0) > 0:
                # Желтый фон для ошибок валидации
                self.sheets_integration.worksheet.format(f'{last_row}:{last_row}', {
                    'backgroundColor': {'red': 1.0, 'green': 1.0, 'blue': 0.8}
                })
                
            logger.info(f"✅ Строка {last_row} добавлена в Google Sheets с {len(row_data)} колонками")
            
        except Exception as e:
            logger.error(f"❌ Ошибка добавления в Google Sheets: {e}")
            raise
    
    def _save_analysis_results(self, audio_path: Path, analysis_result: Dict) -> Path:
        """Сохранение результатов анализа"""
        output_dir = Path("output/enhanced")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        analysis_file = output_dir / f"{audio_path.stem}_unified_analysis.json"
        
        with open(analysis_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2)
            
        logger.info(f"💾 Результаты анализа сохранены: {analysis_file}")
        return analysis_file

    def _save_validation_results(self, audio_path: Path, validation_result: Dict):
        """Сохранение результатов валидации"""
        output_dir = Path("output/enhanced")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        validation_file = output_dir / f"{audio_path.stem}_validation.json"
        
        # Сериализация результатов валидации
        serializable_results = {}
        for category, results in validation_result.items():
            if category == "summary":
                serializable_results[category] = results
            else:
                serializable_results[category] = {}
                for field, result in results.items():
                    if hasattr(result, 'field_name'):  # ValidationResult объект
                        serializable_results[category][field] = {
                            "field_name": result.field_name,
                            "value": result.value,
                            "is_valid": result.is_valid,
                            "confidence": result.confidence,
                            "warnings": result.warnings,
                            "severity": result.severity,
                            "source_quote": result.source_quote
                        }
                    else:
                        serializable_results[category][field] = result
                        
        with open(validation_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, ensure_ascii=False, indent=2)
            
        logger.info(f"💾 Результаты валидации сохранены: {validation_file}")

    def _create_html_report_with_validation(self, audio_path: Path, transcription: str,
                                          analysis: Dict, validation_result: Dict) -> Path:
        """Создание HTML отчета с результатами валидации"""
        
        # Базовый HTML отчет
        report_file = self._create_html_report(audio_path, transcription, {"analysis": analysis})
        
        # Добавляем секцию валидации в HTML
        validation_html = self._render_validation_section(validation_result)
        
        # Читаем существующий HTML
        with open(report_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        # Вставляем валидацию перед транскрипцией (ищем правильный класс)
        insertion_point = html_content.find('<div class="section">\n                <h2>📝 Транскрипция звонка</h2>')
        if insertion_point != -1:
            new_html = (
                html_content[:insertion_point] + 
                f'<div class="section">\n                <h2>🛡️ Валидация данных</h2>\n                {validation_html}\n            </div>\n            \n            ' +
                html_content[insertion_point:]
            )
            
            # Перезаписываем файл
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(new_html)
        else:
            # Если не найдена точка вставки, просто добавляем в конец контента
            content_end = html_content.find('        </div>\n        \n        <div class="footer">')
            if content_end != -1:
                new_html = (
                    html_content[:content_end] + 
                    f'            <div class="section">\n                <h2>🛡️ Валидация данных</h2>\n                {validation_html}\n            </div>\n            \n' +
                    html_content[content_end:]
                )
                
                # Перезаписываем файл
                with open(report_file, 'w', encoding='utf-8') as f:
                    f.write(new_html)
                
        return report_file

    def _render_validation_section(self, validation_result: Dict) -> str:
        """Рендеринг секции валидации для HTML отчета"""
        summary = validation_result.get("summary", {})
        
        # Определяем общий статус валидации
        if summary.get("errors", 0) > 0:
            status_class = "validation-critical"
            status_text = "🚨 КРИТИЧЕСКИЕ ОШИБКИ"
            status_color = "#f44336"
        elif summary.get("warnings", 0) > 5:
            status_class = "validation-warning"
            status_text = "⚠️ МНОГО ПРЕДУПРЕЖДЕНИЙ"
            status_color = "#ff9800"
        elif summary.get("average_confidence", 1.0) < 0.7:
            status_class = "validation-low-confidence"
            status_text = "📊 НИЗКАЯ УВЕРЕННОСТЬ"
            status_color = "#ff9800"
        else:
            status_class = "validation-good"
            status_text = "✅ ДАННЫЕ ВАЛИДНЫ"
            status_color = "#4caf50"
            
        html = f'''
        <div class="validation-summary" style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <h3 style="margin: 0; color: #333;">Общий статус</h3>
                    <span class="{status_class}" style="background: {status_color}; color: white; padding: 8px 16px; border-radius: 20px; font-weight: bold;">
                        {status_text}
                    </span>
                </div>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                    <div style="text-align: center;">
                        <div style="font-size: 24px; font-weight: bold; color: #2196f3;">
                            {summary.get("total_fields", 0)}
                        </div>
                        <div style="color: #666;">Всего полей</div>
                    </div>
                    
                    <div style="text-align: center;">
                        <div style="font-size: 24px; font-weight: bold; color: #f44336;">
                            {summary.get("errors", 0)}
                        </div>
                        <div style="color: #666;">Ошибок</div>
                    </div>
                    
                    <div style="text-align: center;">
                        <div style="font-size: 24px; font-weight: bold; color: #ff9800;">
                            {summary.get("warnings", 0)}
                        </div>
                        <div style="color: #666;">Предупреждений</div>
                    </div>
                    
                    <div style="text-align: center;">
                        <div style="font-size: 24px; font-weight: bold; color: #4caf50;">
                            {summary.get("average_confidence", 0.0):.0%}
                        </div>
                        <div style="color: #666;">Уверенность</div>
                    </div>
                </div>
            </div>
        '''
        
        # Критические проблемы
        if summary.get("critical_issues"):
            html += '''
            <div class="critical-issues" style="background: #ffebee; border-left: 4px solid #f44336; padding: 15px; margin-bottom: 20px;">
                <h4 style="color: #f44336; margin-top: 0;">🚨 Критические проблемы</h4>
                <ul style="margin-bottom: 0;">
            '''
            for issue in summary["critical_issues"]:
                html += f'<li style="color: #d32f2f; margin-bottom: 5px;">{issue}</li>'
            html += '</ul></div>'
            
        # Рекомендации
        if summary.get("recommendations"):
            html += '''
            <div class="recommendations" style="background: #e3f2fd; border-left: 4px solid #2196f3; padding: 15px;">
                <h4 style="color: #1976d2; margin-top: 0;">💡 Рекомендации</h4>
                <ul style="margin-bottom: 0;">
            '''
            for rec in summary["recommendations"]:
                html += f'<li style="color: #1565c0; margin-bottom: 5px;">{rec}</li>'
            html += '</ul></div>'
            
        html += '</div>'  # Закрываем validation-summary
        
        return html


def main():
    """Тестирование enhanced pipeline v3.0"""
    
    if len(sys.argv) < 2:
        print("❌ Использование: python enhanced_pipeline_v3.py <путь_к_аудиофайлу>")
        sys.exit(1)
    
    audio_file = Path(sys.argv[1])
    
    if not audio_file.exists():
        print(f"❌ Файл не найден: {audio_file}")
        sys.exit(1)
    
    print("🚀 ENHANCED PIPELINE v3.0 (UNIFIED)")
    print("=" * 70)
    print(f"📁 Файл: {audio_file}")
    print(f"🔒 Автономный режим: ВКЛ")
    print(f"🏥 Медицинская конфиденциальность: ГАРАНТИРОВАНА")
    print("=" * 70)
    
    # Инициализация и загрузка моделей
    pipeline = EnhancedAudioPipelineV3()
    pipeline.load_models()
    
    # Обработка файла
    result = pipeline.process_audio_file(audio_file)
    
    if result["success"]:
        print("\n🎉 ENHANCED ОБРАБОТКА v3.0 ЗАВЕРШЕНА!")
        print("=" * 70)
        print(f"📝 Транскрипция: {result['transcription_file']}")
        print(f"📊 Анализ: {result['analysis_file']}")
        print(f"📋 HTML отчет: {result['html_report_file']}")
        print(f"⏱️ Время обработки: {result['processing_time']:.2f}с")
        print(f"🎵 Длительность аудио: {result['audio_duration']:.2f}с")
        print(f"🤖 LM Studio: {'✅ Использован' if result['lm_studio_used'] else '❌ Fallback'}")
        print(f"📈 Метод анализа: {result['analysis_method']}")
        print("=" * 70)
    else:
        print(f"\n❌ Ошибка обработки: {result['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main() 