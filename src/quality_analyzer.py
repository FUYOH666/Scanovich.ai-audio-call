"""
Модуль анализа качества обслуживания через Commercial LLM Sonnet 4.5.

Функции:
- Определение типа оборудования (1.5T vs 3T)
- Парсинг скриптов обслуживания (30 критериев)
- Анализ звонков через OpenRouter API (Commercial LLM Sonnet 4.5)
- Расчёт итоговых оценок качества
"""

import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from openai import OpenAI
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from src.config_validation import QualityAnalysisConfig

logger = logging.getLogger(__name__)


class ScriptParser:
    """Парсер скриптов обслуживания из Markdown файлов."""

    def __init__(self, script_path: str):
        """
        Инициализация парсера.

        Args:
            script_path: Путь к .md файлу скрипта
        """
        self.script_path = Path(script_path)
        self.criteria = []

    def parse(self) -> List[Dict]:
        """
        Парсинг критериев из .md файла.

        Returns:
            List[Dict]: Список критериев с описанием
        """
        if not self.script_path.exists():
            raise FileNotFoundError(f"Скрипт не найден: {self.script_path}")

        with open(self.script_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Парсинг основных сущностей (1-20)
        main_section = re.search(
            r"### Основные сущности(.+?)(?=###|$)", content, re.DOTALL
        )
        if main_section:
            self._parse_criteria_section(main_section.group(1), block="main")

        # Парсинг дополнительных сущностей (21-30)
        additional_section = re.search(
            r"### Дополнительные расширенные сущности(.+?)(?=###|$)",
            content,
            re.DOTALL,
        )
        if additional_section:
            self._parse_criteria_section(
                additional_section.group(1), block="additional"
            )

        logger.info(f"Парсинг скрипта {self.script_path.name}: {len(self.criteria)} критериев")

        return self.criteria

    def _parse_criteria_section(self, section_text: str, block: str):
        """Парсинг секции критериев."""
        # Регулярное выражение для поиска критериев: "1. **Название** — описание"
        pattern = r"(\d+)\.\s+\*\*(.+?)\*\*\s+[—-]\s+(.+?)(?=\n\d+\.|$)"

        for match in re.finditer(pattern, section_text, re.DOTALL):
            criterion_id = int(match.group(1))
            name = match.group(2).strip()
            description = match.group(3).strip().replace("\n", " ")

            self.criteria.append(
                {
                    "id": criterion_id,
                    "name": name,
                    "description": description,
                    "block": block,
                }
            )


class EquipmentDetector:
    """Определение типа оборудования (1.5T vs 3T) из транскрипции."""

    KEYWORDS_TEMPLATE_B = [
        r"\b3\s*тесл",
        r"три\s*тесл",
        r"3т\b",
        r"высокопольн",
        r"самый\s+точн",
        r"новейш.{0,10}аппарат",
    ]

    KEYWORDS_1_5T = [
        r"1[.,]5\s*тесл",
        r"полтора\s*тесл",
        r"1,5т\b",
    ]

    @classmethod
    def detect(cls, transcription: str, classification: Optional[Dict] = None) -> str:
        """
        Определить тип оборудования из транскрипции.

        Args:
            transcription: Текст транскрипции
            classification: Классификация от VLLM (опционально)

        Returns:
            str: "template_a" или "template_b" (определяется по ключевым словам)
        """
        text_lower = transcription.lower()

        # Проверка на Template B (по ключевым словам)
        for pattern in cls.KEYWORDS_TEMPLATE_B:
            if re.search(pattern, text_lower):
                logger.info("Обнаружен тип услуги: Template B")
                return "template_b"

        # Проверка на Template A (по ключевым словам)
        for pattern in cls.KEYWORDS_1_5T:
            if re.search(pattern, text_lower):
                logger.info("Обнаружен тип услуги: Template A")
                return "template_a"

        # По умолчанию Template A (базовый шаблон)
        logger.info("Тип услуги не определён, используем Template A по умолчанию")
        return "template_a"


class CommercialLLMAnalyzer:
    """Интеграция с Commercial LLM Sonnet 4.5 через OpenRouter."""

    def __init__(self, config: QualityAnalysisConfig):
        """
        Инициализация Commercial LLM анализатора.

        Args:
            config: Конфигурация анализа качества
        """
        self.config = config

        # Получение API ключа из ENV
        api_key = os.getenv(config.api_key_env)
        if not api_key:
            raise ValueError(
                f"API ключ не найден в ENV: {config.api_key_env}. "
                "Установите переменную окружения OPENROUTER_API_KEY"
            )

        try:
            self.client = OpenAI(
                base_url=config.base_url,
                api_key=api_key,
                timeout=config.timeout,
            )
            logger.info(f"✓ Commercial LLM Sonnet 4.5 клиент инициализирован: {config.base_url}")
        except Exception as e:
            logger.error(f"Ошибка инициализации OpenRouter клиента: {e}")
            raise RuntimeError(f"Не удалось подключиться к OpenRouter: {e}") from e

    def build_system_prompt(self, script_criteria: List[Dict], equipment_type: str) -> str:
        """
        Построить system prompt для Commercial LLM.

        Args:
            script_criteria: Список критериев из скрипта
            equipment_type: Тип оборудования (1.5T или 3T)

        Returns:
            str: System prompt
        """
        criteria_text = "\n\n".join(
            [
                f"{c['id']}. **{c['name']}** — {c['description']}"
                for c in script_criteria
            ]
        )

        system_prompt = f"""Ты - эксперт по оценке качества обслуживания в организациях.

КОНТЕКСТ:
- Организация с несколькими филиалами
- Операторы принимают звонки от клиентов
- Есть утверждённые корпоративные скрипты обслуживания

ЗАДАЧА:
Объективно оценить качество работы оператора по 30 критериям из скрипта {equipment_type}.

КРИТЕРИИ ОЦЕНКИ (скрипт {equipment_type}):

{criteria_text}

ФОРМАТ ОЦЕНКИ:
Для каждого критерия:
- score: 0 (не выполнено), 0.5 (частично), 1 (выполнено полностью)
- comment: краткое объяснение оценки (1-2 предложения)
- relevant: true (критерий применим к данному звонку) / false (неприменим)

ВАЖНЫЕ ПРИНЦИПЫ:
- Будь объективным, не завышай и не занижай оценки
- Если критерий неприменим (например, клиент сам отказался от допуслуги) - ставь relevant: false, score: null
- Фокусируйся на действиях АДМИНИСТРАТОРА, а не клиента
- Учитывай контекст разговора (срочность, эмоциональное состояние клиента)
- В "strengths" и "weaknesses" - только конкретные наблюдаемые факты
- В "recommendations" - только действенные, применимые на практике советы

СТРУКТУРА ОТВЕТА:
Верни СТРОГО ВАЛИДНЫЙ JSON в следующем формате:
{{
  "equipment_detected": "{equipment_type}",
  "criteria_evaluations": [
    {{
      "id": 1,
      "name": "Название критерия",
      "score": 0.0-1.0 или null,
      "comment": "Краткое объяснение",
      "relevant": true/false
    }},
    ...
  ],
  "overall_score": 0-100,
  "strengths": ["Сильная сторона 1", "Сильная сторона 2", ...],
  "weaknesses": ["Слабая сторона 1", "Слабая сторона 2", ...],
  "recommendations": ["Рекомендация 1", "Рекомендация 2", ...],
  "reasoning": "Детальное объяснение итоговой оценки с примерами из звонка..."
}}"""

        return system_prompt

    def build_user_prompt(
        self, transcription: str, metadata: Optional[Dict] = None
    ) -> str:
        """
        Построить user prompt для Commercial LLM.

        Args:
            transcription: Текст транскрипции
            metadata: Метаданные звонка

        Returns:
            str: User prompt
        """
        metadata_text = ""
        if metadata and "classification" in metadata:
            classification = metadata["classification"]
            metadata_text = f"""МЕТАДАННЫЕ ЗВОНКА:
- Имя оператора: {classification.get('admin_name', 'Не указано')}
- Адрес клиники: {classification.get('clinic_address', 'Не указано')}
- Тип звонка: {classification.get('type', 'Не определён')}
- Тональность: {classification.get('sentiment', 'Не определена')}
- Ключевые темы: {', '.join(classification.get('key_topics', []))}

"""

        user_prompt = f"""{metadata_text}ТРАНСКРИПЦИЯ ЗВОНКА:

{transcription}

---

Проанализируй этот звонок по всем 30 критериям скрипта.
Верни детальную оценку в JSON формате согласно инструкции."""

        return user_prompt

    @retry(
        retry=retry_if_exception_type((Exception,)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=10),
        reraise=True,
    )
    def _call_claude(self, system_prompt: str, user_prompt: str) -> Tuple[str, Dict]:
        """
        Вызов Commercial LLM Sonnet 4.5 API с retry-логикой.

        Args:
            system_prompt: System prompt
            user_prompt: User prompt

        Returns:
            Tuple[str, Dict]: (ответ, статистика токенов)
        """
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )

            result_text = response.choices[0].message.content.strip()

            # Статистика токенов
            tokens_used = {
                "prompt": response.usage.prompt_tokens,
                "completion": response.usage.completion_tokens,
                "total": response.usage.total_tokens,
            }

            # Расчёт стоимости (Commercial LLM Sonnet 4.5: $3/$15 за 1M токенов)
            cost_usd = (
                tokens_used["prompt"] * 0.000003
                + tokens_used["completion"] * 0.000015
            )

            logger.info(
                f"Commercial LLM ответ получен: {tokens_used['total']} токенов, ${cost_usd:.4f}"
            )

            return result_text, {"tokens_used": tokens_used, "cost_usd": cost_usd}

        except Exception as e:
            logger.warning(f"Ошибка вызова Commercial LLM API (retry): {e}")
            raise

    def analyze(
        self,
        transcription: str,
        script_criteria: List[Dict],
        equipment_type: str,
        metadata: Optional[Dict] = None,
    ) -> Dict:
        """
        Полный анализ звонка через Commercial LLM.

        Args:
            transcription: Текст транскрипции
            script_criteria: Критерии из скрипта
            equipment_type: Тип оборудования
            metadata: Метаданные звонка

        Returns:
            Dict: Результат анализа
        """
        # Построение промптов
        system_prompt = self.build_system_prompt(script_criteria, equipment_type)
        user_prompt = self.build_user_prompt(transcription, metadata)

        # Вызов Commercial LLM
        response_text, api_stats = self._call_claude(system_prompt, user_prompt)

        # Парсинг JSON
        evaluation = self._parse_response(response_text)

        if evaluation:
            evaluation.update(api_stats)
            return evaluation
        else:
            raise ValueError("Не удалось распарсить ответ от Commercial LLM")

    def _parse_response(self, response_text: str) -> Optional[Dict]:
        """
        Парсинг JSON ответа от Commercial LLM.

        Args:
            response_text: Ответ от Commercial LLM

        Returns:
            Dict или None: Распарсенный JSON
        """
        try:
            # Извлечение JSON (может быть обёрнут в markdown)
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            else:
                json_str = response_text.strip()

            # Парсинг JSON
            result = json.loads(json_str)

            # Валидация структуры
            required_fields = [
                "criteria_evaluations",
                "overall_score",
                "strengths",
                "weaknesses",
                "recommendations",
            ]
            for field in required_fields:
                if field not in result:
                    logger.error(f"Commercial LLM ответ не содержит поле: {field}")
                    return None

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON от Commercial LLM: {e}")
            logger.debug(f"Некорректный JSON: {response_text[:500]}")
            return None


