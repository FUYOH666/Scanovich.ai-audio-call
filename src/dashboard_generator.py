"""
Генератор Dashboard для Google Sheets.

Формирует строки Dashboard в формате временного ряда:
каждая строка = день с ключевыми метриками.
"""

import logging
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger(__name__)


class DashboardGenerator:
    """Генератор строк Dashboard для Google Sheets."""

    def __init__(self):
        """Инициализация генератора."""
        logger.info("✓ DashboardGenerator инициализирован")

    def generate_daily_row(self, aggregate: Dict) -> List:
        """
        Сформировать строку Dashboard за день.

        Args:
            aggregate: Витрина дня из AnalyticsAggregator.aggregate_day()

        Returns:
            List: Строка с 22 значениями (столбцами)
        """
        date = aggregate.get("date", "N/A")
        total_calls = aggregate.get("total_calls", 0)
        avg_score = aggregate.get("avg_score", 0)
        err_rate = aggregate.get("err_rate", 0)

        # Форматирование даты
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            date_formatted = date_obj.strftime("%d.%m.%Y")
        except (ValueError, TypeError):
            date_formatted = date

        # Апсейл метрики
        upsell = aggregate.get("upsell_metrics", {})
        video_rate = upsell.get("video_conclusion_rate", 0)
        upsales_rate = upsell.get("upsales_rate", 0)
        price_rate = upsell.get("price_mentioned_rate", 0)

        # Топ-3 ошибки
        top_failures = aggregate.get("top_3_failures", [])
        
        # Дополняем до 3 элементов пустыми значениями если нужно
        while len(top_failures) < 3:
            top_failures.append({"param_name": "-", "miss_rate": 0})

        top1_name = top_failures[0].get("param_name", "-")
        top1_rate = top_failures[0].get("miss_rate", 0)
        top2_name = top_failures[1].get("param_name", "-")
        top2_rate = top_failures[1].get("miss_rate", 0)
        top3_name = top_failures[2].get("param_name", "-")
        top3_rate = top_failures[2].get("miss_rate", 0)

        # Рейтинг администраторов
        by_admin = aggregate.get("by_admin", {})
        best_admin, best_score = self._get_best_admin(by_admin)
        worst_admin, worst_score = self._get_worst_admin(by_admin)

        # Рейтинг филиалов
        by_branch = aggregate.get("by_branch", {})
        problem_branch, problem_err = self._get_problem_branch(by_branch)
        top_branch, top_err = self._get_top_branch(by_branch)

        # Лучший и худший звонок дня (экстремумы)
        best_call = aggregate.get("best_call", {})
        best_call_admin = best_call.get("admin_name", "-") if best_call else "-"
        best_call_score = best_call.get("score", 0) if best_call else 0

        worst_call = aggregate.get("worst_call", {})
        worst_call_admin = worst_call.get("admin_name", "-") if worst_call else "-"
        worst_call_score = worst_call.get("score", 0) if worst_call else 0

        # Отметка о наличии детальной витрины
        details_mark = "✓"

        # Формирование строки (26 столбцов)
        row = [
            date_formatted,                  # 1. Дата
            total_calls,                     # 2. Звонков
            round(avg_score, 1),             # 3. Балл
            self._format_percent(err_rate),  # 4. ERR
            self._format_percent(video_rate),    # 5. Видео %
            self._format_percent(upsales_rate),  # 6. Допродажи %
            self._format_percent(price_rate),    # 7. Цена %
            top1_name,                       # 8. Топ-1 ошибка
            self._format_percent(top1_rate), # 9. Топ-1 %
            top2_name,                       # 10. Топ-2 ошибка
            self._format_percent(top2_rate), # 11. Топ-2 %
            top3_name,                       # 12. Топ-3 ошибка
            self._format_percent(top3_rate), # 13. Топ-3 %
            best_admin,                      # 14. 🏆 Лучший
            best_score,                      # 15. Балл лучшего
            worst_admin,                     # 16. ❌ Худший
            worst_score,                     # 17. Балл худшего
            problem_branch,                  # 18. 🏢 Проблемный
            self._format_percent(problem_err), # 19. ERR проблемного
            top_branch,                      # 20. 🏆 Топ филиал
            self._format_percent(top_err),   # 21. ERR топового
            best_call_admin,                 # 22. 🌟 Лучший разговор (админ)
            round(best_call_score, 1),       # 23. Балл лучшего разговора
            worst_call_admin,                # 24. ⚠️ Требует внимания (админ)
            round(worst_call_score, 1),      # 25. Балл худшего разговора
            details_mark,                    # 26. 📊 Детали
        ]

        logger.debug(
            f"Dashboard строка сформирована: {date_formatted}, "
            f"{total_calls} звонков, балл={avg_score:.1f}, ERR={err_rate:.0%}"
        )

        return row

    def _format_percent(self, value: float) -> str:
        """
        Форматировать число как процент.

        Args:
            value: Число от 0 до 1

        Returns:
            str: Процент (например "87%")
        """
        return f"{int(value * 100)}%"

    def _get_best_admin(self, by_admin: Dict) -> tuple[str, float]:
        """
        Найти лучшего администратора по avg_score.
        
        Минимум 3 звонка для репрезентативности (исключаем выбросы).

        Args:
            by_admin: Статистика по администраторам

        Returns:
            tuple: (имя, балл)
        """
        if not by_admin:
            return "-", 0.0

        # Фильтруем админов с минимум 3 звонками
        qualified_admins = {
            name: stats for name, stats in by_admin.items()
            if stats.get("calls", 0) >= 3
        }
        
        # Если нет админов с 3+ звонками - берем всех
        if not qualified_admins:
            qualified_admins = by_admin
        
        best = max(qualified_admins.items(), key=lambda x: x[1].get("avg_score", 0))
        admin_name = best[0]
        calls = best[1].get("calls", 0)
        score = best[1].get("avg_score", 0)
        
        # Если Unknown - добавляем контекст
        if admin_name == "Unknown" or admin_name == "Неизвестен":
            admin_name = f"Не представился ({calls} зв., балл {score:.1f})"
            return admin_name, score
        
        # Добавляем количество звонков для прозрачности
        if calls < 5:
            admin_name = f"{admin_name} ({calls} зв.)"
        
        return admin_name, score

    def _get_worst_admin(self, by_admin: Dict) -> tuple[str, float]:
        """
        Найти худшего администратора по avg_score.
        
        Минимум 3 звонка для репрезентативности (исключаем выбросы).

        Args:
            by_admin: Статистика по администраторам

        Returns:
            tuple: (имя, балл)
        """
        if not by_admin:
            return "-", 0.0

        # Фильтруем админов с минимум 3 звонками
        qualified_admins = {
            name: stats for name, stats in by_admin.items()
            if stats.get("calls", 0) >= 3
        }
        
        # Если нет админов с 3+ звонками - берем всех
        if not qualified_admins:
            qualified_admins = by_admin
        
        worst = min(qualified_admins.items(), key=lambda x: x[1].get("avg_score", 0))
        admin_name = worst[0]
        calls = worst[1].get("calls", 0)
        score = worst[1].get("avg_score", 0)
        
        # Если Unknown - добавляем контекст
        if admin_name == "Unknown" or admin_name == "Неизвестен":
            admin_name = f"Не представился ({calls} зв., балл {score:.1f})"
            return admin_name, score
        
        # Добавляем количество звонков для прозрачности
        if calls < 5:
            admin_name = f"{admin_name} ({calls} зв.)"
        
        return admin_name, score

    def _get_problem_branch(self, by_branch: Dict) -> tuple[str, float]:
        """
        Найти проблемный филиал (максимальный ERR, при равенстве - минимальный балл).
        
        Минимум 3 звонка для репрезентативности (исключаем выбросы).

        Args:
            by_branch: Статистика по филиалам

        Returns:
            tuple: (филиал, ERR)
        """
        if not by_branch:
            return "-", 0.0

        # Если только один филиал - не показываем (нечего сравнивать)
        if len(by_branch) == 1:
            return "-", 0.0

        # Фильтруем филиалы с минимум 3 звонками
        qualified_branches = {
            name: stats for name, stats in by_branch.items()
            if stats.get("calls", 0) >= 3
        }
        
        # Если нет филиалов с 3+ звонками - берем всех
        if not qualified_branches:
            qualified_branches = by_branch

        # Сортировка: сначала по ERR (desc), потом по avg_score (asc)
        # Худший = максимальный ERR + минимальный балл
        problem = max(
            qualified_branches.items(),
            key=lambda x: (x[1].get("err_rate", 0), -x[1].get("avg_score", 0))
        )
        
        branch_name = problem[0]
        err_rate = problem[1].get("err_rate", 0)
        calls = problem[1].get("calls", 0)
        score = problem[1].get("avg_score", 0)
        
        # Если Unknown - добавляем контекст
        if branch_name == "Unknown" or branch_name == "N/A":
            branch_name = f"Не определен ({calls} зв., балл {score:.1f})"
        elif calls < 5:
            # Для малого количества звонков показываем количество
            branch_name = f"{branch_name} ({calls} зв.)"
        
        return branch_name, err_rate

    def _get_top_branch(self, by_branch: Dict) -> tuple[str, float]:
        """
        Найти лучший филиал (минимальный ERR, при равенстве - максимальный балл).
        
        Минимум 3 звонка для репрезентативности (исключаем выбросы).

        Args:
            by_branch: Статистика по филиалам

        Returns:
            tuple: (филиал, ERR)
        """
        if not by_branch:
            return "-", 0.0

        # Если только один филиал - не показываем (нечего сравнивать)
        if len(by_branch) == 1:
            return "-", 0.0

        # Фильтруем филиалы с минимум 3 звонками
        qualified_branches = {
            name: stats for name, stats in by_branch.items()
            if stats.get("calls", 0) >= 3
        }
        
        # Если нет филиалов с 3+ звонками - берем всех
        if not qualified_branches:
            qualified_branches = by_branch

        # Сортировка: сначала по ERR (asc), потом по avg_score (desc)
        # Лучший = минимальный ERR + максимальный балл
        top = min(
            qualified_branches.items(),
            key=lambda x: (x[1].get("err_rate", 0), -x[1].get("avg_score", 0))
        )
        
        branch_name = top[0]
        err_rate = top[1].get("err_rate", 0)
        calls = top[1].get("calls", 0)
        score = top[1].get("avg_score", 0)
        
        # Если Unknown - добавляем контекст
        if branch_name == "Unknown" or branch_name == "N/A":
            branch_name = f"Не определен ({calls} зв., балл {score:.1f})"
        elif calls < 5:
            # Для малого количества звонков показываем количество
            branch_name = f"{branch_name} ({calls} зв.)"
        
        return branch_name, err_rate

    @staticmethod
    def get_headers() -> List[str]:
        """
        Получить заголовки столбцов Dashboard.

        Returns:
            List[str]: Список заголовков (26 элементов)
        """
        return [
            "Дата",
            "Звонков",
            "Балл",
            "ERR",
            "Видео %",
            "Допродажи %",
            "Цена %",
            "Топ-1 ошибка",
            "Топ-1 %",
            "Топ-2 ошибка",
            "Топ-2 %",
            "Топ-3 ошибка",
            "Топ-3 %",
            "🏆 Лучший (средний)",
            "Балл",
            "❌ Худший (средний)",
            "Балл",
            "🏢 Проблемный",
            "ERR",
            "🏆 Топ филиал",
            "ERR",
            "🌟 Лучший разговор",
            "Балл",
            "⚠️ Требует внимания",
            "Балл",
            "📊 Детали",
        ]

