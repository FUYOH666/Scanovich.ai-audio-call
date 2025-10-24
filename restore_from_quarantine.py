#!/usr/bin/env python3
"""
Скрипт восстановления файлов из карантина.

Декодирует JSON-wrapped файлы и перемещает их обратно в input/ для обработки.
"""

import base64
import json
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(levelname)s | %(message)s')
logger = logging.getLogger(__name__)


def restore_json_files():
    """Восстановить JSON-wrapped файлы из карантина."""
    
    quarantine_dir = Path("quarantine")
    input_dir = Path("input")
    
    if not quarantine_dir.exists():
        logger.error("Директория quarantine/ не найдена")
        return 0
    
    # Находим все CORRUPTED_*.mp3 файлы
    corrupted_files = list(quarantine_dir.glob("CORRUPTED_*.mp3"))
    
    if not corrupted_files:
        logger.info("Нет файлов для восстановления в quarantine/")
        return 0
    
    logger.info(f"Найдено файлов в карантине: {len(corrupted_files)}")
    
    restored = 0
    failed = 0
    
    for file in corrupted_files:
        try:
            logger.info(f"\n🔧 Обработка: {file.name}")
            
            # Проверяем, это JSON?
            with open(file, 'rb') as f:
                header = f.read(100)
            
            if not header.strip().startswith(b'{'):
                logger.warning(f"  ⚠️ Не JSON файл, пропускаем")
                continue
            
            # Читаем JSON
            with open(file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Извлекаем base64
            if 'data' not in data:
                logger.error(f"  ❌ Нет поля 'data' в JSON")
                failed += 1
                continue
            
            b64_audio = data['data']
            
            # Декодируем
            audio_bytes = base64.b64decode(b64_audio)
            
            # Сохраняем как сырой MP3
            # Убираем префикс CORRUPTED_ из имени
            original_name = file.name.replace("CORRUPTED_", "")
            restored_file = input_dir / original_name
            
            with open(restored_file, 'wb') as f:
                f.write(audio_bytes)
            
            logger.info(f"  ✅ Восстановлено: {restored_file.name}")
            logger.info(f"     Размер: {len(audio_bytes)} bytes")
            
            # Удаляем файл из карантина
            file.unlink()
            logger.info(f"     Удалён из карантина: {file.name}")
            
            restored += 1
            
        except Exception as e:
            logger.error(f"  ❌ Ошибка: {e}")
            failed += 1
    
    # Итого
    logger.info(f"\n" + "="*60)
    logger.info(f"📊 ИТОГО:")
    logger.info(f"   Восстановлено: {restored}")
    logger.info(f"   Ошибок: {failed}")
    logger.info(f"="*60)
    
    return restored


if __name__ == "__main__":
    try:
        restored_count = restore_json_files()
        sys.exit(0 if restored_count > 0 else 1)
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)

