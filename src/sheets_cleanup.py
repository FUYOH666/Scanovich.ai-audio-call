"""
Утилита для удаления дубликатов из Google Sheets.

Функции:
- Поиск дубликатов по call_id (столбец "📄 Транскрипция")
- Удаление дублирующихся строк (оставляем первую)
- Сухой прогон (dry-run) для проверки перед удалением
"""

import logging
from pathlib import Path
from typing import List, Tuple

import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)


class SheetsCleanup:
    """Очистка дубликатов в Google Sheets."""

    SCOPES = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive.file",
    ]

    def __init__(self, credentials_path: str, spreadsheet_id: str):
        """
        Инициализация.

        Args:
            credentials_path: Путь к JSON credentials
            spreadsheet_id: ID Google Sheets таблицы
        """
        self.credentials_path = Path(credentials_path)
        self.spreadsheet_id = spreadsheet_id

        # Аутентификация
        self._authenticate()

    def _authenticate(self):
        """Аутентификация с Google Sheets API."""
        if not self.credentials_path.exists():
            raise FileNotFoundError(f"Credentials не найдены: {self.credentials_path}")

        try:
            creds = Credentials.from_service_account_file(
                str(self.credentials_path), scopes=self.SCOPES
            )

            self.client = gspread.authorize(creds)
            self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)

            logger.info(f"✓ Подключение к Google Sheets: {self.spreadsheet.title}")

        except Exception as e:
            logger.error(f"Ошибка аутентификации: {e}")
            raise RuntimeError(f"Не удалось подключиться к Google Sheets: {e}") from e

    def find_duplicates(self, worksheet_name: str = "📞 Все звонки") -> List[Tuple[int, str]]:
        """
        Найти дубликаты в таблице.

        Args:
            worksheet_name: Название листа

        Returns:
            List[Tuple[int, str]]: Список дубликатов (номер строки, call_id)
        """
        try:
            worksheet = self.spreadsheet.worksheet(worksheet_name)
        except gspread.exceptions.WorksheetNotFound:
            logger.error(f"Лист '{worksheet_name}' не найден")
            return []

        # Получаем столбец с транскрипциями (предпоследний, индекс 41)
        transcription_col_index = 41
        transcription_col = worksheet.col_values(transcription_col_index)

        # Находим дубликаты
        seen = {}
        duplicates = []

        for row_idx, cell_value in enumerate(transcription_col[1:], start=2):  # Пропускаем заголовок
            if not cell_value or cell_value == "":
                continue

            # Извлекаем call_id из "output/{call_id}.txt" или "=HYPERLINK(...)"
            call_id = None
            if "output/" in cell_value and ".txt" in cell_value:
                # Формат: "output/{call_id}.txt" или "=HYPERLINK("output/{call_id}.txt", "...")"
                start = cell_value.find("output/") + 7
                end = cell_value.find(".txt", start)
                if start > 6 and end > start:
                    call_id = cell_value[start:end]

            if not call_id:
                continue

            if call_id in seen:
                # Дубликат найден!
                duplicates.append((row_idx, call_id))
                logger.info(f"Дубликат найден: строка {row_idx}, call_id={call_id} (оригинал: строка {seen[call_id]})")
            else:
                seen[call_id] = row_idx

        return duplicates

    def remove_duplicates(self, dry_run: bool = True) -> int:
        """
        Удалить дубликаты из таблицы.

        Args:
            dry_run: Если True - только вывод, без удаления

        Returns:
            int: Количество удалённых строк
        """
        duplicates = self.find_duplicates()

        if not duplicates:
            logger.info("✅ Дубликатов не найдено")
            return 0

        logger.info(f"Найдено дубликатов: {len(duplicates)}")

        if dry_run:
            logger.info("🔍 DRY RUN - удаление не выполнено. Запустите с --apply для удаления")
            for row_idx, call_id in duplicates:
                print(f"  Строка {row_idx}: {call_id}")
            return 0

        # Удаление дубликатов (начиная с конца, чтобы индексы не сбивались)
        try:
            worksheet = self.spreadsheet.worksheet("📞 Все звонки")

            # Сортируем по убыванию номера строки
            duplicates_sorted = sorted(duplicates, key=lambda x: x[0], reverse=True)

            for row_idx, call_id in duplicates_sorted:
                logger.info(f"Удаление строки {row_idx}: {call_id}")
                worksheet.delete_rows(row_idx)

            logger.info(f"✅ Удалено дубликатов: {len(duplicates)}")
            return len(duplicates)

        except Exception as e:
            logger.error(f"Ошибка удаления дубликатов: {e}")
            return 0

