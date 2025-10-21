"""
Извлечение ошибок из анализа качества.

Фильтрует только failed/unknown критерии, извлекает цитаты,
сохраняет в SQLite.
"""

import logging
import re
from datetime import datetime
from typing import Dict, List

from src.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class ErrorExtractor:
    """Извлечение ошибок из результатов анализа качества."""

    # Критерии 1-20 = обязательные (required)
    # Критерии 21-30 = желательные (optional)
    REQUIRED_CRITERIA = list(range(1, 21))
    OPTIONAL_CRITERIA = list(range(21, 31))

    def __init__(self, db_path: str):
        """
        Инициализация экстрактора ошибок.

        Args:
            db_path: Путь к SQLite БД
        """
        self.db_manager = DatabaseManager(db_path)
        logger.info("✓ ErrorExtractor инициализирован")

    def extract_errors(
        self, quality_analysis: Dict, transcription_text: str = ""
    ) -> List[Dict]:
        """
        Извлечь ошибки из результата анализа качества.

        Args:
            quality_analysis: Результат от QualityAnalyzer
            transcription_text: Текст транскрипции (для цитат)

        Returns:
            List[Dict]: Список событий ошибок
        """
        events = []

        # Проверка наличия оценок критериев
        if "criteria_evaluations" not in quality_analysis:
            logger.warning("Нет criteria_evaluations в анализе")
            return events

        call_id = quality_analysis.get("call_id", "unknown")
        timestamp = quality_analysis.get("processed_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        # Имя администратора (уже нормализовано VLLM на этапе постобработки)
        admin_name = quality_analysis.get("admin_name")
        
        branch_address = quality_analysis.get("clinic_address")
        equipment_type = quality_analysis.get("equipment_type")

        # Обработка каждого критерия
        for criterion in quality_analysis["criteria_evaluations"]:
            param_id = criterion.get("id")
            score = criterion.get("score")
            relevant = criterion.get("relevant", True)

            # Фильтр: только ошибки (failed или unknown)
            is_failed = relevant and score is not None and score < 1.0
            is_unknown = not relevant and score is None

            if is_failed or is_unknown:
                # Определение severity
                severity = "required" if param_id in self.REQUIRED_CRITERIA else "optional"
                status = "failed" if is_failed else "unknown"

                # Извлечение цитаты (если есть транскрипция)
                quote = self._extract_quote(
                    transcription_text, criterion.get("name", ""), criterion.get("comment", "")
                )

                event = {
                    "call_id": call_id,
                    "timestamp": timestamp,
                    "admin_name": admin_name,
                    "branch_address": branch_address,
                    "equipment_type": equipment_type,
                    "param_id": param_id,
                    "param_name": criterion.get("name", ""),
                    "severity": severity,
                    "status": status,
                    "score": score,
                    "comment": criterion.get("comment", ""),
                    "quote": quote,
                    "transcription_path": f"output/{call_id}.txt",
                }

                events.append(event)

        logger.info(f"Извлечено ошибок: {len(events)} (из {len(quality_analysis['criteria_evaluations'])} критериев)")

        return events

    def _extract_quote(self, transcription: str, param_name: str, comment: str) -> str:
        """
        Извлечь цитату из транскрипции (контекст проблемы).

        Args:
            transcription: Полная транскрипция
            param_name: Название параметра
            comment: Комментарий к ошибке

        Returns:
            str: Цитата (до 200 символов)
        """
        if not transcription:
            return comment[:200] if comment else ""

        # Простое извлечение - первые 200 символов как контекст
        # В будущем можно улучшить - искать упоминания администратора
        quote = transcription[:200].strip()

        if len(transcription) > 200:
            quote += "..."

        return quote

    def save_to_db(self, events: List[Dict]) -> int:
        """
        Сохранить события в БД.

        Args:
            events: Список событий

        Returns:
            int: Количество сохранённых
        """
        return self.db_manager.insert_error_events(events)

    def save_call_summary(self, quality_analysis: Dict) -> bool:
        """
        Сохранить сводку по звонку.

        Args:
            quality_analysis: Результат анализа качества

        Returns:
            bool: True если сохранено
        """
        # Подсчёт ошибок по severity
        required_errors = 0
        optional_errors = 0

        for criterion in quality_analysis.get("criteria_evaluations", []):
            param_id = criterion.get("id")
            score = criterion.get("score")
            relevant = criterion.get("relevant", True)

            is_error = (relevant and score is not None and score < 1.0) or (
                not relevant and score is None
            )

            if is_error:
                if param_id in self.REQUIRED_CRITERIA:
                    required_errors += 1
                else:
                    optional_errors += 1

        summary = {
            "call_id": quality_analysis.get("call_id", "unknown"),
            "timestamp": quality_analysis.get("processed_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
            "admin_name": quality_analysis.get("admin_name"),
            "branch_address": quality_analysis.get("clinic_address"),
            "equipment_type": quality_analysis.get("equipment_type"),
            "overall_score": quality_analysis.get("overall_score"),
            "errors_count": required_errors + optional_errors,
            "required_errors": required_errors,
            "optional_errors": optional_errors,
        }

        return self.db_manager.insert_call_summary(summary)

