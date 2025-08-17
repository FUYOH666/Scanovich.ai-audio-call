#!/usr/bin/env python3
"""
Конфигурация для полностью автономной работы pipeline
Медицинский центр МРТ Лидер - без интернет соединений

Автор: Scanovich
"""

import os
from pathlib import Path

# Получаем путь к проекту
PROJECT_ROOT = Path(__file__).parent.absolute()

def setup_offline_environment():
    """Настройка окружения для автономной работы"""
    
    # Устанавливаем локальный кэш HuggingFace
    local_cache = PROJECT_ROOT / "models" / "hub"
    os.environ["HUGGINGFACE_HUB_CACHE"] = str(local_cache)
    os.environ["HF_HOME"] = str(PROJECT_ROOT / "models")
    
    # КРИТИЧНО: Отключаем все интернет запросы
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["HUGGINGFACE_HUB_OFFLINE"] = "1"
    
    # Отключаем телеметрию
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "0"  # Прогресс-бары оставляем
    
    # Удаляем токен из окружения если есть
    if "HF_TOKEN" in os.environ:
        del os.environ["HF_TOKEN"]
    if "HUGGINGFACE_HUB_TOKEN" in os.environ:
        del os.environ["HUGGINGFACE_HUB_TOKEN"]
    
    print("🔒 НАСТРОЕНА АВТОНОМНАЯ РАБОТА:")
    print(f"   📁 Локальный кэш: {local_cache}")
    print(f"   🚫 Интернет запросы: ОТКЛЮЧЕНЫ")
    print(f"   🔑 Токены: УДАЛЕНЫ")
    print(f"   🏥 Режим: МЕДИЦИНСКИЙ (полная конфиденциальность)")

def get_local_model_path(model_name: str) -> str:
    """Получить путь к локальной модели"""
    model_map = {
        "large-v3": "models--openai--whisper-large-v3",
        "faster-whisper-large-v3": "models--Systran--faster-whisper-large-v3"
    }
    
    local_model = model_map.get(model_name, model_name)
    return str(PROJECT_ROOT / "models" / "hub" / local_model)

def verify_offline_setup():
    """Проверка готовности к автономной работе"""
    required_models = [
        "models--openai--whisper-large-v3",
        "models--Systran--faster-whisper-large-v3"
    ]
    
    missing_models = []
    for model in required_models:
        model_path = PROJECT_ROOT / "models" / "hub" / model
        if not model_path.exists():
            missing_models.append(model)
    
    if missing_models:
        print(f"❌ ОТСУТСТВУЮТ МОДЕЛИ: {missing_models}")
        return False
    
    print("✅ ВСЕ МОДЕЛИ ДОСТУПНЫ ЛОКАЛЬНО")
    return True

# Конфигурация для медицинского центра
MEDICAL_CONFIG = {
    "ensure_privacy": True,
    "disable_telemetry": True, 
    "offline_only": True,
    "local_processing": True,
    "no_external_apis": True,
    "hipaa_compliant": True  # Соответствие медицинским стандартам
}

if __name__ == "__main__":
    setup_offline_environment()
    verify_offline_setup() 