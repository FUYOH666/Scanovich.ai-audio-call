#!/usr/bin/env python3
"""
АВТОНОМНЫЙ Аудио Pipeline для медицинских центров
БЕЗ ИНТЕРНЕТА, БЕЗ ТОКЕНОВ - полная конфиденциальность

Автор: Scanovich
Python 3.11 + WhisperX (OFFLINE)
"""

# ПЕРВЫМ ДЕЛОМ настраиваем автономный режим  
from config_offline import setup_offline_environment, verify_offline_setup
setup_offline_environment()

import sys
import time
import logging
import gc
from pathlib import Path
from typing import Dict

import whisperx
import soundfile as sf

# Настройка логирования с правильным путем
log_dir = Path("output/logs")
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'offline_pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class OfflineAudioPipeline:
    """Полностью автономный класс для обработки аудио без интернета"""
    
    def __init__(self):
        # НЕТ ТОКЕНОВ - работаем только с локальными моделями
        self.device = "cpu"  # Надежный CPU режим
        self.compute_type = "int8"
        
        # Модели WhisperX
        self.whisper_model = None
        self.align_model = None
        self.align_metadata = None

        
        logger.info("🔒 Инициализация АВТОНОМНОГО pipeline")
        logger.info("🏥 Режим: МЕДИЦИНСКИЙ (без интернета)")
        
    def load_models(self):
        """Загрузка ТОЛЬКО локальных моделей"""
        logger.info("📦 Загрузка локальных моделей...")
        
        try:
            # Проверяем готовность
            if not verify_offline_setup():
                raise Exception("Локальные модели не готовы!")
            
            # 1. Загрузка Whisper из локального кэша (автоопределение языка)
            logger.info("🎯 Загрузка локального Whisper large-v3...")
            self.whisper_model = whisperx.load_model(
                "large-v3", 
                self.device, 
                compute_type=self.compute_type
                # language=None - автоопределение языка (ru, kk, en, th)
            )
            
            # 2. Загрузка выравнивания будет динамической по языку
            logger.info("⚡ Подготовка к загрузке модели выравнивания...")
            # Модель выравнивания будет загружена после определения языка
            self.align_model = None
            self.align_metadata = None
            
            # 3. Диаризация убрана - теперь делается через LLM в unified_pipeline
            
            logger.info("✅ Все локальные модели загружены!")
            logger.info("🔒 Интернет НЕ ИСПОЛЬЗУЕТСЯ")
            
        except Exception as e:
            logger.error(f"💥 Ошибка загрузки локальных моделей: {e}")
            raise
            
    def get_audio_info(self, audio_path: Path) -> Dict:
        """Получение информации об аудиофайле"""
        try:
            audio_data, sample_rate = sf.read(str(audio_path))
            duration = len(audio_data) / sample_rate
            
            return {
                "path": str(audio_path),
                "duration": duration,
                "sample_rate": sample_rate,
                "channels": 1 if len(audio_data.shape) == 1 else audio_data.shape[1]
            }
        except Exception as e:
            logger.error(f"Ошибка получения информации об аудио: {e}")
            return {}
    
    def transcribe_audio(self, audio_path: Path) -> Dict:
        """Автономная транскрибация аудио с диаризацией"""
        logger.info(f"🎯 Начало АВТОНОМНОЙ транскрибации: {audio_path}")
        start_time = time.time()
        
        try:
            # Загрузка аудио
            audio = whisperx.load_audio(str(audio_path))
            
            # 1. Транскрибация с локальным Whisper (автоопределение языка)
            logger.info("🎤 Транскрибация с локальным Whisper...")
            result = self.whisper_model.transcribe(
                audio, 
                batch_size=4,  # Консервативный размер для стабильности
                # language=None - автоопределение языка (ru, kk, en, th)
            )
            
            # 2. Выравнивание с динамической загрузкой модели по языку
            detected_language = result.get("language", "ru")
            logger.info(f"🌍 Определен язык: {detected_language}")
            
            # Поддерживаемые языки: русский, казахский, английский, тайский
            language_map = {"ru": "ru", "kk": "ru", "en": "en", "th": "en"}
            align_language = language_map.get(detected_language, "ru")
            
            logger.info(f"⚡ Загрузка модели выравнивания для языка: {align_language}")
            self.align_model, self.align_metadata = whisperx.load_align_model(
                language_code=align_language, 
                device=self.device
            )
            
            logger.info("⚡ Выравнивание с локальными моделями...")
            result = whisperx.align(
                result["segments"], 
                self.align_model, 
                self.align_metadata, 
                audio, 
                self.device, 
                return_char_alignments=False
            )
            
            # 3. Диаризация убрана - выполняется через LLM на ЭТАПЕ 2 в unified_pipeline
            logger.info("⚡ Диаризация будет выполнена через LLM (ЭТАП 2)")
            
            processing_time = time.time() - start_time
            logger.info(f"✅ АВТОНОМНАЯ транскрибация завершена за {processing_time:.2f}с")
            
            return {
                "segments": result["segments"],
                "processing_time": processing_time,
                "language": result.get("language", "ru"),
                "offline_mode": True
            }
            
        except Exception as e:
            logger.error(f"💥 Ошибка автономной транскрибации: {e}")
            raise
    


    def format_transcription(self, result: Dict) -> str:
        """Форматирование транскрипции БЕЗ диаризации (только Whisper + временные метки)"""
        formatted_text = []
        
        # Добавляем заголовок об автономном режиме
        formatted_text.append("🔒 АВТОНОМНАЯ ТРАНСКРИБАЦИЯ (БЕЗ ИНТЕРНЕТА)")
        formatted_text.append("🏥 Медицинский центр")
        formatted_text.append("🎭 Диаризация будет выполнена через LLM на ЭТАПЕ 2")
        formatted_text.append("=" * 50)
        formatted_text.append("")
        
        # Простое форматирование с временными метками (БЕЗ ролей)
        segments = result["segments"]
        
        for segment in segments:
            start_time = f"{segment['start']:.1f}s"
            text = segment['text'].strip()
            
            # Только временная метка + текст (роли будут назначены LLM)
            formatted_text.append(f"[{start_time}] {text}")
        
        formatted_text.append("")
        formatted_text.append("🔒 Данные обработаны локально, конфиденциальность гарантирована")
        formatted_text.append("🎭 Роли администратор/клиент будут определены LLM для максимальной точности")
        
        return "\n".join(formatted_text)
    

    
    def process_audio_file(self, audio_path: Path) -> Dict:
        """Полная автономная обработка аудиофайла"""
        logger.info(f"🚀 Начало АВТОНОМНОЙ обработки: {audio_path}")
        total_start_time = time.time()
        
        try:
            # 1. Получение информации об аудио
            audio_info = self.get_audio_info(audio_path)
            logger.info(f"📊 Аудио информация: {audio_info}")
            
            # 2. Автономная транскрибация с диаризацией
            transcription_result = self.transcribe_audio(audio_path)
            
            # 3. Форматирование транскрипции
            formatted_transcription = self.format_transcription(transcription_result)
            
            # 4. Сохранение результатов в структурированную папку
            output_name = audio_path.stem
            
            # Создаем папки если не существуют
            output_dir = Path("output")
            transcriptions_dir = output_dir / "transcriptions"
            logs_dir = output_dir / "logs"
            transcriptions_dir.mkdir(parents=True, exist_ok=True)
            logs_dir.mkdir(parents=True, exist_ok=True)
            
            # Сохраняем транскрипцию
            transcription_file = transcriptions_dir / f"{output_name}_offline_transcription.txt"
            transcription_file.write_text(formatted_transcription, encoding='utf-8')
            logger.info(f"💾 Автономная транскрипция сохранена: {transcription_file}")
            
            total_processing_time = time.time() - total_start_time
            
            logger.info(f"🎉 АВТОНОМНАЯ обработка завершена! Время: {total_processing_time:.2f}с")
            
            # 🛠️ СТАБИЛИЗАЦИЯ v5.0: Очистка памяти после транскрипции
            try:
                # Принудительная очистка для предотвращения утечек памяти WhisperX
                collected = gc.collect()
                if collected > 0:
                    logger.info(f"🧹 Очищено {collected} объектов после транскрипции")
            except Exception as gc_error:
                logger.warning(f"⚠️ Ошибка очистки памяти: {gc_error}")
            
            return {
                "success": True,
                "transcription_file": str(transcription_file),
                "processing_time": total_processing_time,
                "audio_duration": audio_info.get("duration", 0),
                "transcription": formatted_transcription,
                "offline_mode": True,
                "privacy_guaranteed": True
            }
            
        except Exception as e:
            logger.error(f"💥 Ошибка автономной обработки: {e}")
            return {
                "success": False,
                "error": str(e),
                "offline_mode": True
            }


