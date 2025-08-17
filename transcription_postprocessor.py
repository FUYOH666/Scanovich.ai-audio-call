#!/usr/bin/env python3
"""
🔧 Постобработчик транскрипций WhisperX Pipeline v4.0
Автор: Scanovich.ai

Модуль для улучшения точности транскрипций через постобработку:
- Исправление имен администраторов
- Корректировка медицинских терминов
- Стандартизация числительных
- Исправление названий клиник
"""

import re
import logging
from typing import Dict, List, Tuple
from pathlib import Path

logger = logging.getLogger(__name__)


class TranscriptionPostProcessor:
    """Постобработчик для улучшения точности транскрипций"""
    
    def __init__(self):
        """Инициализация постобработчика"""
        
        # Словарь исправления имен администраторов (на основе реальных ошибок)
        self.admin_names_corrections = {
            # РЕАЛЬНЫЕ ОШИБКИ ИЗ ТРАНСКРИПЦИЙ:
            "дианыча": "Диана",
            "яныча": "Яна",  # Исправлено! 😄
            "янечка": "Яна",
            "янка": "Яна", 
            "янушка": "Яна",
            
            # НОВЫЕ ОШИБКИ из Google Таблицы:
            "александр": "Александра",  # В клинике работают девушки
            "алена": "Алёна",           # Возможно правильно, но уточняем
            "лена": "Алёна",            # Из второго звонка ✅ ИСПРАВЛЕНО
            "ленка": "Алёна",           # Дополнительный вариант
            "аленка": "Алёна",          # Дополнительный вариант
            
            # Дополнительные варианты
            "дианычка": "Диана", 
            "дианочка": "Диана",
            "дианка": "Диана",
            "дианюша": "Диана",
            "дианушка": "Диана",
            "анечка": "Анна",
            "анюта": "Анна",
            "анютка": "Анна",
            "машенька": "Мария",
            "машуля": "Мария",
            "катенька": "Екатерина",
            "катюша": "Екатерина",
            "оленька": "Ольга",
            "олечка": "Ольга",
            "наташенька": "Наталья",
            "наташа": "Наталья",
            "светланочка": "Светлана",
            "светочка": "Светлана",
            "юленька": "Юлия",
            "юлечка": "Юлия",
            "иринка": "Ирина",
            "ирочка": "Ирина",
            "танечка": "Татьяна",
            "танюша": "Татьяна",
            "викуля": "Виктория",
            "викторочка": "Виктория",
            
            # Часто путают мужские/женские имена в МРТ клиниках
            "саша": "Александра",      # По умолчанию женское в медицине
            "женя": "Евгения",         # По умолчанию женское в медицине  
            "валя": "Валентина",       # По умолчанию женское в медицине
        }
        
        # Словарь числительных (для веса, возраста, цен)
        self.numbers_corrections = {
            # Вес
            "девяносто пять": "95",
            "девяноста пять": "95", 
            "девяносто два": "92",
            "девяносто три": "93",
            "восемьдесят пять": "85",
            "восемьдесят": "80",
            "семьдесят пять": "75",
            "семьдесят": "70",
            "шестьдесят пять": "65",
            "шестьдесят": "60",
            "пятьдесят пять": "55",
            "пятьдесят": "50",
            
            # Цены
            "одиннадцать тысяч": "11000",
            "двенадцать тысяч": "12000", 
            "тринадцать тысяч": "13000",
            "четырнадцать тысяч": "14000",
            "пятнадцать тысяч": "15000",
            "шестнадцать тысяч": "16000",
            "семнадцать тысяч": "17000",
            "восемнадцать тысяч": "18000",
            "девятнадцать тысяч": "19000",
            "двадцать тысяч": "20000",
            "двадцать одна тысяча": "21000",
            "двадцать две тысячи": "22000",
            "двадцать три тысячи": "23000",
            
            # Возраст
            "тридцать пять": "35",
            "сорок": "40",
            "сорок пять": "45",
            "пятьдесят": "50"
        }
        
        # Медицинские термины (на основе реальных ошибок)
        self.medical_corrections = {
            # РЕАЛЬНЫЕ ОШИБКИ ИЗ ТРАНСКРИПЦИЙ:
            "грызи": "грыжи",
            "прогроза": "протрузия",
            "намертые": "на МРТ",
            "защемление невозможно": "защемление нервов",
            "логалища": "влагалища",
            "брашовый дс": "брюшной полости",
            
            # Дополнительные медицинские термины
            "эмэрти": "МРТ",
            "эм эр ти": "МРТ", 
            "мэрти": "МРТ",
            "магнитно резонансная": "магнитно-резонансная",
            "магнитно резонансное": "магнитно-резонансное",
            "томаграфия": "томография",
            "томагрофия": "томография",
            "позваночника": "позвоночника",
            "позваночный": "позвоночный",
            "голавы": "головы",
            "галовы": "головы",
            "головнова": "головного",
            "суставав": "суставов",
            "суставной": "суставов",
            "контрастом": "с контрастом",
            "контрасное": "контрастное",
            "видеозаключения": "видеозаключение",
            "видео заключения": "видеозаключение",
            "видеаключение": "видеозаключение"
        }
        
        # Названия клиник и адресов (на основе реальных ошибок)
        self.clinic_corrections = {
            # РЕАЛЬНЫЕ ОШИБКИ ИЗ ТРАНСКРИПЦИЙ:
            "марта лидер": "МРТ-Лидер",
            "санта-диагностика": "центр диагностики МРТ-Лидер",
            
            # Дополнительные варианты
            "варфаламеева": "Варфоломеева",
            "варфоломева": "Варфоломеева",
            "варфаломева": "Варфоломеева",
            "мэрт лидер": "МРТ-Лидер",
            "мэрти лидер": "МРТ-Лидер",
            "эмэрт лидер": "МРТ-Лидер",
            "мерт лидер": "МРТ-Лидер",
            "центр мэрт": "центр МРТ",
            "центр эмэрт": "центр МРТ",
            "центр мерт": "центр МРТ"
        }
        
        # Общие исправления
        self.general_corrections = {
            "добрый день": "Добрый день",
            "добрай день": "Добрый день",
            "добраго дня": "Доброго дня", 
            "здраствуйте": "Здравствуйте",
            "здраствуте": "Здравствуйте",
            "прывет": "Привет",
            "прывит": "Привет",
            "спосибо": "Спасибо",
            "спасиба": "Спасибо",
            "пажалуйста": "Пожалуйста",
            "пожалуста": "Пожалуйста"
        }
        
        # НОВЫЙ СЛОВАРЬ: Мусорные слова в ФИО (ошибки WhisperX)
        self.garbage_words_in_names = [
            "осень", "цель", "ванна", "лето", "зима", "весна",
            "стол", "стул", "окно", "дверь", "крыша", "пол",
            "машина", "дорога", "улица", "дом", "квартира",
            "работа", "учеба", "школа", "институт", "больница",
            "магазин", "покупка", "продажа", "деньги", "рубль",
            "время", "час", "минута", "день", "неделя", "месяц"
        ]
        
    def process_transcription(self, transcription: str, context: str = "") -> Tuple[str, Dict]:
        """
        Основной метод постобработки транскрипции
        
        Args:
            transcription: Исходная транскрипция
            context: Контекст звонка (например, "МРТ-клиника")
            
        Returns:
            Tuple[обработанная_транскрипция, статистика_изменений]
        """
        
        logger.info("🔧 Начинаем постобработку транскрипции...")
        
        original_transcription = transcription
        changes_stats = {
            "admin_names": 0,
            "numbers": 0,
            "medical_terms": 0,
            "clinic_names": 0,
            "general": 0,
            "total_changes": 0
        }
        
        # 1. Исправление имен администраторов
        transcription, admin_changes = self._fix_admin_names(transcription)
        changes_stats["admin_names"] = admin_changes
        
        # 2. Исправление числительных
        transcription, number_changes = self._fix_numbers(transcription)
        changes_stats["numbers"] = number_changes
        
        # 3. Исправление медицинских терминов
        transcription, medical_changes = self._fix_medical_terms(transcription)
        changes_stats["medical_terms"] = medical_changes
        
        # 4. Исправление названий клиник
        transcription, clinic_changes = self._fix_clinic_names(transcription)
        changes_stats["clinic_names"] = clinic_changes
        
        # 5. Общие исправления
        transcription, general_changes = self._fix_general_terms(transcription)
        changes_stats["general"] = general_changes
        
        # 6. НОВЫЙ ЭТАП: Очистка мусорных слов в ФИО
        transcription, garbage_changes = self._clean_garbage_words_in_names(transcription)
        changes_stats["garbage_cleanup"] = garbage_changes
        
        # 7. Подсчет общих изменений
        changes_stats["total_changes"] = sum([
            admin_changes, number_changes, medical_changes, 
            clinic_changes, general_changes, garbage_changes
        ])
        
        # Логирование результатов
        if changes_stats["total_changes"] > 0:
            logger.info(f"✅ Постобработка завершена: {changes_stats['total_changes']} исправлений")
            logger.info(f"   👤 Имена: {admin_changes}, 🔢 Числа: {number_changes}")
            logger.info(f"   🏥 Медицина: {medical_changes}, 🏢 Клиники: {clinic_changes}")
            logger.info(f"   📝 Общие: {general_changes}, 🗑️ Мусор: {garbage_changes}")
        else:
            logger.info("✅ Постобработка завершена: исправления не требуются")
            
        return transcription, changes_stats
    
    def _fix_admin_names(self, text: str) -> Tuple[str, int]:
        """Исправление имен администраторов"""
        changes = 0
        for wrong_name, correct_name in self.admin_names_corrections.items():
            # Универсальный поиск имени в тексте
            pattern = rf'\b{re.escape(wrong_name)}\b'
            if re.search(pattern, text, re.IGNORECASE):
                text = re.sub(pattern, correct_name, text, flags=re.IGNORECASE)
                changes += 1
                    
        return text, changes
    
    def _fix_numbers(self, text: str) -> Tuple[str, int]:
        """Исправление числительных"""
        changes = 0
        for number_word, number_digit in self.numbers_corrections.items():
            if number_word.lower() in text.lower():
                # Заменяем только если это не часть другого слова
                pattern = rf'\b{re.escape(number_word)}\b'
                if re.search(pattern, text, re.IGNORECASE):
                    text = re.sub(pattern, f"{number_digit} ({number_word})", 
                                text, flags=re.IGNORECASE)
                    changes += 1
                    
        return text, changes
    
    def _fix_medical_terms(self, text: str) -> Tuple[str, int]:
        """Исправление медицинских терминов"""
        changes = 0
        for wrong_term, correct_term in self.medical_corrections.items():
            if wrong_term.lower() in text.lower():
                pattern = rf'\b{re.escape(wrong_term)}\b'
                if re.search(pattern, text, re.IGNORECASE):
                    text = re.sub(pattern, correct_term, text, flags=re.IGNORECASE)
                    changes += 1
                    
        return text, changes
    
    def _fix_clinic_names(self, text: str) -> Tuple[str, int]:
        """Исправление названий клиник и адресов"""
        changes = 0
        for wrong_name, correct_name in self.clinic_corrections.items():
            if wrong_name.lower() in text.lower():
                pattern = rf'\b{re.escape(wrong_name)}\b'
                if re.search(pattern, text, re.IGNORECASE):
                    text = re.sub(pattern, correct_name, text, flags=re.IGNORECASE)
                    changes += 1
                    
        return text, changes
    
    def _fix_general_terms(self, text: str) -> Tuple[str, int]:
        """Общие исправления речи"""
        changes = 0
        for wrong_term, correct_term in self.general_corrections.items():
            if wrong_term.lower() in text.lower():
                pattern = rf'\b{re.escape(wrong_term)}\b'
                if re.search(pattern, text, re.IGNORECASE):
                    text = re.sub(pattern, correct_term, text, flags=re.IGNORECASE)
                    changes += 1
                    
        return text, changes
    
    def add_custom_correction(self, category: str, wrong_term: str, correct_term: str):
        """Добавление пользовательских исправлений"""
        category_map = {
            "admin_names": self.admin_names_corrections,
            "numbers": self.numbers_corrections,
            "medical": self.medical_corrections,
            "clinic": self.clinic_corrections,
            "general": self.general_corrections
        }
        
        if category in category_map:
            category_map[category][wrong_term.lower()] = correct_term
            logger.info(f"✅ Добавлено исправление: '{wrong_term}' → '{correct_term}' в категорию '{category}'")
        else:
            logger.error(f"❌ Неизвестная категория: {category}")
    
    def get_correction_stats(self) -> Dict:
        """Получение статистики словарей исправлений"""
        return {
            "admin_names": len(self.admin_names_corrections),
            "numbers": len(self.numbers_corrections),
            "medical_terms": len(self.medical_corrections),
            "clinic_names": len(self.clinic_corrections),
            "general_terms": len(self.general_corrections),
            "garbage_words": len(self.garbage_words_in_names)
        }
    
    def _clean_garbage_words_in_names(self, text: str) -> Tuple[str, int]:
        """Очистка мусорных слов в ФИО (ошибки WhisperX)"""
        changes = 0
        original_text = text
        
        # ПРОСТОЙ ПОДХОД: ищем конкретные проблемные паттерны
        
        # 1. Специфический случай "Осень, цель, ванна"
        if "осень" in text.lower() and "цель" in text.lower() and "ванна" in text.lower():
            # Ищем строку с этими словами
            pattern = r'([Оо]сень[,\s]*[Цц]ель[,\s]*[Вв]анна[,\s]*)'
            match = re.search(pattern, text)
            if match:
                # Удаляем мусорные слова
                text = re.sub(pattern, '', text)
                changes += 1
                logger.info(f"🗑️ Удален мусор 'Осень, цель, ванна' из ФИО")
        
        # 2. Общая очистка мусорных слов из любых ФИО в тексте
        for garbage_word in self.garbage_words_in_names:
            # Ищем мусорные слова в контексте с именами
            pattern = rf'\b{re.escape(garbage_word)}\b[,\s]*'
            if re.search(pattern, text, re.IGNORECASE):
                # Проверяем что рядом есть имена (начинающиеся с заглавной буквы)
                name_context_pattern = rf'{pattern}([А-Я][а-я]+(?:\s+[А-Я][а-я]+)*)'
                match = re.search(name_context_pattern, text, re.IGNORECASE)
                if match:
                    # Заменяем только если рядом есть имена
                    text = re.sub(pattern, '', text, flags=re.IGNORECASE)
                    changes += 1
                    logger.info(f"🗑️ Удалено мусорное слово '{garbage_word}' из контекста имен")
        
        # 3. Очищаем множественные запятые и пробелы после удаления
        text = re.sub(r',\s*,+', ',', text)  # множественные запятые
        text = re.sub(r'^\s*,\s*', '', text)  # запятая в начале строки
        text = re.sub(r',\s*$', '', text)     # запятая в конце строки
        text = re.sub(r'\s{2,}', ' ', text)   # множественные пробелы
        
        return text, changes


def test_postprocessor():
    """Тестирование постобработчика"""
    print("🧪 ТЕСТИРОВАНИЕ ПОСТОБРАБОТЧИКА ТРАНСКРИПЦИЙ")
    print("=" * 60)
    
    processor = TranscriptionPostProcessor()
    
    # Тестовые примеры
    test_cases = [
        "Здравствуйте, я Дианыча, чем могу помочь?",
        "МРТ стоит одиннадцать тысяч рублей",
        "Мой вес девяносто пять килограмм",
        "Адрес клиники Варфаламеева 175А",
        "Нужно сделать эмэрти позваночника",
        "Центр мэрт лидер работает до 20:00"
    ]
    
    for i, test_text in enumerate(test_cases, 1):
        print(f"\n📝 Тест {i}:")
        print(f"До:   {test_text}")
        
        processed_text, stats = processor.process_transcription(test_text)
        print(f"После: {processed_text}")
        print(f"Изменений: {stats['total_changes']}")
    
    # Статистика словарей
    print(f"\n📊 Статистика словарей:")
    stats = processor.get_correction_stats()
    for category, count in stats.items():
        print(f"   {category}: {count} правил")


if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Запуск тестов
    test_postprocessor() 