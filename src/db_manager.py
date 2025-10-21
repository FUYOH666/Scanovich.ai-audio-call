"""
Менеджер SQLite базы данных для аналитики ошибок.

Схема:
- error_events: события ошибок (failed/unknown критерии)
- calls_summary: сводка по звонкам (для быстрых запросов)
"""

import logging
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Менеджер SQLite базы данных для аналитики."""

    SCHEMA = """
    -- Таблица событий ошибок
    CREATE TABLE IF NOT EXISTS error_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        call_id TEXT NOT NULL,
        timestamp DATETIME NOT NULL,
        admin_name TEXT,
        branch_address TEXT,
        equipment_type TEXT,
        param_id INTEGER,
        param_name TEXT,
        severity TEXT CHECK(severity IN ('required', 'optional')),
        status TEXT CHECK(status IN ('failed', 'unknown')),
        score REAL,
        comment TEXT,
        quote TEXT,
        transcription_path TEXT,
        UNIQUE(call_id, param_id)  -- Идемпотентность
    );

    CREATE INDEX IF NOT EXISTS idx_timestamp ON error_events(timestamp);
    CREATE INDEX IF NOT EXISTS idx_admin ON error_events(admin_name);
    CREATE INDEX IF NOT EXISTS idx_param ON error_events(param_id);
    CREATE INDEX IF NOT EXISTS idx_severity ON error_events(severity);
    CREATE INDEX IF NOT EXISTS idx_status ON error_events(status);

    -- Таблица сводки по звонкам
    CREATE TABLE IF NOT EXISTS calls_summary (
        call_id TEXT PRIMARY KEY,
        timestamp DATETIME NOT NULL,
        admin_name TEXT,
        branch_address TEXT,
        equipment_type TEXT,
        overall_score REAL,
        errors_count INTEGER,
        required_errors INTEGER,
        optional_errors INTEGER
    );

    CREATE INDEX IF NOT EXISTS idx_calls_timestamp ON calls_summary(timestamp);
    CREATE INDEX IF NOT EXISTS idx_calls_admin ON calls_summary(admin_name);
    """

    def __init__(self, db_path: str):
        """
        Инициализация менеджера БД.

        Args:
            db_path: Путь к SQLite файлу
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Создание схемы
        self._init_schema()

        logger.info(f"✓ DatabaseManager инициализирован: {db_path}")

    def _init_schema(self):
        """Создать схему БД если не существует."""
        conn = self.get_connection()
        try:
            conn.executescript(self.SCHEMA)
            conn.commit()
            logger.debug("Схема БД создана/проверена")
        except Exception as e:
            logger.error(f"Ошибка создания схемы БД: {e}")
            raise
        finally:
            conn.close()

    def get_connection(self) -> sqlite3.Connection:
        """
        Получить соединение с БД.

        Returns:
            sqlite3.Connection: Соединение
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Для dict-like доступа
        return conn

    def insert_error_events(self, events: List[Dict]) -> int:
        """
        Вставить события ошибок (batch insert).

        Args:
            events: Список событий ошибок

        Returns:
            int: Количество вставленных записей
        """
        if not events:
            return 0

        conn = self.get_connection()
        inserted = 0

        try:
            cursor = conn.cursor()

            for event in events:
                try:
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO error_events 
                        (call_id, timestamp, admin_name, branch_address, equipment_type,
                         param_id, param_name, severity, status, score, comment, 
                         quote, transcription_path)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            event["call_id"],
                            event["timestamp"],
                            event.get("admin_name"),
                            event.get("branch_address"),
                            event.get("equipment_type"),
                            event["param_id"],
                            event["param_name"],
                            event["severity"],
                            event["status"],
                            event.get("score"),
                            event.get("comment"),
                            event.get("quote"),
                            event.get("transcription_path"),
                        ),
                    )

                    if cursor.rowcount > 0:
                        inserted += 1

                except sqlite3.IntegrityError:
                    # Дубликат - пропускаем (идемпотентность)
                    pass

            conn.commit()
            logger.info(f"✓ Вставлено событий ошибок: {inserted}/{len(events)}")

        except Exception as e:
            logger.error(f"Ошибка вставки событий: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

        return inserted

    def insert_call_summary(self, summary: Dict) -> bool:
        """
        Вставить сводку по звонку.

        Args:
            summary: Сводка по звонку

        Returns:
            bool: True если вставлено
        """
        conn = self.get_connection()

        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO calls_summary
                (call_id, timestamp, admin_name, branch_address, equipment_type,
                 overall_score, errors_count, required_errors, optional_errors)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    summary["call_id"],
                    summary["timestamp"],
                    summary.get("admin_name"),
                    summary.get("branch_address"),
                    summary.get("equipment_type"),
                    summary.get("overall_score"),
                    summary.get("errors_count", 0),
                    summary.get("required_errors", 0),
                    summary.get("optional_errors", 0),
                ),
            )

            conn.commit()
            logger.debug(f"✓ Сводка по звонку сохранена: {summary['call_id']}")
            return True

        except Exception as e:
            logger.error(f"Ошибка вставки сводки: {e}")
            return False
        finally:
            conn.close()

    def get_stats(self) -> Dict:
        """
        Получить общую статистику БД.

        Returns:
            Dict: Статистика
        """
        conn = self.get_connection()

        try:
            cursor = conn.cursor()

            # Количество событий
            cursor.execute("SELECT COUNT(*) FROM error_events")
            events_count = cursor.fetchone()[0]

            # Количество звонков
            cursor.execute("SELECT COUNT(*) FROM calls_summary")
            calls_count = cursor.fetchone()[0]

            # Временной диапазон
            cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM calls_summary")
            time_range = cursor.fetchone()

            return {
                "events_count": events_count,
                "calls_count": calls_count,
                "date_from": time_range[0] if time_range[0] else None,
                "date_to": time_range[1] if time_range[1] else None,
            }

        finally:
            conn.close()

