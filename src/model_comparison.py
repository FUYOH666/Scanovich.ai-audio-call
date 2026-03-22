"""
Модуль A/B тестирования моделей для анализа качества.

Сравнивает:
- локальный LLM (VLLM / OpenAI-compatible) — без API-стоимости
- облачный LLM (часто OpenRouter) — по тарифам провайдера
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, Optional, Tuple

from openai import OpenAI

from src.config_validation import QualityAnalysisConfig, VLLMConfig
from src.quality_analyzer import EquipmentDetector, OpenRouterAnalyzer, ScriptParser

logger = logging.getLogger(__name__)


class LLMAnalyzer:
    """Анализатор качества через локальный LLM-30B (VLLM)."""

    def __init__(self, vllm_config: VLLMConfig):
        """
        Инициализация LLM анализатора.

        Args:
            vllm_config: Конфигурация VLLM
        """
        self.config = vllm_config

        try:
            self.client = OpenAI(
                base_url=vllm_config.base_url,
                api_key="EMPTY",
                timeout=vllm_config.timeout,
            )
            logger.info(f"✓ LLM-30B клиент инициализирован: {vllm_config.base_url}")
        except Exception as e:
            logger.error(f"Ошибка инициализации LLM клиента: {e}")
            raise RuntimeError(f"Не удалось подключиться к VLLM: {e}") from e

    def analyze(
        self,
        system_prompt: str,
        user_prompt: str,
    ) -> Tuple[str, Dict]:
        """
        Анализ через LLM-30B.

        Args:
            system_prompt: System prompt
            user_prompt: User prompt

        Returns:
            Tuple[str, Dict]: (ответ, метрики)
        """
        start_time = time.time()

        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,  # Немного температуры для LLM
                max_tokens=self.config.max_tokens,
            )

            result_text = response.choices[0].message.content.strip()
            elapsed = time.time() - start_time

            # Метрики (для VLLM токены не возвращаются в стандартном формате)
            metrics = {
                "response_time": round(elapsed, 2),
                "cost_usd": 0.0,  # Локальный VLLM - бесплатно
                "model": "LLM-30B (Local VLLM)",
            }

            logger.info(f"LLM ответ получен за {elapsed:.2f}s (бесплатно)")

            return result_text, metrics

        except Exception as e:
            logger.error(f"Ошибка вызова LLM API: {e}")
            raise


class ModelComparator:
    """Сравнение моделей для анализа качества."""

    def __init__(
        self, quality_config: QualityAnalysisConfig, vllm_config: VLLMConfig
    ):
        """
        Инициализация компаратора.

        Args:
            quality_config: Конфигурация анализа качества
            vllm_config: Конфигурация VLLM
        """
        self.openrouter_analyzer = OpenRouterAnalyzer(quality_config)
        self.local_llm_analyzer = LLMAnalyzer(vllm_config)

        # Загрузка скриптов
        self.scripts = {}
        for equipment_type, script_filename in quality_config.scripts.items():
            script_path = Path(script_filename)
            if script_path.exists():
                parser = ScriptParser(str(script_path))
                self.scripts[equipment_type] = parser.parse()

        logger.info("✓ ModelComparator инициализирован")

    def compare(
        self, transcription: str, metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Сравнительный анализ одного звонка через обе модели.

        Args:
            transcription: Текст транскрипции
            metadata: Метаданные звонка

        Returns:
            Dict: Результаты сравнения
        """
        logger.info("🔬 Запуск сравнительного A/B теста моделей...")

        # Определение типа оборудования
        classification = metadata.get("classification") if metadata else None
        equipment_type = EquipmentDetector.detect(transcription, classification)

        # Выбор скрипта
        script_key = "script_3t" if equipment_type == "3T" else "script_1_5t"
        script_criteria = self.scripts[script_key]

        # Построение промптов (одинаковые для обеих моделей)
        system_prompt = self.openrouter_analyzer.build_system_prompt(
            script_criteria, equipment_type
        )
        user_prompt = self.openrouter_analyzer.build_user_prompt(transcription, metadata)

        # Тест 1: облачный LLM (OpenRouter / …)
        logger.info("Тест 1/2: облачный LLM (OpenRouter-compatible)...")
        try:
            claude_response, claude_stats = self.openrouter_analyzer._call_claude(
                system_prompt, user_prompt
            )
            claude_result = self.openrouter_analyzer._parse_response(claude_response)
            if claude_result:
                claude_result.update(claude_stats)
        except Exception as e:
            logger.error(f"Ошибка облачного LLM анализа: {e}")
            claude_result = {"error": str(e)}

        # Тест 2: локальный VLLM
        logger.info("Тест 2/2: локальный LLM (VLLM)...")
        try:
            qwen_response, qwen_metrics = self.local_llm_analyzer.analyze(
                system_prompt, user_prompt
            )
            qwen_result = self.openrouter_analyzer._parse_response(qwen_response)
            if qwen_result:
                qwen_result.update(qwen_metrics)
            else:
                # Если JSON не распарсился, сохраняем сырой ответ
                qwen_result = {
                    "error": "Failed to parse JSON",
                    "raw_response": qwen_response[:500],
                    **qwen_metrics,
                }
        except Exception as e:
            logger.error(f"Ошибка LLM анализа: {e}")
            qwen_result = {"error": str(e)}

        # Сравнение результатов
        comparison = {
            "equipment_type": equipment_type,
            "transcription_length": len(transcription),
            "claude_sonnet_4_5": claude_result,
            "qwen3_30b": qwen_result,
            "comparison_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        }

        logger.info("✓ Сравнительный тест завершён")

        return comparison

    def print_comparison(self, comparison: Dict):
        """
        Вывод результатов сравнения в консоль.

        Args:
            comparison: Результаты от compare()
        """
        print("\n" + "=" * 80)
        print("🔬 A/B ТЕСТ: облачный LLM (OpenRouter-compatible) vs локальный VLLM")
        print("=" * 80)

        print(f"\n📋 Параметры теста:")
        print(f"  Оборудование: {comparison['equipment_type']}")
        print(f"  Длина транскрипции: {comparison['transcription_length']} символов")

        # Облачный LLM
        claude = comparison["claude_sonnet_4_5"]
        print(f"\n{'=' * 80}")
        print("🌟 МОДЕЛЬ A: облачный LLM (OpenRouter / OpenAI-compatible)")
        print("=" * 80)

        if "error" in claude:
            print(f"  ❌ Ошибка: {claude['error']}")
        else:
            print(f"  Итоговый балл: {claude.get('overall_score', 'N/A')}/100")
            print(f"  Токенов: {claude.get('tokens_used', {}).get('total', 'N/A')}")
            print(f"  Стоимость: ${claude.get('cost_usd', 'N/A')}")
            print(f"\n  ✅ Сильные стороны:")
            for s in claude.get("strengths", [])[:3]:
                print(f"    • {s}")
            print(f"\n  ⚠️ Слабые стороны:")
            for w in claude.get("weaknesses", [])[:3]:
                print(f"    • {w}")

        # LLM результаты
        qwen = comparison["qwen3_30b"]
        print(f"\n{'=' * 80}")
        print("🤖 МОДЕЛЬ B: LLM-30B (Local VLLM)")
        print("=" * 80)

        if "error" in qwen:
            print(f"  ❌ Ошибка: {qwen['error']}")
            if "raw_response" in qwen:
                print(f"  Сырой ответ (первые 300 символов):")
                print(f"  {qwen['raw_response'][:300]}...")
        else:
            print(f"  Итоговый балл: {qwen.get('overall_score', 'N/A')}/100")
            print(f"  Время ответа: {qwen.get('response_time', 'N/A')}s")
            print(f"  Стоимость: $0.00 (локально)")
            print(f"\n  ✅ Сильные стороны:")
            for s in qwen.get("strengths", [])[:3]:
                print(f"    • {s}")
            print(f"\n  ⚠️ Слабые стороны:")
            for w in qwen.get("weaknesses", [])[:3]:
                print(f"    • {w}")

        # Сравнительная таблица
        print(f"\n{'=' * 80}")
        print("📊 СРАВНИТЕЛЬНАЯ ТАБЛИЦА")
        print("=" * 80)

        print(f"\n| Критерий | Облачный LLM | Локальный VLLM |")
        print(f"|----------|-------------------|-----------|")

        claude_score = claude.get("overall_score", "ERROR")
        qwen_score = qwen.get("overall_score", "ERROR")
        print(f"| Итоговый балл | {claude_score} | {qwen_score} |")

        claude_cost = f"${claude.get('cost_usd', 0):.4f}"
        qwen_cost = "$0.00"
        print(f"| Стоимость | {claude_cost} | {qwen_cost} |")

        claude_time = "~60s"
        qwen_time = f"{qwen.get('response_time', 'N/A')}s"
        print(f"| Время ответа | {claude_time} | {qwen_time} |")

        claude_criteria = len(claude.get("criteria_evaluations", []))
        qwen_criteria = len(qwen.get("criteria_evaluations", []))
        print(f"| Критериев оценено | {claude_criteria}/30 | {qwen_criteria}/30 |")

        # Рекомендация
        print(f"\n{'=' * 80}")
        print("💡 РЕКОМЕНДАЦИЯ")
        print("=" * 80)

        if "error" in qwen:
            print(f"\n❌ LLM-30B не справился с задачей")
            print(f"\n✅ Рекомендация: Использовать облачный LLM")
            print(f"   Причина: Локальная модель не может обработать сложный промпт")
        elif claude_score == qwen_score:
            print(f"\n✅ Обе модели показали одинаковый результат!")
            print(f"\n💰 Рекомендация: Использовать LLM-30B (локально)")
            print(f"   Экономия: ${claude.get('cost_usd', 0):.4f} на звонок")
        elif isinstance(claude_score, (int, float)) and isinstance(qwen_score, (int, float)):
            diff = abs(claude_score - qwen_score)
            if diff <= 5:
                print(f"\n✅ Модели показали схожие результаты (разница {diff:.1f} баллов)")
                print(f"\n💰 Рекомендация: Использовать LLM-30B (локально)")
                print(f"   Экономия: ${claude.get('cost_usd', 0):.4f} на звонок")
                print(f"   Качество: Достаточное для задачи")
            else:
                print(f"\n⚠️ Существенная разница в оценках: {diff:.1f} баллов")
                print(f"\n✅ Рекомендация: Использовать облачный LLM")
                print(f"   Причина: Более точный и объективный анализ")
                print(f"   Стоимость: ${claude.get('cost_usd', 0):.4f}/звонок - приемлемо для качества")
        else:
            print(f"\n⚠️ Невозможно сравнить результаты")
            print(f"\n✅ Рекомендация: Использовать облачный LLM")
            print(f"   Причина: Гарантированная стабильность и качество")

        print("\n" + "=" * 80 + "\n")