def main():
    """Главная функция для автономной обработки"""
    
    # Проверка аргументов командной строки
    if len(sys.argv) != 2:
        print("Использование: python offline_pipeline.py <путь_к_аудиофайлу>")
        print("Пример: python offline_pipeline.py test_call.mp3")
        sys.exit(1)
    
    audio_path = Path(sys.argv[1])
    
    if not audio_path.exists():
        print(f"❌ Ошибка: файл {audio_path} не найден!")
        sys.exit(1)
    
    # Инициализация автономного pipeline
    pipeline = OfflineAudioPipeline()
    
    try:
        print("🔒 ЗАПУСК АВТОНОМНОГО PIPELINE")
        print("🏥 МЕДИЦИНСКИЙ РЕЖИМ - БЕЗ ИНТЕРНЕТА")
        print("=" * 60)
        
        # Загрузка локальных моделей
        pipeline.load_models()
        
        # Обработка файла
        result = pipeline.process_audio_file(audio_path)
        
        if result["success"]:
            print("\n🎉 АВТОНОМНАЯ ОБРАБОТКА ЗАВЕРШЕНА!")
            print("=" * 60)
            print(f"📝 Транскрипция: {result['transcription_file']}")
            print(f"⏱️  Время обработки: {result['processing_time']:.2f}с")
            print(f"🎵 Длительность аудио: {result['audio_duration']:.2f}с")
            print("🔒 ДАННЫЕ НЕ ПОКИДАЛИ СИСТЕМУ")
            print("🏥 МЕДИЦИНСКАЯ КОНФИДЕНЦИАЛЬНОСТЬ СОБЛЮДЕНА")
            
        else:
            print(f"\n❌ ОШИБКА АВТОНОМНОЙ ОБРАБОТКИ: {result['error']}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Автономная обработка прервана пользователем")
    except Exception as e:
        print(f"\n💥 КРИТИЧЕСКАЯ ОШИБКА: {e}")
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main() 