class QualityAnalyzer:
    """Главный класс анализа качества обслуживания."""

    def __init__(self, config: QualityAnalysisConfig, vllm_config=None):
        """
        Инициализация анализатора качества.

        Args:
            config: Конфигурация анализа качества
            vllm_config: Конфигурация VLLM (для локального анализатора)
        """
        self.config = config
        
        # Выбор анализатора в зависимости от provider
        if config.provider == "vllm":
            # Используем локальный VLLM (LLM-30B)
            from src.model_comparison import LLMAnalyzer
            
            # Создаём временный конфиг для LLM
            if vllm_config is None:
                from src.config_validation import VLLMConfig
                vllm_config = VLLMConfig(
                    base_url=config.base_url,
                    model=config.model,
                    timeout=config.timeout
                )
            self.analyzer = LLMAnalyzer(vllm_config)
            logger.info("✓ Используется локальный VLLM (LLM-30B) для анализа качества")
        else:
            # Используем OpenRouter (Commercial LLM)
            self.analyzer = CommercialLLMAnalyzer(config)
            logger.info("✓ Используется OpenRouter (Commercial LLM Sonnet 4.5) для анализа качества")

        # Парсинг скриптов
        self.scripts = {}
        for equipment_type, script_filename in config.scripts.items():
            script_path = Path(script_filename)
            if script_path.exists():
                parser = ScriptParser(str(script_path))
                self.scripts[equipment_type] = parser.parse()
                logger.info(
                    f"✓ Скрипт загружен: {equipment_type} ({len(self.scripts[equipment_type])} критериев)"
                )
            else:
                logger.warning(f"Скрипт не найден: {script_filename}")

        if not self.scripts:
            raise FileNotFoundError("Не загружено ни одного скрипта!")

        logger.info("✓ QualityAnalyzer инициализирован")

    def analyze_call(
        self, transcription_path: str, metadata_path: Optional[str] = None
    ) -> Dict:
        """
        Анализ одного звонка.

        Args:
            transcription_path: Путь к файлу транскрипции
            metadata_path: Путь к файлу метаданных (опционально)

        Returns:
            Dict: Результат анализа качества
        """
        # Загрузка транскрипции
        transcription_path_obj = Path(transcription_path)
        if not transcription_path_obj.exists():
            raise FileNotFoundError(f"Транскрипция не найдена: {transcription_path}")

        with open(transcription_path_obj, "r", encoding="utf-8") as f:
            transcription = f.read()

        # Загрузка метаданных
        metadata = None
        if metadata_path:
            metadata_path_obj = Path(metadata_path)
            if metadata_path_obj.exists():
                with open(metadata_path_obj, "r", encoding="utf-8") as f:
                    metadata = json.load(f)

        logger.info(f"Анализ качества: {transcription_path_obj.name}")

        # 1. Определение типа оборудования
        classification = metadata.get("classification") if metadata else None
        equipment_type = EquipmentDetector.detect(transcription, classification)

        # 2. Выбор соответствующего скрипта
        script_key = "script_3t" if equipment_type == "3T" else "script_1_5t"
        if script_key not in self.scripts:
            raise ValueError(f"Скрипт {script_key} не загружен!")

        script_criteria = self.scripts[script_key]

        # 3. Анализ через выбранную модель (VLLM или Commercial LLM)
        if self.config.provider == "vllm":
            # Построение промптов
            system_prompt = self._build_system_prompt(script_criteria, equipment_type)
            user_prompt = self._build_user_prompt(transcription, metadata)
            
            # Анализ через LLM
            response_text, metrics = self.analyzer.analyze(system_prompt, user_prompt)
            evaluation = self._parse_response(response_text)
            if evaluation:
                evaluation.update(metrics)
            else:
                raise ValueError("Не удалось распарсить ответ от LLM")
        else:
            # Анализ через Commercial LLM
            evaluation = self.analyzer.analyze(
                transcription, script_criteria, equipment_type, metadata
            )

        # 4. Добавление метаинформации
        result = {
            "call_id": transcription_path_obj.stem,
            "equipment_type": equipment_type,
            "processed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "admin_name": classification.get("admin_name") if classification else None,
            "clinic_address": (
                classification.get("clinic_address") if classification else None
            ),
            **evaluation,
        }

        cost_str = f"${result['cost_usd']:.4f}" if result.get('cost_usd', 0) > 0 else "бесплатно (локально)"
        logger.info(
            f"✓ Анализ завершён: балл={result['overall_score']:.1f}/100, "
            f"стоимость={cost_str}"
        )

        return result
    
    def _build_system_prompt(self, script_criteria, equipment_type):
        """Построить system prompt (используется для VLLM)."""
        # Используем метод из CommercialLLMAnalyzer
        from src.model_comparison import LLMAnalyzer
        
        criteria_text = "\n\n".join(
            [
                f"{c['id']}. **{c['name']}** — {c['description']}"
                for c in script_criteria
            ]
        )

        return f"""Ты - эксперт по оценке качества обслуживания в организациях.

КОНТЕКСТ:
- Организация с несколькими филиалами
- Операторы принимают звонки от клиентов
- Есть утверждённые корпоративные скрипты обслуживания

ЗАДАЧА:
Объективно оценить качество работы оператора по 30 критериям из скрипта {equipment_type}.

КРИТЕРИИ ОЦЕНКИ (скрипт {equipment_type}):

{criteria_text}

ФОРМАТ ОЦЕНКИ:
Для каждого критерия:
- score: 0 (не выполнено), 0.5 (частично), 1 (выполнено полностью)
- comment: краткое объяснение оценки (1-2 предложения)
- relevant: true (критерий применим) / false (неприменим)

ВАЖНО:
- Будь объективным, не завышай и не занижай оценки
- Если критерий неприменим - ставь relevant: false, score: null
- Фокусируйся на действиях АДМИНИСТРАТОРА
- В "strengths" и "weaknesses" - только конкретные факты

СТРУКТУРА ОТВЕТА (СТРОГО ВАЛИДНЫЙ JSON):
{{
  "equipment_detected": "{equipment_type}",
  "criteria_evaluations": [
    {{"id": 1, "name": "...", "score": 0-1 или null, "comment": "...", "relevant": true/false}},
    ...
  ],
  "overall_score": 0-100,
  "strengths": ["..."],
  "weaknesses": ["..."],
  "recommendations": ["..."],
  "reasoning": "Детальное объяснение..."
}}"""
    
    def _build_user_prompt(self, transcription, metadata):
        """Построить user prompt (используется для VLLM)."""
        metadata_text = ""
        if metadata and "classification" in metadata:
            classification = metadata["classification"]
            metadata_text = f"""МЕТАДАННЫЕ ЗВОНКА:
- Имя оператора: {classification.get('admin_name', 'Не указано')}
- Адрес клиники: {classification.get('clinic_address', 'Не указано')}
- Тип звонка: {classification.get('type', 'Не определён')}
- Тональность: {classification.get('sentiment', 'Не определена')}
- Ключевые темы: {', '.join(classification.get('key_topics', []))}

"""

        return f"""{metadata_text}ТРАНСКРИПЦИЯ ЗВОНКА:

{transcription}

---

Проанализируй этот звонок по всем 30 критериям скрипта.
Верни детальную оценку в JSON формате согласно инструкции."""
    
    def _parse_response(self, response_text):
        """Парсинг JSON ответа."""
        try:
            # Извлечение JSON
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_str = response_text[json_start:json_end].strip()
            else:
                json_str = response_text.strip()

            result = json.loads(json_str)

            required_fields = [
                "criteria_evaluations",
                "overall_score",
                "strengths",
                "weaknesses",
                "recommendations",
            ]
            for field in required_fields:
                if field not in result:
                    logger.error(f"Ответ не содержит поле: {field}")
                    return None

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Ошибка парсинга JSON: {e}")
            logger.debug(f"Некорректный JSON: {response_text[:500]}")
            return None

    def save_analysis(self, analysis: Dict, filename: str) -> str:
        """
        Сохранить результат анализа в JSON.

        Args:
            analysis: Результат анализа
            filename: Имя файла (без расширения)

        Returns:
            str: Путь к сохранённому файлу
        """
        output_path = (
            Path(self.config.paths["individual"]) / f"{filename}.json"
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)

        logger.info(f"Анализ качества сохранён: {output_path.name}")
        return str(output_path)

