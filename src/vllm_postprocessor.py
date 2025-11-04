"""
VLLM-постобработка через LLM-30B.

Функции:
- Исправление ошибок ASR
- Контекстное маскирование PII (фамилии, телефоны)
- Классификация звонка
- Сохранение критичных данных (имя админа, адрес медцентра)
- Нормализация адресов и имён админов через branches.yaml
"""

import json
import logging
from typing import Optional, Tuple

from openai import OpenAI
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from src.config_validation import VLLMConfig
from src.branches_manager import BranchesManager

logger = logging.getLogger(__name__)


# Промпт для LLM-30B (будет дополнен данными из branches.yaml)
VLLM_SYSTEM_PROMPT_TEMPLATE = """Ты - эксперт по обработке транскрипций телефонных звонков.

ЗАДАЧИ:
1. Исправь типичные ошибки ASR (неправильно распознанные слова, повторы, артефакты распознавания)

2. МАСКИРУЙ только персональные данные клиента:
   - Фамилии и отчества клиентов → [ФИО]
   - Телефоны (любые последовательности цифр ≥7 символов) → [ТЕЛЕФОН]
   
3. НЕ МАСКИРУЙ (критично для анализа):
   - Имя сотрудника/оператора
   - Название компании/организации
   - Адрес офиса/филиала с номером дома
   - Профессиональные термины и специфичная лексика
   - Цифры: цены, параметры, характеристики (оставляй как есть)
   - Даты и время (оставляй как есть)

{branches_info}

4. ИСПРАВЬ ИМЕНА ОПЕРАТОРОВ к стандартным вариантам согласно branches.yaml:
   - Используй нормализацию из branches.yaml (admins section)
   - Пример: "Вариант1", "Вариант2" → "Каноническое имя"
   - ВАЖНО: Whisper может неправильно распознать имена, особенно похожие по звучанию
   - Если имя из нескольких слов - оставь ТОЛЬКО ПЕРВОЕ СЛОВО (имя оператора всегда одно слово)
   
5. Классифицируй звонок:
   - type: "запись_на_прием", "консультация", "отмена", "перенос", "жалоба", "вопрос_о_ценах"
   - sentiment: "положительный", "нейтральный", "негативный"
   - key_topics: [список тем, максимум 3]
   - operator_name: "имя оператора" (если упомянуто)
   - location_address: "адрес офиса/филиала" (если упомянут - нормализуй к стандартному варианту из branches.yaml)

ПРИМЕРЫ:

Входная транскрипция: "Здравствуйте, меня зовут Иванов Сергей Петрович, мой телефон 89501234567, мне 45 лет. Хочу записаться на услугу по адресу улица Примерная 25. Оператор Ольга мне говорила, что цена 3500 рублей."

Результат: "Здравствуйте, меня зовут [ФИО], мой телефон [ТЕЛЕФОН], мне 45 лет. Хочу записаться на услугу по адресу улица Примерная 25. Оператор Ольга мне говорила, что цена 3500 рублей."

---

Верни ТОЛЬКО валидный JSON в формате:
{{
  "cleaned_text": "исправленный и замаскированный текст",
  "classification": {{
    "type": "тип звонка",
    "sentiment": "тональность",
    "key_topics": ["тема1", "тема2"],
    "admin_name": "имя или null",
    "clinic_address": "адрес или null"
  }}
}}"""


