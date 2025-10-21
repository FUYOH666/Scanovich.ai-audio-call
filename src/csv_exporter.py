"""
CSV экспорт аналитических данных для Excel-анализа.

Форматы:
- errors_export.csv - детальный список ошибок
- admin_summary.csv - сводка по администраторам
"""

import csv
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List

from src.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class CSVExporter:
    """Экспорт аналитики в CSV формат."""

    def __init__(self, db_path: str):
        """
        Инициализация экспортера.

        Args:
            db_path: Путь к SQLite БД
        """
        self.db_manager = DatabaseManager(db_path)
        logger.info("✓ CSVExporter инициализирован")

    def export_errors(
        self, output_path: str, period_days: int = 7, admin_filter: str = None
    ) -> bool:
        """
        Экспорт ошибок в CSV.

        Args:
            output_path: Путь к выходному CSV
            period_days: Период в днях
            admin_filter: Фильтр по администратору

        Returns:
            bool: True если экспортировано
        """
        date_from = (datetime.now() - timedelta(days=period_days)).strftime("%Y-%m-%d")

        conn = self.db_manager.get_connection()

        try:
            cursor = conn.cursor()

            # SQL запрос
            sql = """
                SELECT 
                    DATE(timestamp) as date,
                    admin_name,
                    branch_address,
                    equipment_type,
                    param_name,
                    severity,
                    status,
                    score,
                    comment,
                    quote
                FROM error_events
                WHERE DATE(timestamp) >= ?
            """

            params = [date_from]

            if admin_filter:
                sql += " AND admin_name = ?"
                params.append(admin_filter)

            sql += " ORDER BY timestamp DESC"

            cursor.execute(sql, params)
            rows = cursor.fetchall()

            # Запись в CSV
            with open(output_path, "w", newline="", encoding="utf-8-sig") as csvfile:
                fieldnames = [
                    "Дата",
                    "Админ",
                    "Филиал",
                    "Оборудование",
                    "Критерий",
                    "Severity",
                    "Статус",
                    "Балл",
                    "Комментарий",
                    "Цитата",
                ]

                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for row in rows:
                    writer.writerow(
                        {
                            "Дата": row["date"],
                            "Админ": row["admin_name"] or "N/A",
                            "Филиал": row["branch_address"] or "N/A",
                            "Оборудование": row["equipment_type"] or "N/A",
                            "Критерий": row["param_name"],
                            "Severity": row["severity"],
                            "Статус": row["status"],
                            "Балл": row["score"] if row["score"] is not None else "N/A",
                            "Комментарий": row["comment"] or "",
                            "Цитата": row["quote"] or "",
                        }
                    )

            logger.info(
                f"✓ Экспорт ошибок: {len(rows)} записей → {output_path}"
            )

            return True

        except Exception as e:
            logger.error(f"Ошибка экспорта CSV: {e}")
            return False
        finally:
            conn.close()

    def export_admin_summary(
        self, output_path: str, period_days: int = 7
    ) -> bool:
        """
        Экспорт сводки по администраторам.

        Args:
            output_path: Путь к выходному CSV
            period_days: Период в днях

        Returns:
            bool: True если экспортировано
        """
        date_from = (datetime.now() - timedelta(days=period_days)).strftime("%Y-%m-%d")

        conn = self.db_manager.get_connection()

        try:
            cursor = conn.cursor()

            # Получение данных
            cursor.execute(
                """
                SELECT 
                    admin_name,
                    COUNT(*) as calls,
                    AVG(overall_score) as avg_score,
                    SUM(CASE WHEN errors_count > 0 THEN 1 ELSE 0 END) as calls_with_errors
                FROM calls_summary
                WHERE DATE(timestamp) >= ?
                GROUP BY admin_name
                ORDER BY calls_with_errors DESC
                """,
                (date_from,),
            )

            rows = cursor.fetchall()

            # Запись в CSV
            with open(output_path, "w", newline="", encoding="utf-8-sig") as csvfile:
                fieldnames = ["Админ", "Период", "Звонков", "ERR", "Средний балл"]

                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

                for row in rows:
                    err_rate = row["calls_with_errors"] / row["calls"] if row["calls"] > 0 else 0

                    writer.writerow(
                        {
                            "Админ": row["admin_name"] or "N/A",
                            "Период": f"{date_from} - {datetime.now().strftime('%Y-%m-%d')}",
                            "Звонков": row["calls"],
                            "ERR": f"{err_rate:.1%}",
                            "Средний балл": f"{row['avg_score']:.1f}/100",
                        }
                    )

            logger.info(
                f"✓ Экспорт сводки админов: {len(rows)} записей → {output_path}"
            )

            return True

        except Exception as e:
            logger.error(f"Ошибка экспорта сводки: {e}")
            return False
        finally:
            conn.close()

