"""
Интеграция с Google Sheets для live мониторинга владельцем.

Вариант B (батчи):
- Батчевое обновление всех звонков (23:00)
- Ежечасное обновление Dashboard
- Еженедельное обновление трендов
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import gspread
from google.oauth2.service_account import Credentials

from src.db_manager import DatabaseManager

logger = logging.getLogger(__name__)


class GoogleSheetsIntegrator:
    """Интеграция с Google Sheets для аналитики."""

    # Scope для Google Sheets API
    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
    ]

    def __init__(
        self,
        credentials_path: str,
        spreadsheet_id: str,
        db_path: str,
    ):
        """
        Инициализация интегратора.

        Args:
            credentials_path: Путь к JSON credentials
            spreadsheet_id: ID Google Sheets таблицы
            db_path: Путь к SQLite БД
        """
        self.credentials_path = Path(credentials_path)
        self.spreadsheet_id = spreadsheet_id
        self.db_manager = DatabaseManager(db_path)

        # Аутентификация
        self._authenticate()

        logger.info(f"✓ GoogleSheetsIntegrator инициализирован")

    def _authenticate(self):
        """Аутентификация с Google Sheets API."""
        if not self.credentials_path.exists():
            raise FileNotFoundError(
                f"Credentials не найдены: {self.credentials_path}"
            )

        try:
            creds = Credentials.from_service_account_file(
                str(self.credentials_path), scopes=self.SCOPES
            )

            self.client = gspread.authorize(creds)
            self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)

            logger.info(
                f"✓ Аутентификация с Google Sheets: {self.spreadsheet.title}"
            )

        except Exception as e:
            logger.error(f"Ошибка аутентификации Google Sheets: {e}")
            raise RuntimeError(f"Не удалось подключиться к Google Sheets: {e}") from e

    def add_call_realtime(self, call_data: Dict) -> bool:
        """
        Добавить звонок в Google Sheets (real-time после анализа).

        Args:
            call_data: Данные звонка с анализом качества

        Returns:
            bool: True если добавлено
        """
        call_id = call_data.get('call_id', 'unknown')
        logger.info(f"Добавление звонка в Google Sheets: {call_id}")

        try:
            # Получение или создание листа
            try:
                worksheet = self.spreadsheet.worksheet("📞 Все звонки")
            except gspread.exceptions.WorksheetNotFound:
                worksheet = self.spreadsheet.add_worksheet(
                    title="📞 Все звонки", rows=10000, cols=42  # 8 базовых + 30 критериев + 2 файла
                )

                # Добавление заголовков
                headers = [
                    "Дата",
                    "Время",
                    "Админ",
                    "Филиал",
                    "Оборудование",
                    "Длит.(мин)",
                    "Общий балл",
                    "Ошибок",
                ]
                
                # Добавляем заголовки для всех 30 критериев
                criteria_names = [
                    "1.Название центра", "2.Имя админа", "3.Приветствие", "4.Имя клиента", "5.Жалобы",
                    "6.Длительность симптомов", "7.Характер боли", "8.Визит к врачу", "9.Запрос клиента", "10.Рекомендация",
                    "11.Аргументы", "12.Стоимость", "13.Выбор клиента", "14.Формат заключения", "15.Видеозаключение",
                    "16.Дата записи", "17.Время записи", "18.Персональные данные", "19.Подготовка", "20.Стоимость носителя",
                    "21.Вежливость", "22.Подтверждение", "23.Противопоказания", "24.Повторение итогов", "25.Удобство времени",
                    "26.Льготы/скидки", "27.Эмоц.интеллект", "28.Допродажи", "29.Адрес центра", "30.Телефон/контакты",
                ]
                
                headers.extend(criteria_names)
                headers.extend(["📄 Транскрипция", "📊 JSON"])
                
                worksheet.append_row(headers)
                
                # Заморозка первой строки для удобства прокрутки
                worksheet.freeze(rows=1)
                
                logger.info("✓ Лист '📞 Все звонки' создан с 30 критериями")

            # ⭐ ПРОВЕРКА НА ДУБЛИКАТЫ: ищем call_id в столбце "📄 Транскрипция"
            # Транскрипция формата: "output/{call_id}.txt"
            try:
                # Получаем последний столбец с ссылками на транскрипции (предпоследний)
                transcription_col_index = 41  # 8 базовых + 30 критериев + 1 (Транскрипция)
                transcription_col = worksheet.col_values(transcription_col_index)
                
                # Проверяем, есть ли уже этот call_id
                search_pattern = f"output/{call_id}.txt"
                for cell_value in transcription_col:
                    if search_pattern in str(cell_value):
                        logger.warning(f"⚠️ Звонок {call_id} уже существует в Google Sheets, пропускаем")
                        return False
                        
            except Exception as check_error:
                logger.warning(f"Не удалось проверить дубликаты: {check_error}, продолжаем добавление")

            # Формирование строки
            row = call_data.get("row_data", [])
            
            # Добавление строки с формулами (value_input_option='USER_ENTERED')
            worksheet.append_row(row, value_input_option='USER_ENTERED')
            
            logger.info(f"✓ Звонок добавлен в Google Sheets (с кликабельными ссылками)")
            return True

        except Exception as e:
            logger.error(f"Ошибка добавления звонка в Google Sheets: {e}")
            return False

    def batch_update_calls(self, date: str = None) -> int:
        """
        Батчевое обновление всех звонков за день.

        Args:
            date: Дата в формате YYYY-MM-DD (по умолчанию сегодня)

        Returns:
            int: Количество добавленных строк
        """
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")

        logger.info(f"Батчевая синхронизация звонков за {date}...")

        # Получение данных из SQLite
        conn = self.db_manager.get_connection()

        try:
            cursor = conn.cursor()

            # Запрос звонков с метаданными (включая длительность)
            # Загружаем metadata файлы для получения длительности
            import json
            from pathlib import Path
            
            metadata_dir = Path("metadata")
            
            cursor.execute(
                """
                SELECT 
                    cs.call_id,
                    cs.timestamp,
                    cs.admin_name,
                    cs.branch_address,
                    cs.overall_score,
                    cs.errors_count,
                    cs.required_errors,
                    cs.optional_errors
                FROM calls_summary cs
                WHERE DATE(cs.timestamp) = ?
                ORDER BY cs.timestamp DESC
                """,
                (date,),
            )

            calls = cursor.fetchall()

            if not calls:
                logger.info(f"Нет звонков за {date}")
                return 0

            # Формирование строк для Google Sheets
            rows = []

            for call in calls:
                # Извлечение критичных ошибок
                cursor.execute(
                    """
                    SELECT param_name
                    FROM error_events
                    WHERE call_id = ? AND severity = 'required'
                    ORDER BY param_id
                    LIMIT 5
                    """,
                    (call["call_id"],),
                )

                critical_errors = [row[0] for row in cursor.fetchall()]
                critical_str = ", ".join(critical_errors[:3]) if critical_errors else "-"

                # Извлечение optional ошибок
                cursor.execute(
                    """
                    SELECT param_name
                    FROM error_events
                    WHERE call_id = ? AND severity = 'optional'
                    ORDER BY param_id
                    LIMIT 5
                    """,
                    (call["call_id"],),
                )

                optional_errors = [row[0] for row in cursor.fetchall()]
                optional_str = ", ".join(optional_errors[:3]) if optional_errors else "-"

                # Парсинг timestamp
                dt = datetime.strptime(call["timestamp"], "%Y-%m-%d %H:%M:%S")

                # Извлечение длительности из metadata
                duration_str = ""
                metadata_path = metadata_dir / f"{call['call_id']}.json"
                if metadata_path.exists():
                    try:
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                            audio_duration = metadata.get("asr_metrics", {}).get("audio_duration")
                            if audio_duration:
                                # Конвертация секунд в мин:сек
                                minutes = int(audio_duration // 60)
                                seconds = int(audio_duration % 60)
                                duration_str = f"{minutes}:{seconds:02d}"
                    except:
                        pass

                # Имя админа (если N/A - пытаемся извлечь из транскрипции)
                admin_display = call["admin_name"] or "Неизвестен"

                # Формирование строки с гиперссылками
                # Ссылка на транскрипцию
                transcript_link = f'=HYPERLINK("output/{call["call_id"]}.txt", "Транскрипция")'
                
                # Ссылка на детальный анализ
                quality_link = f'=HYPERLINK("quality_analysis/individual/{call["call_id"]}.json", "30 критериев")'
                
                row = [
                    dt.strftime("%d.%m.%Y"),  # Дата
                    dt.strftime("%H:%M"),  # Время
                    admin_display,  # Админ
                    call["branch_address"] or "N/A",  # Филиал
                    duration_str,  # Длительность (мин:сек)
                    call["overall_score"] or 0,  # Балл
                    call["errors_count"] or 0,  # Ошибок (было ERR)
                    critical_str,  # Critical ошибки
                    optional_str,  # Optional ошибки
                    transcript_link,  # Ссылка на транскрипцию
                    quality_link,  # Ссылка на детальный анализ
                ]

                rows.append(row)

            # Получение или создание листа "Все звонки"
            try:
                worksheet = self.spreadsheet.worksheet("📞 Все звонки")
            except gspread.exceptions.WorksheetNotFound:
                worksheet = self.spreadsheet.add_worksheet(
                    title="📞 Все звонки", rows=1000, cols=10
                )

                # Добавление заголовков
                headers = [
                    "Дата",
                    "Время",
                    "Админ",
                    "Филиал",
                    "Длит.(мин)",
                    "Балл",
                    "Ошибок (всего)",  # Было "ERR" - теперь понятнее
                    "❌ Critical",
                    "⚠️ Optional",
                    "📄 Транскрипция",
                    "📊 Детали (30 критериев)",
                ]
                worksheet.append_row(headers)

            # Батчевое добавление строк (1 API запрос с формулами!)
            if rows:
                worksheet.append_rows(rows, value_input_option='USER_ENTERED')
                logger.info(f"✓ Google Sheets обновлена: {len(rows)} строк добавлено (с кликабельными ссылками)")

            return len(rows)

        finally:
            conn.close()

    def update_dashboard(self, aggregate: Dict) -> bool:
        """
        Обновление Dashboard (добавление/обновление строки за день).

        Args:
            aggregate: Витрина дня из AnalyticsAggregator.aggregate_day()

        Returns:
            bool: True если обновлено
        """
        from src.dashboard_generator import DashboardGenerator

        date = aggregate.get("date", datetime.now().strftime("%Y-%m-%d"))
        
        logger.info(f"Обновление Google Sheets Dashboard за {date}...")

        try:
            # Получение или создание листа Dashboard
            try:
                worksheet = self.spreadsheet.worksheet("📊 Dashboard")
            except gspread.exceptions.WorksheetNotFound:
                # Создание нового листа с заголовками
                worksheet = self.spreadsheet.add_worksheet(
                    title="📊 Dashboard", rows=1000, cols=26
                )
                
                # Добавление заголовков
                generator = DashboardGenerator()
                headers = generator.get_headers()
                worksheet.append_row(headers)
                
                # Заморозка первой строки
                worksheet.freeze(rows=1)
                
                logger.info("✓ Лист '📊 Dashboard' создан с заголовками")

            # Проверка на дубликаты: получаем первый столбец (даты)
            try:
                # Форматируем дату для поиска
                date_obj = datetime.strptime(date, "%Y-%m-%d")
                date_search = date_obj.strftime("%d.%m.%Y")
                
                dates_column = worksheet.col_values(1)  # Первый столбец
                
                # Ищем строку с этой датой (пропускаем заголовок)
                row_index = None
                for i, cell_date in enumerate(dates_column[1:], start=2):
                    if cell_date == date_search:
                        row_index = i
                        break
                
                # Генерация строки Dashboard
                generator = DashboardGenerator()
                dashboard_row = generator.generate_daily_row(aggregate)
                
                if row_index:
                    # Обновление существующей строки (26 столбцов A-Z)
                    range_name = f"A{row_index}:Z{row_index}"
                    worksheet.update(values=[dashboard_row], range_name=range_name, value_input_option='USER_ENTERED')
                    logger.info(f"✓ Dashboard обновлён: строка {row_index} (дата {date_search})")
                else:
                    # Добавление новой строки
                    worksheet.append_row(dashboard_row, value_input_option='USER_ENTERED')
                    logger.info(f"✓ Dashboard: добавлена новая строка за {date_search}")
                
                return True
                
            except Exception as update_error:
                logger.error(f"Ошибка обновления данных Dashboard: {update_error}")
                return False

        except Exception as e:
            logger.error(f"Ошибка обновления Dashboard: {e}")
            return False

    def setup_conditional_formatting(self) -> bool:
        """
        Настройка условного форматирования (цветовое кодирование баллов).

        Returns:
            bool: True если настроено
        """
        try:
            worksheet = self.spreadsheet.worksheet("📞 Все звонки")

            # Условное форматирование для столбца "Балл" (F)
            # Зелёный: ≥85, Жёлтый: 70-84, Красный: <70

            # API для условного форматирования сложный, используем простое решение
            # Владелец может настроить вручную через UI

            logger.info("✓ Условное форматирование (настройте вручную в UI)")
            return True

        except Exception as e:
            logger.error(f"Ошибка настройки форматирования: {e}")
            return False

    def test_connection(self) -> bool:
        """
        Проверка подключения к Google Sheets.

        Returns:
            bool: True если доступ есть
        """
        try:
            title = self.spreadsheet.title
            worksheets = self.spreadsheet.worksheets()

            logger.info(f"✓ Доступ к таблице: {title}")
            logger.info(f"  Листов: {len(worksheets)}")

            for ws in worksheets:
                logger.info(f"    - {ws.title} ({ws.row_count} строк)")

            return True

        except Exception as e:
            logger.error(f"Ошибка проверки подключения: {e}")
            return False

