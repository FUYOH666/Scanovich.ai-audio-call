"""
Модуль отслеживания стоимости API вызовов (OpenRouter).

Функции:
- Сбор статистики токенов и стоимости
- Агрегация по периодам
- Вывод отчётов
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class CostTracker:
    """Отслеживание расходов на API вызовы."""

    def __init__(self, analysis_dir: str):
        """
        Инициализация трекера стоимости.

        Args:
            analysis_dir: Директория с результатами анализа
        """
        self.analysis_dir = Path(analysis_dir)

    def collect_stats(
        self, period_days: Optional[int] = None
    ) -> Dict:
        """
        Сбор статистики по всем анализам.

        Args:
            period_days: Период в днях (None = все время)

        Returns:
            Dict: Агрегированная статистика
        """
        if not self.analysis_dir.exists():
            logger.warning(f"Директория анализов не найдена: {self.analysis_dir}")
            return self._empty_stats()

        analysis_files = list(self.analysis_dir.glob("*.json"))

        if not analysis_files:
            logger.info("Нет анализов для подсчёта статистики")
            return self._empty_stats()

        # Фильтрация по периоду
        if period_days:
            cutoff_date = datetime.now() - timedelta(days=period_days)
            filtered_files = []
            for file in analysis_files:
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        processed_at = datetime.strptime(
                            data["processed_at"], "%Y-%m-%d %H:%M:%S"
                        )
                        if processed_at >= cutoff_date:
                            filtered_files.append(file)
                except Exception:
                    continue
            analysis_files = filtered_files

        # Сбор статистики
        total_calls = 0
        total_tokens_prompt = 0
        total_tokens_completion = 0
        total_cost = 0.0
        scores = []
        admin_stats = {}

        for file in analysis_files:
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                total_calls += 1

                # Токены и стоимость
                if "tokens_used" in data:
                    total_tokens_prompt += data["tokens_used"].get("prompt", 0)
                    total_tokens_completion += data["tokens_used"].get("completion", 0)

                if "cost_usd" in data:
                    total_cost += data["cost_usd"]

                # Оценки
                if "overall_score" in data:
                    scores.append(data["overall_score"])

                # Статистика по администраторам
                admin_name = data.get("admin_name")
                if admin_name:
                    if admin_name not in admin_stats:
                        admin_stats[admin_name] = {
                            "count": 0,
                            "total_score": 0,
                            "scores": [],
                        }
                    admin_stats[admin_name]["count"] += 1
                    admin_stats[admin_name]["total_score"] += data.get(
                        "overall_score", 0
                    )
                    admin_stats[admin_name]["scores"].append(
                        data.get("overall_score", 0)
                    )

            except Exception as e:
                logger.warning(f"Ошибка обработки файла {file.name}: {e}")

        # Расчёт средних
        avg_score = sum(scores) / len(scores) if scores else 0
        avg_tokens_per_call = (
            (total_tokens_prompt + total_tokens_completion) / total_calls
            if total_calls
            else 0
        )
        avg_cost_per_call = total_cost / total_calls if total_calls else 0

        # Средние по администраторам
        for admin_name, stats in admin_stats.items():
            stats["avg_score"] = stats["total_score"] / stats["count"]

        return {
            "total_calls": total_calls,
            "total_tokens": {
                "prompt": total_tokens_prompt,
                "completion": total_tokens_completion,
                "total": total_tokens_prompt + total_tokens_completion,
            },
            "total_cost_usd": round(total_cost, 4),
            "averages": {
                "score": round(avg_score, 2),
                "tokens_per_call": round(avg_tokens_per_call, 0),
                "cost_per_call": round(avg_cost_per_call, 4),
            },
            "admin_stats": admin_stats,
            "period_days": period_days,
        }

    def _empty_stats(self) -> Dict:
        """Пустая статистика."""
        return {
            "total_calls": 0,
            "total_tokens": {"prompt": 0, "completion": 0, "total": 0},
            "total_cost_usd": 0.0,
            "averages": {"score": 0, "tokens_per_call": 0, "cost_per_call": 0},
            "admin_stats": {},
        }

    def print_stats(self, stats: Dict):
        """
        Вывод статистики в консоль.

        Args:
            stats: Статистика от collect_stats()
        """
        print("\n" + "=" * 60)
        print("💰 СТАТИСТИКА СТОИМОСТИ АНАЛИЗА КАЧЕСТВА")
        print("=" * 60)

        if stats["total_calls"] == 0:
            print("\nАнализов пока нет")
            print("=" * 60 + "\n")
            return

        print(f"\n📊 Общие показатели:")
        print(f"  Проанализировано звонков: {stats['total_calls']}")
        print(f"  Средний балл качества: {stats['averages']['score']}/100")

        print(f"\n💵 Токены и стоимость:")
        print(f"  Prompt токенов: {stats['total_tokens']['prompt']:,}")
        print(f"  Completion токенов: {stats['total_tokens']['completion']:,}")
        print(f"  Всего токенов: {stats['total_tokens']['total']:,}")
        print(f"  Общая стоимость: ${stats['total_cost_usd']:.4f}")

        print(f"\n📈 Средние показатели:")
        print(f"  Токенов на звонок: {stats['averages']['tokens_per_call']:.0f}")
        print(f"  Стоимость на звонок: ${stats['averages']['cost_per_call']:.4f}")

        # Статистика по администраторам
        if stats["admin_stats"]:
            print(f"\n👥 По администраторам:")
            for admin_name, admin_data in sorted(
                stats["admin_stats"].items(),
                key=lambda x: x[1]["avg_score"],
                reverse=True,
            ):
                print(
                    f"  {admin_name}: {admin_data['count']} звонков, "
                    f"средний балл {admin_data['avg_score']:.1f}/100"
                )

        print("\n" + "=" * 60 + "\n")

