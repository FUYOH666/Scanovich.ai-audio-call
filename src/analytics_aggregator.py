"""
Агрегация аналитики: витрины day/week/month, метрики ERR/MissRate.

SQL-based агрегация для быстрых запросов на 60K звонков/месяц.
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

from src.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class AnalyticsAggregator:
    """Агрегация аналитики из SQLite."""

    def __init__(self, db_path: str, aggregates_path: str):
        """
        Инициализация агрегатора.

        Args:
            db_path: Путь к SQLite БД
            aggregates_path: Путь для сохранения витрин
        """
        self.db_manager = DatabaseManager(db_path)
        self.aggregates_path = Path(aggregates_path)
        self.aggregates_path.mkdir(parents=True, exist_ok=True)

        logger.info("✓ AnalyticsAggregator инициализирован")

    def aggregate_day(self, date: str = None) -> Dict:
        """
        Агрегация за день.

        Args:
            date: Дата в формате YYYY-MM-DD (по умолчанию сегодня)

        Returns:
            Dict: Витрина за день
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        conn = self.db_manager.get_connection()

        try:
            # Общие метрики
            cursor = conn.cursor()

            # Всего звонков и ERR
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as total_calls,
                    SUM(CASE WHEN errors_count > 0 THEN 1 ELSE 0 END) as calls_with_errors,
                    SUM(CASE WHEN required_errors > 0 THEN 1 ELSE 0 END) as calls_with_required_errors,
                    AVG(overall_score) as avg_score
                FROM calls_summary
                WHERE DATE(timestamp) = ?
                """,
                (date,),
            )

            row = cursor.fetchone()
            total_calls = row["total_calls"]
            calls_with_errors = row["calls_with_errors"]
            calls_with_required_errors = row["calls_with_required_errors"]
            avg_score = row["avg_score"] if row["avg_score"] else 0

            err_rate = calls_with_errors / total_calls if total_calls > 0 else 0

            # Top-3 провала (required)
            cursor.execute(
                """
                SELECT param_id, param_name, COUNT(*) as miss_count,
                       COUNT(DISTINCT call_id) as calls_affected
                FROM error_events
                WHERE DATE(timestamp) = ? AND severity = 'required'
                GROUP BY param_id, param_name
                ORDER BY miss_count DESC
                LIMIT 3
                """,
                (date,),
            )

            top_failures = []
            for row in cursor.fetchall():
                miss_rate = row["calls_affected"] / total_calls if total_calls > 0 else 0
                top_failures.append(
                    {
                        "param_id": row["param_id"],
                        "param_name": row["param_name"],
                        "miss_count": row["miss_count"],
                        "miss_rate": round(miss_rate, 3),
                    }
                )

            # Статистика по администраторам
            cursor.execute(
                """
                SELECT admin_name,
                       COUNT(*) as calls,
                       AVG(overall_score) as avg_score,
                       SUM(CASE WHEN errors_count > 0 THEN 1 ELSE 0 END) as calls_with_errors
                FROM calls_summary
                WHERE DATE(timestamp) = ?
                GROUP BY admin_name
                ORDER BY calls_with_errors DESC
                """,
                (date,),
            )

            by_admin = {}
            for row in cursor.fetchall():
                admin_name = row["admin_name"] or "Unknown"
                admin_err = row["calls_with_errors"] / row["calls"] if row["calls"] > 0 else 0

                by_admin[admin_name] = {
                    "calls": row["calls"],
                    "avg_score": round(row["avg_score"], 1),
                    "err_rate": round(admin_err, 3),
                }

            # Статистика по филиалам
            cursor.execute(
                """
                SELECT branch_address,
                       COUNT(*) as calls,
                       AVG(overall_score) as avg_score,
                       SUM(CASE WHEN errors_count > 0 THEN 1 ELSE 0 END) as calls_with_errors
                FROM calls_summary
                WHERE DATE(timestamp) = ?
                GROUP BY branch_address
                ORDER BY calls_with_errors DESC
                """,
                (date,),
            )

            by_branch = {}
            for row in cursor.fetchall():
                branch_name = row["branch_address"] or "Unknown"
                branch_err = row["calls_with_errors"] / row["calls"] if row["calls"] > 0 else 0

                by_branch[branch_name] = {
                    "calls": row["calls"],
                    "avg_score": round(row["avg_score"], 1),
                    "err_rate": round(branch_err, 3),
                }

            # Апсейл метрики (критерии 15, 28, 12)
            # Загрузка JSON файлов качества для расчета
            cursor.execute(
                """
                SELECT call_id
                FROM calls_summary
                WHERE DATE(timestamp) = ?
                """,
                (date,),
            )
            
            call_ids = [row["call_id"] for row in cursor.fetchall()]
            upsell_metrics = self._calculate_upsell_metrics(call_ids)

            # Лучший и худший звонок дня (экстремумы)
            cursor.execute(
                """
                SELECT admin_name, overall_score, call_id
                FROM calls_summary
                WHERE DATE(timestamp) = ?
                ORDER BY overall_score DESC
                LIMIT 1
                """,
                (date,),
            )
            
            best_call_row = cursor.fetchone()
            best_call = {
                "admin_name": best_call_row["admin_name"] or "Не представился",
                "score": best_call_row["overall_score"] if best_call_row else 0,
                "call_id": best_call_row["call_id"] if best_call_row else None
            } if best_call_row else None
            
            cursor.execute(
                """
                SELECT admin_name, overall_score, call_id
                FROM calls_summary
                WHERE DATE(timestamp) = ?
                ORDER BY overall_score ASC
                LIMIT 1
                """,
                (date,),
            )
            
            worst_call_row = cursor.fetchone()
            worst_call = {
                "admin_name": worst_call_row["admin_name"] or "Не представился",
                "score": worst_call_row["overall_score"] if worst_call_row else 0,
                "call_id": worst_call_row["call_id"] if worst_call_row else None
            } if worst_call_row else None

            # Формирование витрины
            aggregate = {
                "date": date,
                "total_calls": total_calls,
                "calls_with_errors": calls_with_errors,
                "calls_with_required_errors": calls_with_required_errors,
                "avg_score": round(avg_score, 1),
                "err_rate": round(err_rate, 3),
                "top_3_failures": top_failures,
                "by_admin": by_admin,
                "by_branch": by_branch,
                "upsell_metrics": upsell_metrics,
                "best_call": best_call,
                "worst_call": worst_call,
            }

            # Сохранение витрины
            self._save_aggregate("day", date, aggregate)

            logger.info(
                f"✓ Витрина DAY создана: {date}, звонков={total_calls}, ERR={err_rate:.1%}"
            )

            return aggregate

        finally:
            conn.close()

    def aggregate_week(self, week_start: str = None) -> Dict:
        """
        Агрегация за неделю.

        Args:
            week_start: Начало недели YYYY-MM-DD (понедельник)

        Returns:
            Dict: Витрина за неделю
        """
        if week_start is None:
            # Текущий понедельник
            today = datetime.now()
            week_start = (today - timedelta(days=today.weekday())).strftime("%Y-%m-%d")

        week_end = (
            datetime.strptime(week_start, "%Y-%m-%d") + timedelta(days=6)
        ).strftime("%Y-%m-%d")

        conn = self.db_manager.get_connection()

        try:
            cursor = conn.cursor()

            # Общие метрики за неделю
            cursor.execute(
                """
                SELECT 
                    COUNT(*) as total_calls,
                    SUM(CASE WHEN errors_count > 0 THEN 1 ELSE 0 END) as calls_with_errors,
                    AVG(overall_score) as avg_score
                FROM calls_summary
                WHERE DATE(timestamp) BETWEEN ? AND ?
                """,
                (week_start, week_end),
            )

            row = cursor.fetchone()
            total_calls = row["total_calls"]
            err_rate = row["calls_with_errors"] / total_calls if total_calls > 0 else 0

            # Top-3 провала
            cursor.execute(
                """
                SELECT param_id, param_name, COUNT(*) as miss_count
                FROM error_events
                WHERE DATE(timestamp) BETWEEN ? AND ? AND severity = 'required'
                GROUP BY param_id, param_name
                ORDER BY miss_count DESC
                LIMIT 3
                """,
                (week_start, week_end),
            )

            top_failures = [
                {
                    "param_id": row["param_id"],
                    "param_name": row["param_name"],
                    "miss_count": row["miss_count"],
                }
                for row in cursor.fetchall()
            ]

            # Рейтинг администраторов
            cursor.execute(
                """
                SELECT admin_name,
                       COUNT(*) as calls,
                       AVG(overall_score) as avg_score,
                       SUM(CASE WHEN errors_count > 0 THEN 1 ELSE 0 END) as calls_with_errors
                FROM calls_summary
                WHERE DATE(timestamp) BETWEEN ? AND ?
                GROUP BY admin_name
                ORDER BY calls_with_errors ASC
                """,
                (week_start, week_end),
            )

            admin_ranking = []
            for row in cursor.fetchall():
                admin_err = row["calls_with_errors"] / row["calls"] if row["calls"] > 0 else 0
                admin_ranking.append(
                    {
                        "admin_name": row["admin_name"] or "Unknown",
                        "calls": row["calls"],
                        "avg_score": round(row["avg_score"], 1),
                        "err_rate": round(admin_err, 3),
                    }
                )

            aggregate = {
                "week_start": week_start,
                "week_end": week_end,
                "total_calls": total_calls,
                "err_rate": round(err_rate, 3),
                "avg_score": round(row["avg_score"], 1) if row["avg_score"] else 0,
                "top_3_failures": top_failures,
                "admin_ranking": admin_ranking,
            }

            # Сохранение витрины
            week_num = datetime.strptime(week_start, "%Y-%m-%d").isocalendar()[1]
            week_key = f"{week_start[:4]}-W{week_num:02d}"
            self._save_aggregate("week", week_key, aggregate)

            logger.info(
                f"✓ Витрина WEEK создана: {week_key}, звонков={total_calls}, ERR={err_rate:.1%}"
            )

            return aggregate

        finally:
            conn.close()

    def _calculate_upsell_metrics(self, call_ids: List[str]) -> Dict:
        """
        Вычислить апсейл метрики по критериям 15, 28, 12.

        Args:
            call_ids: Список ID звонков

        Returns:
            Dict: Апсейл метрики
        """
        # Критерии апсейла:
        # 15 - Описание видеозаключения
        # 28 - Допродажи (уточнение о дополнительных услугах)
        # 12 - Стоимость услуг озвучена

        criteria_map = {
            15: "video_conclusion_rate",
            28: "upsales_rate",
            12: "price_mentioned_rate"
        }

        # Счетчики успехов
        successes = {metric: 0 for metric in criteria_map.values()}
        total_evaluated = {metric: 0 for metric in criteria_map.values()}

        quality_dir = Path("quality_analysis/individual")
        
        if not quality_dir.exists():
            logger.warning("Директория quality_analysis не найдена, апсейл метрики = 0")
            return {metric: 0.0 for metric in criteria_map.values()}

        for call_id in call_ids:
            json_path = quality_dir / f"{call_id}.json"
            
            if not json_path.exists():
                continue
                
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    quality_data = json.load(f)
                
                criteria_evaluations = quality_data.get("criteria_evaluations", [])
                
                for criterion in criteria_evaluations:
                    criterion_id = criterion.get("id")
                    
                    if criterion_id not in criteria_map:
                        continue
                    
                    metric_name = criteria_map[criterion_id]
                    
                    # Проверка на relevant
                    if not criterion.get("relevant", True):
                        continue
                    
                    score = criterion.get("score")
                    
                    if score is None:
                        continue
                    
                    total_evaluated[metric_name] += 1
                    
                    # Успех: score >= 0.5
                    if score >= 0.5:
                        successes[metric_name] += 1
                        
            except Exception as e:
                logger.warning(f"Ошибка загрузки качества для {call_id}: {e}")
                continue
        
        # Вычисление процентов
        metrics = {}
        for metric_name in criteria_map.values():
            if total_evaluated[metric_name] > 0:
                rate = successes[metric_name] / total_evaluated[metric_name]
                metrics[metric_name] = round(rate, 3)
            else:
                metrics[metric_name] = 0.0
        
        logger.debug(
            f"Апсейл метрики: видео={metrics['video_conclusion_rate']:.1%}, "
            f"допродажи={metrics['upsales_rate']:.1%}, цена={metrics['price_mentioned_rate']:.1%}"
        )
        
        return metrics

    def _save_aggregate(self, period_type: str, key: str, data: Dict):
        """
        Сохранить витрину в JSON.

        Args:
            period_type: 'day' или 'week' или 'month'
            key: Ключ (дата или неделя)
            data: Данные витрины
        """
        file_path = self.aggregates_path / f"{period_type}_{key}.json"

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.debug(f"Витрина сохранена: {file_path.name}")

    def get_top_admins_needing_training(self, period_days: int = 7, limit: int = 3) -> List[Dict]:
        """
        Получить список администраторов с высоким ERR (требуют обучения).

        Args:
            period_days: Период в днях
            limit: Количество администраторов

        Returns:
            List[Dict]: Список администраторов
        """
        date_from = (datetime.now() - timedelta(days=period_days)).strftime("%Y-%m-%d")

        conn = self.db_manager.get_connection()

        try:
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT admin_name,
                       COUNT(*) as calls,
                       SUM(CASE WHEN errors_count > 0 THEN 1 ELSE 0 END) as calls_with_errors,
                       AVG(overall_score) as avg_score
                FROM calls_summary
                WHERE DATE(timestamp) >= ?
                GROUP BY admin_name
                HAVING calls >= 3  -- Минимум 3 звонка для статистики
                ORDER BY calls_with_errors DESC
                LIMIT ?
                """,
                (date_from, limit),
            )

            result = []
            for row in cursor.fetchall():
                err_rate = row["calls_with_errors"] / row["calls"]
                result.append(
                    {
                        "admin_name": row["admin_name"],
                        "calls": row["calls"],
                        "err_rate": round(err_rate, 3),
                        "avg_score": round(row["avg_score"], 1),
                    }
                )

            return result

        finally:
            conn.close()

