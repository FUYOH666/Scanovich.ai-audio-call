"""
Telegram reporter для автоматических отчётов руководителям.

Функции:
- Ежедневные отчёты директорам (09:00)
- Еженедельные отчёты владельцу (понедельник 10:00)
- Отправка примеров-цитат
- Отправка CSV файлов
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from telegram import Bot

logger = logging.getLogger(__name__)


class TelegramReporter:
    """Отправка аналитических отчётов в Telegram."""

    def __init__(self, bot_token: str, default_chat_id: str = None):
        """
        Инициализация Telegram репортера.

        Args:
            bot_token: Токен Telegram бота
            default_chat_id: Chat ID по умолчанию
        """
        self.bot = Bot(token=bot_token)
        self.default_chat_id = default_chat_id

        logger.info("✓ TelegramReporter инициализирован")

    async def send_daily_report(
        self, aggregate: Dict, chat_id: str = None
    ) -> bool:
        """
        Отправить ежедневный отчёт.

        Args:
            aggregate: Витрина за день
            chat_id: ID чата (опционально)

        Returns:
            bool: True если отправлено
        """
        if chat_id is None:
            chat_id = self.default_chat_id

        if not chat_id:
            logger.error("Chat ID не указан для ежедневного отчёта")
            return False

        # Формирование текста отчёта (без Markdown V2 - проще)
        date_str = datetime.strptime(aggregate["date"], "%Y-%m-%d").strftime("%d.%m.%Y")

        message = f"""📊 Ежедневный отчёт | {date_str}

Звонков сегодня: {aggregate['total_calls']}
ERR: {aggregate['err_rate']:.0%} ({aggregate['calls_with_errors']} звонков с ошибками)

⚠️ Top-3 провала (required):
"""

        for i, failure in enumerate(aggregate.get("top_3_failures", [])[:3], 1):
            miss_rate_pct = failure["miss_rate"] * 100
            message += f"{i}. {failure['param_name']} - {failure['miss_count']} звонков ({miss_rate_pct:.0f}%)\n"

        message += "\n👤 Администраторы:\n"

        # Сортировка админов по ERR (худшие первые)
        sorted_admins = sorted(
            aggregate.get("by_admin", {}).items(),
            key=lambda x: x[1]["err_rate"],
            reverse=True,
        )

        for admin_name, stats in sorted_admins[:5]:
            err_pct = stats["err_rate"] * 100
            emoji = "❌" if stats["err_rate"] >= 0.85 else "⚠️" if stats["err_rate"] >= 0.70 else "✅"
            message += f"• {admin_name} - ERR {err_pct:.0f}% ({stats['calls']} звонков) {emoji}\n"

        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=message
            )

            logger.info(f"✓ Ежедневный отчёт отправлен: {date_str}")
            return True

        except Exception as e:
            logger.error(f"Ошибка отправки ежедневного отчёта: {e}")
            return False

    async def send_weekly_report(
        self, aggregate: Dict, chat_id: str = None
    ) -> bool:
        """
        Отправить еженедельный отчёт.

        Args:
            aggregate: Витрина за неделю
            chat_id: ID чата

        Returns:
            bool: True если отправлено
        """
        if chat_id is None:
            chat_id = self.default_chat_id

        if not chat_id:
            logger.error("Chat ID не указан для еженедельного отчёта")
            return False

        # Формирование текста (обычный текст)
        week_start = datetime.strptime(aggregate["week_start"], "%Y-%m-%d").strftime("%d.%m")
        week_end = datetime.strptime(aggregate["week_end"], "%Y-%m-%d").strftime("%d.%m")

        message = f"""📊 Недельный отчёт | {week_start}-{week_end}

Всего звонков: {aggregate['total_calls']}
Средний ERR: {aggregate['err_rate']:.0%}
Средний балл: {aggregate.get('avg_score', 0):.1f}/100

⚠️ Top-3 провала (required):
"""

        for i, failure in enumerate(aggregate.get("top_3_failures", [])[:3], 1):
            message += f"{i}. {failure['param_name']} - {failure['miss_count']} звонков\n"

        message += "\n🏆 Рейтинг администраторов:\n"

        for i, admin in enumerate(aggregate.get("admin_ranking", [])[:5], 1):
            err_pct = admin["err_rate"] * 100
            emoji = "✅" if admin["err_rate"] < 0.70 else "⚠️" if admin["err_rate"] < 0.85 else "❌"
            message += f"{i}. {admin['admin_name']} - ERR {err_pct:.0f}% {emoji} ({admin['calls']} звонков)\n"

        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
            )

            logger.info(f"✓ Еженедельный отчёт отправлен: {week_start}-{week_end}")
            return True

        except Exception as e:
            logger.error(f"Ошибка отправки еженедельного отчёта: {e}")
            return False

    async def send_csv_file(
        self, csv_path: str, caption: str, chat_id: str = None
    ) -> bool:
        """
        Отправить CSV файл в Telegram.

        Args:
            csv_path: Путь к CSV файлу
            caption: Подпись к файлу
            chat_id: ID чата

        Returns:
            bool: True если отправлено
        """
        if chat_id is None:
            chat_id = self.default_chat_id

        if not Path(csv_path).exists():
            logger.error(f"CSV файл не найден: {csv_path}")
            return False

        try:
            with open(csv_path, "rb") as f:
                await self.bot.send_document(
                    chat_id=chat_id,
                    document=f,
                    caption=caption,
                )

            logger.info(f"✓ CSV файл отправлен: {Path(csv_path).name}")
            return True

        except Exception as e:
            logger.error(f"Ошибка отправки CSV: {e}")
            return False