class VLLMPostprocessor:
    """Постобработка транскрипций через VLLM (LLM-30B)."""

    def __init__(self, config: VLLMConfig, branches_yaml_path: str = "branches.yaml"):
        """
        Инициализация VLLM клиента.

        Args:
            config: VLLM конфигурация
            branches_yaml_path: Путь к branches.yaml
        """
        self.config = config

        if not config.enabled:
            logger.warning("VLLM постобработка отключена в конфиге")
            self.client = None
            self.system_prompt = None
            return

        # Загрузка branches.yaml
        try:
            self.branches_manager = BranchesManager(branches_yaml_path)
            branches_info = self.branches_manager.format_for_prompt()
            
            # Формирование финального промпта с данными о филиалах
            self.system_prompt = VLLM_SYSTEM_PROMPT_TEMPLATE.format(
                branches_info=branches_info
            )
            
            logger.info(
                f"✓ Загружено {len(self.branches_manager.addresses)} филиалов, "
                f"{len(self.branches_manager.admins)} админов"
            )
        except Exception as e:
            logger.warning(
                f"Не удалось загрузить branches.yaml: {e}. "
                "Используется промпт без информации о филиалах."
            )
            self.branches_manager = None
            self.system_prompt = VLLM_SYSTEM_PROMPT_TEMPLATE.format(
                branches_info="(информация о филиалах недоступна)"
            )

        try:
            self.client = OpenAI(
                base_url=config.base_url,
                api_key="EMPTY",  # VLLM не требует API ключ
                timeout=config.timeout,
            )
            logger.info(f"✓ VLLM клиент инициализирован: {config.base_url}")
        except Exception as e:
            logger.error(f"Ошибка инициализации VLLM клиента: {e}")
            raise RuntimeError(f"Не удалось подключиться к VLLM: {e}") from e

    @retry(
        retry=retry_if_exception_type((Exception,)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=10),
        reraise=True,
    )
    def _call_vllm(self, transcription: str) -> dict:
        """
        Вызов VLLM API с retry-логикой.

        Args:
            transcription: Сырая транскрипция

        Returns:
            dict: Результат от VLLM

        Raises:
            Exception: При ошибке API
        """
        if not self.client:
            raise RuntimeError("VLLM клиент не инициализирован")

        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {
                        "role": "user",
                        "content": f"Транскрипция для обработки:\n{transcription}",
                    },
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )

            result_text = response.choices[0].message.content.strip()
            logger.debug(f"VLLM ответ (первые 200 символов): {result_text[:200]}")

            return result_text

        except Exception as e:
            logger.warning(f"Ошибка вызова VLLM API (retry): {e}")
            raise

    def process(
        self, raw_transcription: str, filename: str = ""
    ) -> Tuple[str, Optional[dict]]:
        """
        Полная постобработка транскрипции.

        Args:
            raw_transcription: Сырая транскрипция от ASR
            filename: Имя файла (для логов)

        Returns:
            Tuple[str, dict]: (очищенный текст, классификация)
                             Если VLLM недоступен - возвращает исходный текст
        """
        if not self.config.enabled or not self.client:
            logger.warning(f"VLLM отключен, возврат исходной транскрипции: {filename}")
            return raw_transcription, None

        if not raw_transcription or len(raw_transcription.strip()) < 10:
            logger.warning(f"Слишком короткая транскрипция для VLLM: {filename}")
            return raw_transcription, None

        logger.info(f"VLLM постобработка: {filename}")

        try:
            # Вызов VLLM с retry
            vllm_response = self._call_vllm(raw_transcription)

            # Парсинг JSON
            result = self._parse_vllm_response(vllm_response, filename)

            if result:
                cleaned_text = result.get("cleaned_text", raw_transcription)
                classification = result.get("classification", {})

                logger.info(
                    f"✓ VLLM обработка завершена: {len(cleaned_text)} символов, "
                    f"тип={classification.get('type', 'unknown')}"
                )

                return cleaned_text, classification
            else:
                # Fallback: если парсинг не удался
                logger.warning(
                    f"Не удалось распарсить JSON от VLLM для {filename}, "
                    "используем исходную транскрипцию"
                )
                return raw_transcription, None

        except Exception as e:
            # Финальный fallback после всех retry
            logger.error(
                f"Критическая ошибка VLLM постобработки для {filename}: {e}",
                exc_info=True,
            )
            logger.warning("Используем исходную транскрипцию без обработки")
            return raw_transcription, None

    def _parse_vllm_response(self, response_text: str, filename: str = "") -> Optional[dict]:
        """
        Парсинг JSON ответа от VLLM.

        Args:
            response_text: Ответ от VLLM
            filename: Имя файла (для логирования)

        Returns:
            dict или None: Распарсенный JSON
        """
        try:
            # Попытка найти JSON в тексте (может быть обёрнут в markdown)
            if "```json" in response_text:
                # Извлечение JSON из markdown блока
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                # Просто code block
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            else:
                json_str = response_text.strip()

            # Парсинг JSON
            result = json.loads(json_str)

            # Валидация структуры
            if "cleaned_text" not in result or "classification" not in result:
                logger.error(f"VLLM ответ не содержит нужных полей для {filename}")
                logger.debug(f"Ответ VLLM (первые 300 символов): {response_text[:300]}")
                return None

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON от VLLM для {filename}: {e}")
            # Сохранение сырого ответа в debug лог для анализа
            logger.debug(f"Некорректный JSON (первые 500 символов): {response_text[:500]}")
            
            # Попытка починить JSON (убрать незакрытые строки)
            try:
                # Простое исправление: обрезаем до последней закрывающей фигурной скобки
                last_brace = response_text.rfind('}')
                if last_brace > 0:
                    fixed_json = response_text[:last_brace + 1]
                    result = json.loads(fixed_json)
                    
                    if "cleaned_text" in result and "classification" in result:
                        logger.info(f"✓ JSON исправлен автоматически для {filename}")
                        return result
            except Exception:
                pass
            
            return None

    def health_check(self) -> bool:
        """
        Проверка доступности VLLM API.

        Returns:
            bool: True если VLLM доступен
        """
        if not self.client:
            return False

        try:
            # Простой запрос для проверки
            response = self.client.models.list()
            logger.info(f"✓ VLLM доступен: {len(response.data)} моделей")
            return True
        except Exception as e:
            logger.error(f"VLLM недоступен: {e}")
            return False

