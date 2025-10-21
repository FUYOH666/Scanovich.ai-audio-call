"""
Генератор отчётов по качеству обслуживания.

Функции:
- Агрегация данных по администраторам
- Генерация Markdown отчётов
- Сравнительный анализ администраторов
"""

import json
import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Генератор отчётов по качеству обслуживания."""

    def __init__(self, analysis_dir: str, reports_dir: str):
        """
        Инициализация генератора отчётов.

        Args:
            analysis_dir: Директория с индивидуальными анализами
            reports_dir: Директория для сохранения отчётов
        """
        self.analysis_dir = Path(analysis_dir)
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def aggregate_by_admin(
        self, admin_name: str, period_days: Optional[int] = 7
    ) -> Dict:
        """
        Агрегация данных по администратору за период.

        Args:
            admin_name: Имя администратора
            period_days: Период в днях (по умолчанию неделя)

        Returns:
            Dict: Агрегированные данные
        """
        if not self.analysis_dir.exists():
            return self._empty_aggregate()

        # Фильтрация файлов
        cutoff_date = None
        if period_days:
            cutoff_date = datetime.now() - timedelta(days=period_days)

        analysis_files = []
        for file in self.analysis_dir.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Фильтр по администратору
                if data.get("admin_name") != admin_name:
                    continue

                # Фильтр по дате
                if cutoff_date:
                    processed_at = datetime.strptime(
                        data["processed_at"], "%Y-%m-%d %H:%M:%S"
                    )
                    if processed_at < cutoff_date:
                        continue

                analysis_files.append((file, data))

            except Exception as e:
                logger.warning(f"Ошибка чтения {file.name}: {e}")

        if not analysis_files:
            logger.warning(f"Нет данных для администратора {admin_name}")
            return self._empty_aggregate()

        # Агрегация данных
        scores = []
        all_strengths = []
        all_weaknesses = []
        all_recommendations = []
        criteria_scores = defaultdict(list)
        equipment_counts = Counter()
        call_types = Counter()

        for file, data in analysis_files:
            # Общие баллы
            scores.append(data.get("overall_score", 0))

            # Тип оборудования
            equipment_counts[data.get("equipment_type", "unknown")] += 1

            # Типы звонков
            if "classification" in data:
                call_type = data["classification"].get("type", "unknown")
                call_types[call_type] += 1

            # Сильные/слабые стороны
            all_strengths.extend(data.get("strengths", []))
            all_weaknesses.extend(data.get("weaknesses", []))
            all_recommendations.extend(data.get("recommendations", []))

            # Баллы по критериям
            for criterion in data.get("criteria_evaluations", []):
                if criterion.get("relevant", True) and criterion.get("score") is not None:
                    criteria_scores[criterion["name"]].append(criterion["score"])

        # Расчёт средних по критериям
        criteria_avg = {
            name: round(sum(scores_list) / len(scores_list), 2)
            for name, scores_list in criteria_scores.items()
        }

        # Топ сильных/слабых сторон
        top_strengths = [
            item for item, count in Counter(all_strengths).most_common(5)
        ]
        top_weaknesses = [
            item for item, count in Counter(all_weaknesses).most_common(5)
        ]
        top_recommendations = [
            item for item, count in Counter(all_recommendations).most_common(5)
        ]

        # Находим критерии с самыми низкими баллами
        worst_criteria = sorted(criteria_avg.items(), key=lambda x: x[1])[:5]
        best_criteria = sorted(criteria_avg.items(), key=lambda x: x[1], reverse=True)[
            :5
        ]

        return {
            "admin_name": admin_name,
            "period_days": period_days,
            "total_calls": len(analysis_files),
            "avg_score": round(sum(scores) / len(scores), 2) if scores else 0,
            "min_score": min(scores) if scores else 0,
            "max_score": max(scores) if scores else 0,
            "equipment_distribution": dict(equipment_counts),
            "call_type_distribution": dict(call_types),
            "top_strengths": top_strengths,
            "top_weaknesses": top_weaknesses,
            "top_recommendations": top_recommendations,
            "best_criteria": best_criteria,
            "worst_criteria": worst_criteria,
            "criteria_details": criteria_avg,
        }

    def generate_admin_report(
        self, admin_name: str, period_days: int = 7
    ) -> str:
        """
        Генерация Markdown отчёта по администратору.

        Args:
            admin_name: Имя администратора
            period_days: Период в днях

        Returns:
            str: Путь к сохранённому отчёту
        """
        # Агрегация данных
        aggregate = self.aggregate_by_admin(admin_name, period_days)

        if aggregate["total_calls"] == 0:
            logger.warning(f"Нет данных для генерации отчёта: {admin_name}")
            return ""

        # Формирование Markdown
        period_start = datetime.now() - timedelta(days=period_days)
        report_md = f"""# Отчёт по качеству обслуживания: {admin_name}

**Период:** {period_start.strftime('%d.%m.%Y')} - {datetime.now().strftime('%d.%m.%Y')}  
**Звонков обработано:** {aggregate['total_calls']}  
**Средний балл:** {aggregate['avg_score']}/100  
**Диапазон:** {aggregate['min_score']:.1f} - {aggregate['max_score']:.1f}  

