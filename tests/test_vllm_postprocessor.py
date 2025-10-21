"""
Тесты VLLM постпроцессора (без реального VLLM, моки).
"""

import json

import pytest

from src.config_validation import VLLMConfig
from src.vllm_postprocessor import VLLMPostprocessor


def test_parse_valid_json_response():
    """Тест парсинга валидного JSON ответа от VLLM."""
    vllm_config = VLLMConfig(enabled=False)  # Отключаем для теста
    processor = VLLMPostprocessor(vllm_config)

    # Симуляция ответа от VLLM
    vllm_response = json.dumps(
        {
            "cleaned_text": "Здравствуйте, меня зовут [ФИО], телефон [ТЕЛЕФОН]",
            "classification": {
                "type": "запись_на_прием",
                "sentiment": "положительный",
                "key_topics": ["МРТ", "запись"],
                "admin_name": "Алёна",
                "clinic_address": "улица Ленина 25",
            },
        }
    )

    result = processor._parse_vllm_response(vllm_response)

    assert result is not None
    assert "cleaned_text" in result
    assert "classification" in result
    assert result["classification"]["admin_name"] == "Алёна"


def test_parse_json_in_markdown():
    """Тест парсинга JSON обёрнутого в markdown."""
    vllm_config = VLLMConfig(enabled=False)
    processor = VLLMPostprocessor(vllm_config)

    # VLLM иногда возвращает JSON в markdown блоке
    vllm_response = '''```json
{
  "cleaned_text": "Тестовый текст",
  "classification": {
    "type": "консультация",
    "sentiment": "нейтральный",
    "key_topics": [],
    "admin_name": null,
    "clinic_address": null
  }
}
```'''

    result = processor._parse_vllm_response(vllm_response)

    assert result is not None
    assert result["cleaned_text"] == "Тестовый текст"
    assert result["classification"]["type"] == "консультация"


def test_parse_invalid_json():
    """Тест обработки некорректного JSON."""
    vllm_config = VLLMConfig(enabled=False)
    processor = VLLMPostprocessor(vllm_config)

    vllm_response = "This is not valid JSON"

    result = processor._parse_vllm_response(vllm_response)

    assert result is None  # Должен вернуть None при ошибке парсинга


def test_parse_incomplete_json():
    """Тест обработки неполного JSON (без нужных полей)."""
    vllm_config = VLLMConfig(enabled=False)
    processor = VLLMPostprocessor(vllm_config)

    # JSON без поля "classification"
    vllm_response = json.dumps({"cleaned_text": "Только текст"})

    result = processor._parse_vllm_response(vllm_response)

    assert result is None  # Должен вернуть None если нет нужных полей


def test_process_with_disabled_vllm():
    """Тест обработки при отключенном VLLM."""
    vllm_config = VLLMConfig(enabled=False)
    processor = VLLMPostprocessor(vllm_config)

    raw_text = "Исходная транскрипция"

    cleaned_text, classification = processor.process(raw_text, "test.mp3")

    # Должен вернуть исходный текст без изменений
    assert cleaned_text == raw_text
    assert classification is None


def test_process_empty_transcription():
    """Тест обработки пустой транскрипции."""
    vllm_config = VLLMConfig(enabled=False)
    processor = VLLMPostprocessor(vllm_config)

    raw_text = ""

    cleaned_text, classification = processor.process(raw_text, "test.mp3")

    # Должен вернуть исходный текст (пустой)
    assert cleaned_text == ""
    assert classification is None

