#!/usr/bin/env python3
"""
🏥 Модуль валидации данных для медицинских центров
Автор: Scanovich.ai
Версия: 1.1 - УЛУЧШЕННЫЙ ПОИСК ЧИСЛИТЕЛЬНЫХ

Валидирует извлеченные данные на предмет:
- Медицинской корректности
- Бизнес-логики
- Технической валидности
- Подозрительных значений

НОВОЕ v1.1:
- Поиск числительных прописью ("девяносто пять" = 95)
- Умный поиск цен с тысячами ("одиннадцать тысяч" = 11000)
- Контекстуальная валидация (поиск рядом с ключевыми словами)
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path

# Настройка логирования
log_dir = Path("output/logs")
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'data_validator.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class NumberConverter:
    """Конвертер числительных из текста в цифры"""
    
    def __init__(self):
        # Словарь числительных для веса (кг)
        self.weight_numbers = {
            "тридцать": 30, "сорок": 40, "пятьдесят": 50, "шестьдесят": 60,
            "семьдесят": 70, "восемьдесят": 80, "девяносто": 90,
            "тридцать пять": 35, "сорок пять": 45, "пятьдесят пять": 55,
            "шестьдесят пять": 65, "семьдесят пять": 75, "восемьдесят пять": 85,
            "девяносто пять": 95, "девяноста пять": 95, "девяносто два": 92,
            "девяносто три": 93, "девяносто четыре": 94, "девяносто шесть": 96,
            "девяносто семь": 97, "девяносто восемь": 98, "девяносто девять": 99,
            "сто": 100, "сто пять": 105, "сто десять": 110, "сто двадцать": 120
        }
        
        # Словарь числительных для цен (тысячи рублей)
        self.price_numbers = {
            "три тысячи": 3000, "четыре тысячи": 4000, "пять тысяч": 5000,
            "шесть тысяч": 6000, "семь тысяч": 7000, "восемь тысяч": 8000,
            "девять тысяч": 9000, "десять тысяч": 10000, "одиннадцать тысяч": 11000,
            "двенадцать тысяч": 12000, "тринадцать тысяч": 13000, 
            "четырнадцать тысяч": 14000, "пятнадцать тысяч": 15000,
            "шестнадцать тысяч": 16000, "семнадцать тысяч": 17000,
            "восемнадцать тысяч": 18000, "девятнадцать тысяч": 19000,
            "двадцать тысяч": 20000, "двадцать одна тысяча": 21000,
            "двадцать две тысячи": 22000, "двадцать три тысячи": 23000,
            "двадцать пять тысяч": 25000, "тридцать тысяч": 30000,
            # ДОБАВЛЕНЫ ВАРИАНТЫ С ЦИФРАМИ (критично!)
            "3 тысячи": 3000, "4 тысячи": 4000, "5 тысяч": 5000,
            "6 тысяч": 6000, "7 тысяч": 7000, "8 тысяч": 8000,
            "9 тысяч": 9000, "10 тысяч": 10000, "11 тысяч": 11000,
            "12 тысяч": 12000, "13 тысяч": 13000, "14 тысяч": 14000,
            "15 тысяч": 15000, "16 тысяч": 16000, "17 тысяч": 17000,
            "18 тысяч": 18000, "19 тысяч": 19000, "20 тысяч": 20000,
            "21 тысяча": 21000, "22 тысячи": 22000, "23 тысячи": 23000,
            "25 тысяч": 25000, "30 тысяч": 30000
        }
        
    def find_weight_in_text(self, target_weight: int, text: str) -> Optional[str]:
        """Поиск веса в тексте (цифрами или прописью)"""
        text_lower = text.lower()
        
        # 1. Поиск точного числа (улучшенные паттерны)
        weight_patterns = [
            rf'\b{target_weight}[.,]?\s*(кг|килограмм|килограмма)',  # "80 кг" или "80."
            rf'вес[:\s]*{target_weight}[.,]?',                       # "вес 80."
            rf'{target_weight}[.,]?[:\s]*кг',                        # "80. кг"
            rf'весу?\s*{target_weight}[.,]?',                        # "вес 80."
            rf'{target_weight}[.,]?\s*килограмм',                    # "80. килограмм"
            rf'\b{target_weight}[.,]?\b',                            # просто число "80."
        ]
        
        for pattern in weight_patterns:
            match = re.search(pattern, text_lower)
            if match:
                return match.group(0)
        
        # 2. Поиск прописью
        for text_number, number_value in self.weight_numbers.items():
            if number_value == target_weight:
                # Ищем это числительное в контексте веса
                weight_context_patterns = [
                    rf'{text_number}\s*(кг|килограмм)',
                    rf'вес[:\s]*{text_number}',
                    rf'весу?\s*{text_number}',
                    rf'{text_number}\s*килограмм'
                ]
                
                for pattern in weight_context_patterns:
                    match = re.search(pattern, text_lower)
                    if match:
                        return f"{match.group(0)} (={target_weight})"
                        
                # Даже просто найти числительное
                if text_number in text_lower:
                    return f"найдено '{text_number}' (={target_weight})"
        
        return None
    
    def find_price_in_text(self, target_price: int, text: str) -> Optional[str]:
        """Поиск цены в тексте (цифрами или прописью)"""
        text_lower = text.lower()
        
        # 1. Поиск точного числа (улучшенные паттерны)
        price_patterns = [
            rf'\b{target_price}[.,]?\s*(руб|рубл|тысяч)',    # "11500 руб" или "11500."
            rf'стоимость[:\s]*{target_price}[.,]?',          # "стоимость 11500."
            rf'цена[:\s]*{target_price}[.,]?',               # "цена 11500."
            rf'{target_price}[.,]?[:\s]*руб',                # "11500. руб"
            rf'стоит[:\s]*{target_price}[.,]?',              # "стоит 11500."
            rf'будет\s*{target_price}[.,]?',                 # "будет 11500."
            rf'\b{target_price}[.,]?\b',                     # просто число "11500."
        ]
        
        # 2. Поиск с пробелами (11 500 вместо 11500)
        if target_price >= 1000:
            thousands = target_price // 1000
            hundreds = target_price % 1000
            spaced_price = f"{thousands}\\s+{hundreds:03d}"  # "11 500"
            price_patterns.append(rf'\b{spaced_price}[.,]?\s*(руб|рубл)?')
            
            # Без ведущих нулей
            if hundreds > 0:
                spaced_price_short = f"{thousands}\\s+{hundreds}"  # "11 500"
                price_patterns.append(rf'\b{spaced_price_short}[.,]?\s*(руб|рубл)?')
        
        for pattern in price_patterns:
            match = re.search(pattern, text_lower)
            if match:
                return match.group(0)
        
        # 2. Поиск прописью
        for text_number, number_value in self.price_numbers.items():
            if number_value == target_price:
                # Ищем это числительное в контексте цены
                price_context_patterns = [
                    rf'{text_number}\s*(руб|рубл)',
                    rf'стоимость[:\s]*{text_number}',
                    rf'цена[:\s]*{text_number}',
                    rf'стоит[:\s]*{text_number}'
                ]
                
                for pattern in price_context_patterns:
                    match = re.search(pattern, text_lower)
                    if match:
                        return f"{match.group(0)} (={target_price})"
                        
                # Даже просто найти числительное
                if text_number in text_lower:
                    return f"найдено '{text_number}' (={target_price})"
        
        return None


class ValidationResult:
    """Результат валидации одного поля"""
    
    def __init__(self, field_name: str, value: Any, is_valid: bool = True, 
                 confidence: float = 1.0, warnings: List[str] = None, 
                 source_quote: str = None):
        self.field_name = field_name
        self.value = value
        self.is_valid = is_valid
        self.confidence = confidence
        self.warnings = warnings or []
        self.source_quote = source_quote
        self.severity = "ok" if is_valid else "error"
        
    def add_warning(self, message: str, severity: str = "warning"):
        """Добавить предупреждение"""
        self.warnings.append(message)
        if severity == "error":
            self.is_valid = False
            self.severity = "error"
        elif severity == "warning" and self.severity == "ok":
            self.severity = "warning"


class DataValidator:
    """
    Валидатор данных для медицинского проекта
    
    Проверяет:
    - Персональные данные (ФИО, телефон, возраст, вес)
    - Медицинские данные (симптомы, исследования)
    - Коммерческие данные (цены, даты)
    - Бизнес-логику (соответствие данных друг другу)
    """
    
    def __init__(self):
        logger.info("🛡️ Инициализация валидатора данных v1.1")
        
        # Инициализация конвертера числительных
        self.number_converter = NumberConverter()
        
        # Справочники для валидации
        self.mri_services = {
            "головной мозг": {"min_price": 8000, "max_price": 15000},
            "позвоночник": {"min_price": 4000, "max_price": 8000},
            "сосуды": {"min_price": 8000, "max_price": 15000},
            "суставы": {"min_price": 6000, "max_price": 12000},
            "брюшная полость": {"min_price": 8000, "max_price": 15000}
        }
        
        self.phone_patterns = [
            r'^(\+7|8)[\s\-]?\(?9\d{2}\)?\s?\-?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}$',
            r'^(\+7|8)[\s\-]?\(?8\d{2}\)?\s?\-?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}$'
        ]
        
    def validate_analysis(self, analysis: Dict, transcription: str = "") -> Dict:
        """
        Полная валидация результатов анализа
        
        Args:
            analysis: Результат анализа от LM Studio
            transcription: Оригинальная транскрипция для проверки цитат
            
        Returns:
            Dict с результатами валидации
        """
        logger.info("🔍 Начало валидации извлеченных данных")
        
        validation_results = {}
        business_entities = analysis.get("analysis", {}).get("business_entities", {})
        
        # Валидация персональных данных
        if "client" in business_entities:
            validation_results["personal"] = self._validate_personal_data(
                business_entities["client"], transcription
            )
            
        # Валидация коммерческих данных
        if "pricing" in business_entities:
            validation_results["pricing"] = self._validate_pricing_data(
                business_entities["pricing"], transcription
            )
            
        # Валидация медицинских данных
        if "medical_history" in business_entities:
            validation_results["medical"] = self._validate_medical_data(
                business_entities["medical_history"], transcription
            )
            
        # Валидация записи
        if "appointment" in business_entities:
            validation_results["appointment"] = self._validate_appointment_data(
                business_entities["appointment"], transcription
            )
            
        # Кросс-валидация (проверка логической согласованности)
        validation_results["cross_validation"] = self._cross_validate_data(business_entities)
        
        # Общая статистика
        validation_results["summary"] = self._generate_validation_summary(validation_results)
        
        logger.info(f"✅ Валидация завершена. Найдено проблем: {validation_results['summary']['total_issues']}")
        
        return validation_results
    
    def _validate_personal_data(self, client_data: Dict, transcription: str) -> Dict:
        """Валидация персональных данных"""
        results = {}
        
        # Валидация ФИО
        if "name" in client_data:
            results["name"] = self._validate_name(client_data["name"], transcription)
            
        # Валидация телефона
        if "phone" in client_data:
            results["phone"] = self._validate_phone(client_data["phone"], transcription)
            
        # Валидация возраста
        if "age" in client_data:
            results["age"] = self._validate_age(client_data["age"], transcription)
            
        # Валидация веса
        if "weight" in client_data:
            results["weight"] = self._validate_weight(client_data["weight"], transcription)
            
        # Валидация даты рождения
        if "birth_date" in client_data:
            results["birth_date"] = self._validate_birth_date(client_data["birth_date"], transcription)
            
        return results
    
    def _validate_name(self, name: str, transcription: str) -> ValidationResult:
        """Валидация ФИО"""
        result = ValidationResult("name", name)
        
        if not name or name.strip() == "":
            result.add_warning("ФИО не указано", "error")
            return result
            
        # Проверка на минимальную длину
        if len(name.strip()) < 3:
            result.add_warning("ФИО слишком короткое (менее 3 символов)", "warning")
            result.confidence = 0.3
            
        # Проверка на наличие цифр
        if re.search(r'\d', name):
            result.add_warning("ФИО содержит цифры - возможна ошибка", "warning")
            result.confidence = 0.5
            
        # Проверка на количество слов
        words = name.strip().split()
        if len(words) < 2:
            result.add_warning("ФИО содержит менее 2 слов - возможно неполное", "warning")
            result.confidence = 0.7
        elif len(words) > 4:
            result.add_warning("ФИО содержит более 4 слов - возможна ошибка", "warning")
            result.confidence = 0.6
            
        # Попытка найти источник в транскрипции
        if transcription:
            name_parts = name.lower().split()
            for part in name_parts:
                if len(part) > 2 and part in transcription.lower():
                    result.source_quote = f"Найдено в транскрипции: '{part}'"
                    break
                    
        return result
    
    def _validate_phone(self, phone: str, transcription: str) -> ValidationResult:
        """Валидация телефона"""
        result = ValidationResult("phone", phone)
        
        if not phone or phone.strip() == "":
            result.add_warning("Телефон не указан", "error")
            return result
            
        # Очистка номера от лишних символов
        clean_phone = re.sub(r'[^\d+]', '', phone)
        
        # Проверка на российские форматы
        is_valid_format = False
        for pattern in self.phone_patterns:
            if re.match(pattern, phone):
                is_valid_format = True
                break
                
        if not is_valid_format:
            result.add_warning("Номер телефона не соответствует российскому формату", "warning")
            result.confidence = 0.6
            
        # Проверка длины
        if len(clean_phone) < 10:
            result.add_warning("Номер телефона слишком короткий", "error")
        elif len(clean_phone) > 12:
            result.add_warning("Номер телефона слишком длинный", "warning")
            result.confidence = 0.7
            
        # Проверка на мобильный номер (предпочтительно для записи)
        if not re.search(r'9\d{9}', clean_phone):
            result.add_warning("Не мобильный номер - может быть сложно дозвониться", "warning")
            result.confidence = 0.8
            
        return result
    
    def _validate_age(self, age: int, transcription: str) -> ValidationResult:
        """Валидация возраста"""
        result = ValidationResult("age", age)
        
        if age is None:
            result.add_warning("Возраст не указан", "warning")
            result.confidence = 0.0
            return result
            
        # Проверка разумности возраста
        if age < 0:
            result.add_warning("Отрицательный возраст - ошибка извлечения", "error")
        elif age < 16:
            result.add_warning("Возраст менее 16 лет - требуется согласие родителей", "warning")
            result.confidence = 0.9
        elif age > 120:
            result.add_warning("Возраст более 120 лет - возможна ошибка", "error")
        elif age > 100:
            result.add_warning("Возраст более 100 лет - проверьте корректность", "warning")
            result.confidence = 0.7
            
        return result
    
    def _validate_weight(self, weight: int, transcription: str) -> ValidationResult:
        """Валидация веса - КРИТИЧНО для медицины!"""
        result = ValidationResult("weight", weight)
        
        if weight is None:
            result.add_warning("Вес не указан", "warning")
            result.confidence = 0.0
            return result
            
        # Проверка разумности веса
        if weight < 20:
            result.add_warning("Вес менее 20 кг - возможна ошибка или ребенок", "warning")
            result.confidence = 0.6
        elif weight > 200:
            result.add_warning("Вес более 200 кг - проверьте корректность", "error")
        elif weight > 150:
            result.add_warning("Вес более 150 кг - возможны ограничения МРТ", "warning")
            result.confidence = 0.8
            
        # КРИТИЧНО: Улучшенный поиск веса в транскрипции
        if transcription:
            found_quote = self.number_converter.find_weight_in_text(weight, transcription)
            
            if found_quote:
                result.source_quote = f"Найдено в транскрипции: {found_quote}"
                result.confidence = min(1.0, result.confidence + 0.3)
                logger.info(f"✅ Вес {weight} кг найден: {found_quote}")
            else:
                result.add_warning(
                    f"🚨 КРИТИЧНО: Вес {weight} кг НЕ НАЙДЕН в транскрипции "
                    f"(ни цифрами, ни прописью) - возможна серьезная ошибка!",
                    "error"
                )
                result.confidence = 0.2
                logger.warning(f"❌ Вес {weight} кг НЕ найден в транскрипции")
                
        return result
    
    def _validate_pricing_data(self, pricing_data: Dict, transcription: str) -> Dict:
        """Валидация ценовых данных"""
        results = {}
        
        # Валидация основной стоимости
        if "main_service_cost" in pricing_data:
            results["main_cost"] = self._validate_price(
                pricing_data["main_service_cost"], 
                "основная услуга", 
                transcription
            )
            
        # Валидация общей стоимости
        if "total_mentioned_cost" in pricing_data:
            results["total_cost"] = self._validate_price(
                pricing_data["total_mentioned_cost"], 
                "общая стоимость", 
                transcription
            )
            
        # Валидация видеозаключения
        if "video_conclusion_cost" in pricing_data:
            results["video_cost"] = self._validate_price(
                pricing_data["video_conclusion_cost"], 
                "видеозаключение", 
                transcription,
                min_price=2000,
                max_price=15000
            )
            
        return results
    
    def _validate_price(self, price: int, service_type: str, transcription: str, 
                       min_price: int = 3000, max_price: int = 50000) -> ValidationResult:
        """Валидация цены - КРИТИЧНО для бизнеса!"""
        result = ValidationResult(f"price_{service_type}", price)
        
        if price is None or price == 0:
            result.add_warning(f"Цена за {service_type} не указана", "warning")
            return result
            
        # Проверка разумности для МРТ
        if price < 3000:
            result.add_warning(f"🚨 Цена {price} руб подозрительно низкая для МРТ", "error")
            result.confidence = 0.3
        elif price > 50000:
            result.add_warning(f"Цена {price} руб подозрительно высокая", "warning")
            result.confidence = 0.6
            
        # КРИТИЧНО: Улучшенный поиск цены в транскрипции
        if transcription:
            found_quote = self.number_converter.find_price_in_text(price, transcription)
            
            if found_quote:
                result.source_quote = f"Найдено в транскрипции: {found_quote}"
                result.confidence = min(1.0, result.confidence + 0.3)
                logger.info(f"✅ Цена {price} руб найдена: {found_quote}")
            else:
                result.add_warning(
                    f"🚨 КРИТИЧНО: Цена {price} руб НЕ НАЙДЕНА в транскрипции "
                    f"(ни цифрами, ни прописью) - возможна серьезная ошибка!",
                    "error"
                )
                result.confidence = 0.2
                logger.warning(f"❌ Цена {price} руб НЕ найдена в транскрипции")
                
        return result
    
    def _validate_medical_data(self, medical_data: Dict, transcription: str) -> Dict:
        """Валидация медицинских данных"""
        results = {}
        
        # Валидация симптомов
        if "symptoms" in medical_data:
            results["symptoms"] = self._validate_symptoms(medical_data["symptoms"], transcription)
            
        return results
    
    def _validate_symptoms(self, symptoms: List[str], transcription: str) -> ValidationResult:
        """Валидация симптомов"""
        result = ValidationResult("symptoms", symptoms)
        
        if not symptoms or len(symptoms) == 0:
            result.add_warning("Симптомы не указаны - важно для диагностики", "warning")
            result.confidence = 0.0
            return result
            
        # Проверка на общие симптомы
        common_symptoms = ["боль", "головная боль", "тошнота", "головокружение", "слабость"]
        
        for symptom in symptoms:
            if len(symptom.strip()) < 3:
                result.add_warning(f"Симптом '{symptom}' слишком короткий", "warning")
                result.confidence = 0.7
                
        return result
    
    def _validate_appointment_data(self, appointment_data: Dict, transcription: str) -> Dict:
        """Валидация данных записи"""
        results = {}
        
        # Валидация даты записи
        if "date" in appointment_data:
            results["date"] = self._validate_appointment_date(appointment_data["date"], transcription)
            
        # Валидация времени
        if "time" in appointment_data:
            results["time"] = self._validate_appointment_time(appointment_data["time"], transcription)
            
        return results
    
    def _validate_appointment_date(self, date_str: str, transcription: str) -> ValidationResult:
        """Валидация даты записи"""
        result = ValidationResult("appointment_date", date_str)
        
        if not date_str:
            result.add_warning("Дата записи не указана", "error")
            return result
            
        # Проверка на дату в прошлом (примерная)
        current_date = datetime.now()
        
        # Попытка парсинга различных форматов дат
        date_patterns = [
            r'(\d{1,2})\s*(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)',
            r'(\d{1,2})\.(\d{1,2})\.(\d{4})',
            r'(\d{1,2})\s*(\d{1,2})'
        ]
        
        # Простая проверка на разумность
        if "вчера" in date_str.lower() or "позавчера" in date_str.lower():
            result.add_warning("Дата записи в прошлом - возможна ошибка", "warning")
            result.confidence = 0.3
            
        return result
    
    def _validate_appointment_time(self, time_str: str, transcription: str) -> ValidationResult:
        """Валидация времени записи"""
        result = ValidationResult("appointment_time", time_str)
        
        if not time_str:
            result.add_warning("Время записи не указано", "warning")
            return result
            
        # Проверка формата времени
        time_patterns = [
            r'(\d{1,2}):(\d{2})',
            r'(\d{1,2})\s*(\d{2})',
            r'(\d{1,2})\s*(утра|вечера|дня)'
        ]
        
        is_valid_format = False
        for pattern in time_patterns:
            if re.search(pattern, time_str):
                is_valid_format = True
                break
                
        if not is_valid_format:
            result.add_warning("Неясный формат времени", "warning")
            result.confidence = 0.6
            
        return result
    
    def _validate_birth_date(self, birth_date: str, transcription: str) -> ValidationResult:
        """Валидация даты рождения"""
        result = ValidationResult("birth_date", birth_date)
        
        if not birth_date:
            result.add_warning("Дата рождения не указана", "warning")
            return result
            
        # Проверка на разумность (не в будущем, не более 120 лет назад)
        current_year = datetime.now().year
        
        # Извлечение года из даты рождения
        year_match = re.search(r'19\d{2}|20\d{2}', birth_date)
        if year_match:
            birth_year = int(year_match.group())
            age = current_year - birth_year
            
            if birth_year > current_year:
                result.add_warning("Дата рождения в будущем - ошибка", "error")
            elif age > 120:
                result.add_warning(f"Возраст {age} лет по дате рождения - проверьте", "warning")
                result.confidence = 0.5
            elif age < 0:
                result.add_warning("Отрицательный возраст - ошибка", "error")
                
        return result
    
    def _cross_validate_data(self, business_entities: Dict) -> Dict:
        """Кросс-валидация данных (проверка логической согласованности)"""
        results = {}
        
        client = business_entities.get("client", {})
        pricing = business_entities.get("pricing", {})
        
        # Проверка соответствия возраста и веса
        if "age" in client and "weight" in client:
            age = client["age"]
            weight = client["weight"]
            
            if age and weight:
                if age < 18 and weight > 80:
                    results["age_weight"] = ValidationResult(
                        "age_weight_consistency", 
                        f"Возраст {age}, вес {weight}",
                        is_valid=False
                    )
                    results["age_weight"].add_warning(
                        f"🚨 Несоответствие: возраст {age} лет, вес {weight} кг", 
                        "error"
                    )
                    results["age_weight"].confidence = 0.3
                    
        # Проверка ценовой логики
        if "main_service_cost" in pricing and "total_mentioned_cost" in pricing:
            main_cost = pricing["main_service_cost"]
            total_cost = pricing["total_mentioned_cost"]
            
            if main_cost and total_cost and main_cost > total_cost:
                results["pricing_logic"] = ValidationResult(
                    "pricing_consistency",
                    f"Основная: {main_cost}, Общая: {total_cost}",
                    is_valid=False
                )
                results["pricing_logic"].add_warning(
                    f"Основная услуга ({main_cost} руб) дороже общей стоимости ({total_cost} руб)", 
                    "error"
                )
                
        return results
    
    def _generate_validation_summary(self, validation_results: Dict) -> Dict:
        """Генерация сводки по валидации"""
        summary = {
            "total_fields": 0,
            "valid_fields": 0,
            "warnings": 0,
            "errors": 0,
            "total_issues": 0,
            "average_confidence": 0.0,
            "critical_issues": [],
            "recommendations": []
        }
        
        all_results = []
        
        # Сбор всех результатов валидации
        for category, category_results in validation_results.items():
            if category == "summary":
                continue
                
            if isinstance(category_results, dict):
                for field, result in category_results.items():
                    if isinstance(result, ValidationResult):
                        all_results.append(result)
                        
        # Подсчет статистики
        for result in all_results:
            summary["total_fields"] += 1
            
            if result.is_valid:
                summary["valid_fields"] += 1
            else:
                summary["errors"] += 1
                
            summary["warnings"] += len(result.warnings)
            
            if result.severity == "error":
                summary["critical_issues"].append(f"{result.field_name}: {result.warnings[0] if result.warnings else 'Ошибка'}")
                
        summary["total_issues"] = summary["errors"] + summary["warnings"]
        
        # Средняя уверенность
        if all_results:
            summary["average_confidence"] = sum(r.confidence for r in all_results) / len(all_results)
            
        # Рекомендации
        if summary["errors"] > 0:
            summary["recommendations"].append("🚨 КРИТИЧНО: Исправьте ошибки перед использованием!")
            
        if summary["average_confidence"] < 0.7:
            summary["recommendations"].append("⚠️ Низкая уверенность - нужна ручная проверка")
            
        if summary["warnings"] > 5:
            summary["recommendations"].append("📋 Много предупреждений - проверьте качество транскрипции")
            
        return summary


def validate_analysis_file(analysis_file: Path, transcription_file: Path = None) -> Dict:
    """
    Валидация файла анализа
    
    Args:
        analysis_file: Путь к JSON файлу с анализом
        transcription_file: Путь к файлу транскрипции (опционально)
        
    Returns:
        Dict с результатами валидации
    """
    import json
    
    validator = DataValidator()
    
    # Загрузка анализа
    with open(analysis_file, 'r', encoding='utf-8') as f:
        analysis = json.load(f)
        
    # Загрузка транскрипции (если есть)
    transcription = ""
    if transcription_file and transcription_file.exists():
        with open(transcription_file, 'r', encoding='utf-8') as f:
            transcription = f.read()
            
    # Валидация
    validation_results = validator.validate_analysis(analysis, transcription)
    
    # Сохранение результатов валидации
    validation_file = analysis_file.parent / f"{analysis_file.stem}_validation.json"
    with open(validation_file, 'w', encoding='utf-8') as f:
        # Сериализация результатов валидации
        serializable_results = {}
        for category, results in validation_results.items():
            if category == "summary":
                serializable_results[category] = results
            else:
                serializable_results[category] = {}
                for field, result in results.items():
                    if isinstance(result, ValidationResult):
                        serializable_results[category][field] = {
                            "field_name": result.field_name,
                            "value": result.value,
                            "is_valid": result.is_valid,
                            "confidence": result.confidence,
                            "warnings": result.warnings,
                            "severity": result.severity,
                            "source_quote": result.source_quote
                        }
                    else:
                        serializable_results[category][field] = result
                        
        json.dump(serializable_results, f, ensure_ascii=False, indent=2)
        
    logger.info(f"💾 Результаты валидации сохранены: {validation_file}")
    
    return validation_results


def main():
    """Тестирование валидатора"""
    logger.info("🧪 Тестирование валидатора данных")
    
    # Пример тестовых данных
    test_analysis = {
        "analysis": {
            "business_entities": {
                "client": {
                    "name": "Светлана Хазарусовна",
                    "phone": "+79286154777",
                    "age": 47,
                    "weight": 95
                },
                "pricing": {
                    "main_service_cost": 22000,
                    "total_mentioned_cost": 23000
                }
            }
        }
    }
    
    validator = DataValidator()
    results = validator.validate_analysis(test_analysis)
    
    print("\n📊 РЕЗУЛЬТАТЫ:")
    print(f"Всего полей: {results['summary']['total_fields']}")
    print(f"Ошибок: {results['summary']['errors']}")
    print(f"Предупреждений: {results['summary']['warnings']}")
    print(f"Уверенность: {results['summary']['average_confidence']:.2f}")


if __name__ == "__main__":
    main() 