---

## 📊 Распределение звонков

### По типу оборудования:
"""

        for equipment, count in aggregate["equipment_distribution"].items():
            percent = (count / aggregate["total_calls"]) * 100
            report_md += f"- {equipment}: {count} звонков ({percent:.1f}%)\n"

        report_md += "\n### По типу звонка:\n"
        for call_type, count in aggregate["call_type_distribution"].items():
            percent = (count / aggregate["total_calls"]) * 100
            report_md += f"- {call_type}: {count} ({percent:.1f}%)\n"

        # Сильные стороны
        report_md += "\n---\n\n## ✅ Сильные стороны (Top 5)\n\n"
        for i, strength in enumerate(aggregate["top_strengths"], 1):
            report_md += f"{i}. {strength}\n"

        # Слабые стороны
        report_md += "\n## ⚠️ Области для улучшения (Top 5)\n\n"
        for i, weakness in enumerate(aggregate["top_weaknesses"], 1):
            report_md += f"{i}. {weakness}\n"

        # Рекомендации
        report_md += "\n---\n\n## 💡 Рекомендации (Top 5)\n\n"
        for i, recommendation in enumerate(aggregate["top_recommendations"], 1):
            report_md += f"{i}. {recommendation}\n"

        # Детали по критериям
        report_md += "\n---\n\n## 📋 Детали по критериям\n\n"
        report_md += "### Лучшие критерии:\n"
        for name, score in aggregate["best_criteria"]:
            report_md += f"- {name}: {score:.0%}\n"

        report_md += "\n### Критерии требующие внимания:\n"
        for name, score in aggregate["worst_criteria"]:
            report_md += f"- {name}: {score:.0%}\n"

        report_md += f"\n---\n\n**Отчёт сгенерирован:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"

        # Сохранение отчёта
        report_filename = (
            f"{admin_name}_{period_days}d_{datetime.now().strftime('%Y%m%d')}.md"
        )
        report_path = self.reports_dir / report_filename

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_md)

        logger.info(f"✓ Отчёт сгенерирован: {report_path.name}")
        return str(report_path)

    def compare_admins(self, period_days: int = 7) -> str:
        """
        Сравнительный отчёт по всем администраторам.

        Args:
            period_days: Период в днях

        Returns:
            str: Путь к отчёту
        """
        # Получение списка всех администраторов
        admin_names = set()
        for file in self.analysis_dir.glob("*.json"):
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    admin_name = data.get("admin_name")
                    if admin_name:
                        admin_names.add(admin_name)
            except Exception:
                continue

        if not admin_names:
            logger.warning("Нет данных для сравнительного отчёта")
            return ""

        # Агрегация по каждому администратору
        admin_aggregates = {}
        for admin_name in admin_names:
            admin_aggregates[admin_name] = self.aggregate_by_admin(
                admin_name, period_days
            )

        # Сортировка по среднему баллу
        ranked_admins = sorted(
            admin_aggregates.items(), key=lambda x: x[1]["avg_score"], reverse=True
        )

        # Формирование отчёта
        period_start = datetime.now() - timedelta(days=period_days)
        report_md = f"""# Сравнительный отчёт по администраторам

**Период:** {period_start.strftime('%d.%m.%Y')} - {datetime.now().strftime('%d.%m.%Y')}  
**Всего администраторов:** {len(admin_names)}  

---

## 🏆 Рейтинг администраторов

| Место | Администратор | Звонков | Средний балл | Диапазон |
|-------|---------------|---------|--------------|----------|
"""

        for rank, (admin_name, data) in enumerate(ranked_admins, 1):
            medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
            report_md += (
                f"| {medal} {rank} | {admin_name} | {data['total_calls']} | "
                f"{data['avg_score']:.1f}/100 | {data['min_score']:.1f}-{data['max_score']:.1f} |\n"
            )

        report_md += "\n---\n\n## 💡 Best Practices (от лучших администраторов)\n\n"

        # Сильные стороны лучших
        if ranked_admins:
            best_admin_name, best_data = ranked_admins[0]
            report_md += f"### {best_admin_name} (средний балл: {best_data['avg_score']:.1f})\n\n"
            for strength in best_data["top_strengths"][:3]:
                report_md += f"- ✅ {strength}\n"

        report_md += f"\n---\n\n**Отчёт сгенерирован:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"

        # Сохранение
        report_filename = f"comparison_{period_days}d_{datetime.now().strftime('%Y%m%d')}.md"
        report_path = self.reports_dir / report_filename

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_md)

        logger.info(f"✓ Сравнительный отчёт сгенерирован: {report_path.name}")
        return str(report_path)

    def _empty_aggregate(self) -> Dict:
        """Пустая агрегация."""
        return {
            "total_calls": 0,
            "avg_score": 0,
            "min_score": 0,
            "max_score": 0,
            "equipment_distribution": {},
            "call_type_distribution": {},
            "top_strengths": [],
            "top_weaknesses": [],
            "top_recommendations": [],
            "best_criteria": [],
            "worst_criteria": [],
        }

