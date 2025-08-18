#!/usr/bin/env python3
"""
Google Sheets Integration для WhisperX Pipeline v2.0
Автор: Scanovich | Медицинские центры

Система оценки звонков по 20 баллам согласно корпоративному скрипту
"""

import json
import logging
import re
from pathlib import Path
from typing import List, Any, Dict
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

logger = logging.getLogger(__name__)


class GoogleSheetsIntegration:
    """Интеграция с Google Sheets для оценки звонков по 20 баллам (со справедливой оценкой субъективных критериев)"""
    
    def __init__(self, credentials_path: str = "credentials/google_credentials.json", 
                 spreadsheet_url: str = "https://docs.google.com/spreadsheets/d/_JVpERS1v7R5o/edit"):
        """
        Инициализация интеграции с Google Sheets
        
        Args:
            credentials_path: Путь к JSON файлу с credentials от Google Service Account
            spreadsheet_url: URL Google Sheets таблицы
        """
        self.credentials_path = Path(credentials_path)
        self.spreadsheet_url = spreadsheet_url
        self.gc = None
        self.worksheet = None
        
        # 📊 ЭТАЛОННАЯ СТРУКТУРА КОЛОНОК (29 колонок A-AC) - полная структура с справедливой оценкой
        # Источник: https://docs.google.com/spreadsheets/d/-qJ8nCoy-EQ73VJEj27poa/edit
        self.columns = [
            # ОСНОВНАЯ ИНФОРМАЦИЯ (5 колонок)
            "Дата",                                    # A
            "Время звонка",                           # B  
            "Длительность звонка",                    # C
            "Администратор",                          # D
            "Тип звонка",                            # E
            
            # КРИТЕРИИ ОЦЕНКИ СКРИПТА (15 колонок)
            "Приветствие",                           # F
            "Название клиники",                      # G
            "Администратор представилась",           # H
            "Имя пациента",                         # I
            "Блок опроса",                          # J
            "Презентация исследования (что входит)", # K
            "Комплекс предложен",                    # L
            "Цена озвучена",                        # M
            "Соблюдена структура скрипта",          # N
            "Возражение отработано",                 # O
            "ФИО пациента",                         # P
            "Дата рождения",                        # Q
            "Номер телефона",                       # R
            "Дата/время записи",                    # S
            "Адрес клиники",                        # T
            
            # ДОПОЛНИТЕЛЬНЫЕ КРИТЕРИИ (6 колонок)
            "Паспорт и прошлые иссл.",              # U
            "Диск (флешка) озвучен",                # V
            "Видеозаключение предложено",           # W
            "Подготовка озвучена",                  # X
            "Приятный разговор, пациента не перебивала", # Y
            "Улыбка в голосе",                      # Z
            
            # ИТОГОВЫЕ РЕЗУЛЬТАТЫ (3 колонки)
            "Итог",                                 # AA
            "Пациент записался",                    # AB  
            "Комментарии"                           # AC
        ]
    
    def _clean_admin_name(self, admin_name: str) -> str:
        """
        Очистка имени администратора от лишних слов и системных фраз
        
        Проблема: LM  "лидер администратор"
        Решение: Фильтруем шумовые слова, оставляем только реальные имена
        
        Args:
            admin_name: Сырое имя администратора из LM Studio
            
        Returns:
            Очищенное имя или "Не указан" если имя не найдено
        """
        if not admin_name or admin_name.strip() == '':
            return "Не указан"
        
        # 🔧 НОВОЕ v5.0: Обработка LM Studio ошибок типа "не определен"
        problematic_phrases = [
            'не определен', 'не указан', 'не найден', 'не выявлен',
            'отсутствует', 'нет данных', 'неизвестно', 'не установлен'
        ]
        
        admin_lower = admin_name.lower().strip()
        if any(phrase in admin_lower for phrase in problematic_phrases):
            return "Не указан"
        
        # Список слов которые НЕ являются именами администраторов
        noise_words = [
            'администратор', 'админ', 'мрт', 'лидер', 'центр', 
            'диагностики', 'клиника', 'оператор', 'менеджер',
            'добрый', 'день', 'утро', 'вечер', 'помочь', 'служба'
        ]
        
        # Убираем знаки препинания и разбиваем на слова
        cleaned = re.sub(r'[^\w\s]', ' ', admin_name.lower())
        words = cleaned.split()
        
        # Фильтруем шумовые слова
        clean_words = []
        for word in words:
            if len(word) > 1 and not any(noise in word for noise in noise_words):
                clean_words.append(word)
        
        # Если остались слова - берем первое (обычно имя)
        if clean_words:
            return clean_words[0].capitalize()
        
        # Проверяем исходное имя на валидные имена
        original_words = admin_name.split()
        for word in original_words:
            clean_word = re.sub(r'[^\w]', '', word)
            if len(clean_word) >= 3 and clean_word.isalpha():
                # Проверяем что это не шумовое слово
                if not any(noise in clean_word.lower() for noise in noise_words):
                    return clean_word.capitalize()
        
        return "Не указан"

    def _extract_admin_name_from_transcription(self, transcription: str) -> str:
        """
        НОВАЯ v5.0: Умное извлечение имени администратора из транскрипции
        
        Проблема: LM Studio иногда не может связать "администратор" + "Имя" в разных фразах
        Решение: Regex поиск распространенных паттернов представления
        """
        if not transcription:
            return "Не указан"
        
        # Список русских женских имен для администраторов МРТ-центра
        admin_names = [
            'Анна', 'Мария', 'Елена', 'Ольга', 'Татьяна', 'Наталья', 'Ирина', 
            'Светлана', 'Людмила', 'Екатерина', 'Алена', 'Диана',
            'Юлия', 'Валентина', 'Галина', 'Нина', 'Лариса', 'Марина'
        ]
        
        # Паттерны поиска имен администраторов
        patterns = [
            # "администратор Имя"
            r'администратор\s+([А-Яё]+)',
            # "Имя, чем могу помочь" (в начале строки ADMIN)
            r'ADMIN.*?([А-Яё]+),\s*чем\s+могу',
            # "Имя, могу помочь"
            r'ADMIN.*?([А-Яё]+),\s*могу\s+помочь',
            # После "администратор" в следующей строке только имя
            r'администратор[^А-Яё]*?ADMIN.*?([А-Яё]+),',
            # Имя в начале фразы после представления клиники
            r'МРТ[- ]?[Лл]идер[^А-Яё]*?ADMIN.*?([А-Яё]+),',
        ]
        
        # Поиск по паттернам
        for pattern in patterns:
            matches = re.findall(pattern, transcription, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                name = match.strip().capitalize()
                # Проверяем что это действительно женское имя
                if name in admin_names:
                    return name
        
        # Если не нашли точные паттерны - ищем любые женские имена в ADMIN репликах
        admin_lines = re.findall(r'ADMIN:.*', transcription)
        for line in admin_lines[:5]:  # Проверяем только первые 5 строк админа
            for name in admin_names:
                # Ищем имя как отдельное слово с запятой после
                if re.search(rf'\b{name},', line, re.IGNORECASE):
                    return name
        
        return "Не указан"

    def _normalize_phone_number(self, phone: str) -> str:
        """
        Нормализация номера телефона в формат 8-XXX-XXX-XX-XX
        
        Проблемы: "9185798338", "8-918-567-2641", "918-567-26-41"
        Решение: Единый формат с восьмеркой и дефисами
        """
        if not phone or phone.strip() == "":
            return "Не указан"
        
        # Убираем все символы кроме цифр
        digits_only = re.sub(r'\D', '', phone)
        
        # Если номер начинается с 7, заменяем на 8
        if digits_only.startswith('7') and len(digits_only) == 11:
            digits_only = '8' + digits_only[1:]
        
        # Если номер 10 цифр (без 8), добавляем 8
        if len(digits_only) == 10:
            digits_only = '8' + digits_only
        
        # Проверяем что получился 11-значный номер с восьмеркой
        if len(digits_only) == 11 and digits_only.startswith('8'):
            # Форматируем: 8-XXX-XXX-XX-XX
            return f"8-{digits_only[1:4]}-{digits_only[4:7]}-{digits_only[7:9]}-{digits_only[9:11]}"
        
        # Если не удалось нормализовать - возвращаем как есть
        return phone

    def _normalize_birth_date(self, birth_date: str) -> str:
        """
        Нормализация даты рождения в формат DD.MM.YYYY
        
        Проблемы: "1991-08-30", "63-24-12", "06.11.1962"
        Решение: Единый формат DD.MM.YYYY
        """
        if not birth_date or birth_date.strip() == "" or birth_date == "null":
            return "Не указана"
        
        birth_lower = birth_date.lower().strip()
        if any(phrase in birth_lower for phrase in ['не указан', 'не найден', 'отсутствует']):
            return "Не указана"
        
        # Убираем лишние символы, оставляем только цифры и разделители
        cleaned = re.sub(r'[^\d.-]', '', birth_date)
        
        # Паттерны для разных форматов
        patterns = [
            # DD.MM.YYYY или DD-MM-YYYY
            (r'(\d{1,2})[.-](\d{1,2})[.-](\d{4})', lambda m: f"{int(m.group(1)):02d}.{int(m.group(2)):02d}.{m.group(3)}"),
            # YYYY-MM-DD
            (r'(\d{4})[.-](\d{1,2})[.-](\d{1,2})', lambda m: f"{int(m.group(3)):02d}.{int(m.group(2)):02d}.{m.group(1)}"),
            # YY-DD-MM (как "63-24-12")
            (r'(\d{2})[.-](\d{1,2})[.-](\d{1,2})', lambda m: f"{int(m.group(2)):02d}.{int(m.group(3)):02d}.19{m.group(1)}")
        ]
        
        for pattern, formatter in patterns:
            match = re.match(pattern, cleaned)
            if match:
                try:
                    result = formatter(match)
                    # Проверяем разумность даты (год от 1900 до 2023)
                    year = int(result.split('.')[2])
                    if 1900 <= year <= 2023:
                        return result
                except:
                    continue
        
        # Если не удалось распарсить - возвращаем исходное
        return birth_date

    def _parse_appointment_datetime(self, raw_date: str, raw_time: str = "") -> str:
        """
        Парсинг даты/времени записи в единый формат DD.MM.YYYY HH:MM
        
        Проблема: Сырые цитаты "На 13 мая во сколько? ... 15.45", "21 мая 9 утра"
        Решение: Smart парсинг с поддержкой разных форматов
        
        Args:
            raw_date: Сырая дата из LM Studio
            raw_time: Сырое время из LM Studio
            
        Returns:
            Форматированная дата "DD.MM.YYYY HH:MM" или исходный текст
        """
        try:
            # Объединяем дату и время
            combined = f"{raw_date} {raw_time}".strip()
            if not combined:
                return ""
            
            # Словарь месяцев
            months = {
                'января': '01', 'февраля': '02', 'марта': '03', 'апреля': '04',
                'мая': '05', 'июня': '06', 'июля': '07', 'августа': '08',
                'сентября': '09', 'октября': '10', 'ноября': '11', 'декабря': '12'
            }
            
            # Текущий год для дополнения
            current_year = datetime.now().year
            
            # 🔍 ПРОВЕРКА: Уже правильный формат?
            if re.match(r'\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}', combined):
                return combined
            
            # 🔍 ПРОВЕРКА: Отдельные части уже в правильном формате?
            date_match = re.match(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', raw_date)
            time_match = re.match(r'(\d{1,2}):(\d{2})', raw_time)
            
            if date_match and time_match:
                day = int(date_match.group(1))
                month = int(date_match.group(2))
                year = int(date_match.group(3))
                hour = int(time_match.group(1))
                minute = int(time_match.group(2))
                return f"{day:02d}.{month:02d}.{year} {hour:02d}:{minute:02d}"
            
            # Паттерны для извлечения даты и времени
            patterns = [
                # "13 мая ... 15.45" или "13 мая во сколько? ... 15.45"
                r'(\d{1,2})\s+(мая|июня|июля|августа|сентября|октября|ноября|декабря|января|февраля|марта|апреля).*?(\d{1,2})[:\.](\d{2})',
                # "21 мая 9 утра"
                r'(\d{1,2})\s+(мая|июня|июля|августа|сентября|октября|ноября|декабря|января|февраля|марта|апреля)\s+(\d{1,2})\s+утра',
                # "22 мая 12.30"
                r'(\d{1,2})\s+(мая|июня|июля|августа|сентября|октября|ноября|декабря|января|февраля|марта|апреля)\s+(\d{1,2})[:\.](\d{2})',
                # "завтра 22:30" или "на субботу в 20.30"
                r'(?:завтра|субботу|воскресенье|понедельник|вторник|среду|четверг|пятницу).*?(\d{1,2})[:\.](\d{2})',
                # Просто время "22:30" или "20.30"
                r'(\d{1,2})[:\.](\d{2})'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, combined.lower())
                if match:
                    groups = match.groups()
                    
                    if len(groups) == 4:  # День, месяц, час, минута
                        day = int(groups[0])
                        month_name = groups[1]
                        hour = int(groups[2])
                        minute = int(groups[3])
                        month = months.get(month_name, '01')
                        return f"{day:02d}.{month}.{current_year} {hour:02d}:{minute:02d}"
                    
                    elif len(groups) == 3 and 'утра' in combined:  # День, месяц, час утра
                        day = int(groups[0])
                        month_name = groups[1]
                        hour = int(groups[2])
                        month = months.get(month_name, '01')
                        return f"{day:02d}.{month}.{current_year} {hour:02d}:00"
                    
                    elif len(groups) == 2:  # Только час и минута
                        hour = int(groups[0])
                        minute = int(groups[1])
                        # Используем завтрашний день для "завтра"
                        if 'завтра' in combined.lower():
                            tomorrow = datetime.now().date().replace(day=datetime.now().day + 1)
                            return f"{tomorrow.day:02d}.{tomorrow.month:02d}.{tomorrow.year} {hour:02d}:{minute:02d}"
                        else:
                            return f"__.__.{current_year} {hour:02d}:{minute:02d}"
            
            # Если не смогли распарсить - возвращаем как есть
            return combined
            
        except Exception as e:
            logger.warning(f"Ошибка парсинга даты/времени '{raw_date} {raw_time}': {e}")
            return f"{raw_date} {raw_time}".strip()

    def _clean_address(self, address: str) -> str:
        """
        Нормализация адреса клиники в единый формат
        
        Проблема: "адрес Варфоломеева 175А.", "Адрес Курчатова 38"
        Решение: Убираем лишние слова, приводим к формату "Улица, дом"
        
        Args:
            address: Сырой адрес из LM Studio
            
        Returns:
            Нормализованный адрес в формате "Улица, дом"
        """
        if not address or address.strip() == '':
            return ""
        
        # Убираем лишние слова в начале
        cleaned = address.strip()
        cleaned = re.sub(r'^(адрес|адреса?)\s*', '', cleaned, flags=re.IGNORECASE)
        
        # Убираем точки в конце
        cleaned = re.sub(r'\.+$', '', cleaned)
        
        # Убираем лишние пробелы
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # Если нет запятой - пытаемся её добавить между улицей и номером
        if ',' not in cleaned:
            # Паттерн: "Улица номер" -> "Улица, номер"
            match = re.match(r'([А-Яа-я\s]+)\s+(\d+[А-Яа-я]?)$', cleaned)
            if match:
                street = match.group(1).strip()
                number = match.group(2).strip()
                cleaned = f"{street}, {number}"
        
        # Первая буква заглавная
        if cleaned:
            cleaned = cleaned[0].upper() + cleaned[1:]
        
        return cleaned
    
    def setup_credentials(self) -> bool:
        """Настройка подключения к Google Sheets"""
        try:
            if not self.credentials_path.exists():
                logger.error(f"Файл credentials не найден: {self.credentials_path}")
                return False
            
            # Области доступа для Google Sheets API
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Загрузка credentials
            credentials = Credentials.from_service_account_file(
                self.credentials_path, 
                scopes=scopes
            )
            
            # Подключение к Google Sheets
            self.gc = gspread.authorize(credentials)
            
            # Открытие таблицы по URL
            spreadsheet = self.gc.open_by_url(self.spreadsheet_url)
            self.worksheet = spreadsheet.sheet1  # Первый лист
            
            logger.info("✅ Подключение к Google Sheets установлено")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка подключения к Google Sheets: {e}")
            return False
    
    def initialize_headers(self) -> bool:
        """Инициализация заголовков таблицы"""
        try:
            # Проверяем, есть ли уже заголовки
            existing_headers = self.worksheet.row_values(1)
            
            if not existing_headers or existing_headers != self.columns:
                # Устанавливаем заголовки
                self.worksheet.clear()
                self.worksheet.append_row(self.columns)
                
                # Форматирование заголовков
                self.worksheet.format('1:1', {
                    'backgroundColor': {'red': 0.2, 'green': 0.4, 'blue': 0.8},
                    'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
                })
                
                logger.info("✅ Заголовки таблицы инициализированы (система 20 баллов)")
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка инициализации заголовков: {e}")
            return False
    
    def extract_data_from_analysis(self, analysis_file: Path, audio_file: str) -> List[Any]:
        """Извлечение данных из JSON файла анализа для добавления в таблицу"""
        try:
            with open(analysis_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Извлекаем основную информацию
            analysis = data.get('analysis', {})
            audio_duration = data.get('audio_duration', 0)  # Длительность аудио в секундах
            
            # 🔄 НОВАЯ ЛОГИКА v7.0: НЕ ИСПОЛЬЗУЕМ row_ready! 
            # Всегда используем структурированную логику с правильным преобразованием
            logger.info("🔄 Используем структурированную логику вместо row_ready")
            
            # 🔄 FALLBACK: Если row_ready нет - используем старую логику извлечения
            logger.info("⚠️ row_ready не найден, используем старую логику извлечения данных")
            business_entities = analysis.get('business_entities', {})
            script_evaluation = analysis.get('script_evaluation', {})  # Новая секция для 20 баллов
            
            # 🔧 УЛУЧШЕНИЕ v5.0: Проверяем наличие business_entities
            if not business_entities:
                logger.warning(f"⚠️ business_entities отсутствует в {analysis_file.name} - используем backup извлечение")
                # Используем только script_evaluation если есть
                business_entities = {}
            
            # Извлекаем бизнес-сущности
            call_result = business_entities.get('call_result', {})
            personal_info = business_entities.get('personal_info', {})
            commercial_info = business_entities.get('commercial_info', {})
            
            # 🎯 НОВОЕ v5.0: BACKUP извлечение имени администратора из транскрипции
            admin_name_backup = "Не указан"
            corrected_transcription = analysis.get('corrected_transcription', '')
            if corrected_transcription:
                admin_name_backup = self._extract_admin_name_from_transcription(corrected_transcription)
                if admin_name_backup != "Не указан":
                    logger.info(f"🔧 BACKUP: Извлечено имя администратора '{admin_name_backup}' из транскрипции")
            
            # Определяем финальное имя администратора (с умной backup логикой)
            primary_admin_name = personal_info.get('admin_name') or script_evaluation.get('администратор', '')
            
            # Если primary источник содержит проблемные значения - используем backup
            if any(phrase in primary_admin_name.lower() for phrase in ['не определен', 'не указан', 'не найден', '']):
                if admin_name_backup != "Не указан":
                    final_admin_name = admin_name_backup
                    logger.info(f"🔧 BACKUP: Заменили '{primary_admin_name}' на '{admin_name_backup}' из транскрипции")
                else:
                    final_admin_name = primary_admin_name
            else:
                final_admin_name = primary_admin_name
            
            # Очищаем имя администратора
            final_admin_name = self._clean_admin_name(final_admin_name)
            
            # Вычисляем аналитические данные  
            total_score = script_evaluation.get('общая_оценка', 0)
            # Проверяем записался ли клиент (новая логика)
            conversion_status = call_result.get('conversion', '').lower()
            recorded = 1 if 'записался' in conversion_status else 0
            script_compliance_percent = (total_score / 20 * 100) if total_score else 0
            
            # Логика упущенных пациентов
            lost_due_to_script = 0
            not_recorded_good_script = 0
            
            if not recorded:  # Если не записался
                if script_compliance_percent < 70:  # Низкое соблюдение скрипта (меньше 70%)
                    lost_due_to_script = 1
                else:  # Хорошее соблюдение скрипта, но все равно не записался
                    not_recorded_good_script = 1
            
            # Формируем строку данных согласно новой структуре
            row_data = [
                # ОСНОВНАЯ ИНФОРМАЦИЯ О ЗВОНКЕ
                datetime.now().strftime('%d.%m.%Y'),  # Дата
                datetime.now().strftime('%H:%M'),  # Время звонка (время обработки)
                f"{audio_duration/60:.1f} мин",  # Длительность
                final_admin_name,  # Администратор (с backup извлечением)
                
                # БЛОК I: ПРИВЕТСТВИЕ
                script_evaluation.get('приветствие', {}).get('score', 0),
                script_evaluation.get('название_клиники', {}).get('score', 0),
                script_evaluation.get('фио_администратора', {}).get('score', 0),
                script_evaluation.get('имя_пациента', {}).get('score', 0),
                
                # БЛОК II: РАСКРЫВАЮЩИЕ ВОПРОСЫ
                script_evaluation.get('блок_опроса', {}).get('score', 0),
                script_evaluation.get('презентация_исследования', {}).get('score', 0),
                script_evaluation.get('комплекс_предложен', {}).get('score', 0),
                script_evaluation.get('цена_озвучена', {}).get('score', 0),
                
                # БЛОК III: ПРОДАЖА/ЗАПИСЬ
                script_evaluation.get('соблюден_алгоритм', {}).get('score', 0),
                script_evaluation.get('возражение_обработано', {}).get('score', 0),
                script_evaluation.get('структура_скрипта', {}).get('score', 0),
                
                # КОЛОНКИ С КОНКРЕТНЫМИ ДАННЫМИ + ПОСТ-ОБРАБОТКА v5.0 (ЕДИНЫЙ ФОРМАТ!)
                personal_info.get('client_name', ''),  # 15. ФИО клиента (ПОЛНОЕ ИМЯ!)
                self._normalize_birth_date(personal_info.get('birth_date', '')),  # 16. Дата рождения (DD.MM.YYYY)
                self._normalize_phone_number(personal_info.get('phone_number', '')),  # 17. Номер телефона (8-XXX-XXX-XX-XX)
                self._parse_appointment_datetime(
                    commercial_info.get('appointment_date', ''), 
                    commercial_info.get('appointment_time', '')
                ),  # 18. Дата/время записи (единый формат DD.MM.YYYY HH:MM)
                self._clean_address(commercial_info.get('clinic_address', '')),  # 19. Адрес клиники (нормализованный)
                
                # ДОПОЛНИТЕЛЬНЫЕ МЕТРИКИ
                script_evaluation.get('паспорт_документы', {}).get('score', 0),
                script_evaluation.get('диск_озвучен', {}).get('score', 0),
                script_evaluation.get('видеозаключение', {}).get('score', 0),
                script_evaluation.get('подготовка', {}).get('score', 0),
                
                # ИТОГОВЫЕ РЕЗУЛЬТАТЫ
                total_score,  # Общая оценка
                'Да' if recorded else 'Нет',  # Пациент записался
                script_evaluation.get('комментарии', ''),  # Комментарии
                'Записался' if recorded else 'Не записался',  # Итог
                
                # 🚀 НОВАЯ БИЗНЕС-АНАЛИТИКА
                1,  # Входящий звонок (всегда 1)
                recorded,  # Записался (1/0)
                lost_due_to_script,  # Упущен из-за скрипта
                not_recorded_good_script,  # Не записался при соблюдении
                f"{recorded * 100:.1f}%",  # Конверсия % (для одного звонка)
                f"{script_compliance_percent:.1f}%",  # Соблюдение скрипта %
                call_result.get('recommendations', script_evaluation.get('бизнес_анализ', ''))  # Бизнес-анализ ЛЛМ
            ]
            
            return row_data
            
        except Exception as e:
            logger.error(f"Ошибка извлечения данных из {analysis_file}: {e}")
            return []
    
    def add_standardized_data_to_sheet(self, standardized_data: Dict[str, Any], audio_file: str) -> bool:
        """
        🔄 НОВЫЙ МЕТОД v2.1: Добавление унифицированных данных в Google Sheets
        
        Гарантирует:
        - Справедливую оценку администраторов (влияет на премии!)
        - Одинаковые данные в HTML и Google Sheets
        - Все обязательные поля присутствуют
        """
        try:
            if not self.gc or not self.worksheet:
                if not self.setup_credentials():
                    return False
            
            # Инициализируем заголовки если нужно
            if not self.initialize_headers():
                return False
            
            # Извлекаем данные из унифицированной структуры
            row_data = self._extract_from_standardized_data(standardized_data, audio_file)
            
            if not row_data:
                logger.error("Не удалось извлечь данные из унифицированной структуры")
                return False
            
            # Находим следующую пустую строку (после заголовков)
            all_values = self.worksheet.get_all_values()
            next_row = len(all_values) + 1
            
            # 🔧 ЗАЩИТА: Проверяем что row_data соответствует эталонным 29 колонкам
            if len(row_data) != 29:
                logger.error(f"❌ ОШИБКА: row_data содержит {len(row_data)} элементов, ожидается 29!")
                logger.error(f"🔍 Первые 5 элементов: {row_data[:5]}")
                logger.error(f"🔍 Последние 5 элементов: {row_data[-5:]}")
                return False
            
            # Добавляем строку точно в столбцы A-AC (29 колонок)
            range_name = f'A{next_row}:AC{next_row}'
            self.worksheet.update(values=[row_data], range_name=range_name)
            
            # Применяем цветовое форматирование для результата
            last_row = next_row
            
            # Колонка "Пациент записался" (индекс 26 = колонка AA)
            recorded = standardized_data.get('call_result', {}).get('status', '').lower()
            is_recorded = any(word in recorded for word in ['записался', 'записан', 'запись'])
            
            if is_recorded:
                # Зеленый цвет для успешной записи
                self.worksheet.format(f'AA{last_row}', {
                    "backgroundColor": {"red": 0.85, "green": 0.92, "blue": 0.83},
                    "textFormat": {"bold": True}
                })
            else:
                # Красный цвет для неуспешной записи
                self.worksheet.format(f'AA{last_row}', {
                    "backgroundColor": {"red": 0.96, "green": 0.8, "blue": 0.8},
                    "textFormat": {"bold": True}
                })
            
            logger.info(f"✅ Унифицированные данные добавлены в Google Sheets: строка {next_row}")
            logger.info(f"📊 Общая оценка: {standardized_data.get('total_score', 0)}/20")
            logger.info(f"👤 Администратор: {standardized_data.get('personal_info', {}).get('admin_name', 'не указан')}")
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка добавления унифицированных данных в Google Sheets: {e}")
            return False
    
    def _extract_from_standardized_data(self, standardized_data: Dict[str, Any], audio_file: str) -> List[Any]:
        """🔄 Извлечение данных под эталонную структуру (29 колонок A-AC)"""
        
        personal = standardized_data.get('personal_info', {})
        commercial = standardized_data.get('commercial_info', {})
        script = standardized_data.get('script_evaluation', {})
        call_result = standardized_data.get('call_result', {})
        total_score = standardized_data.get('total_score', 0)
        audio_duration = standardized_data.get('audio_duration', 0)
        
        # Определяем записался ли клиент
        status = call_result.get('status', '').lower()
        recorded = any(word in status for word in ['записался', 'записан', 'запись'])
        
        # Конвертируем score (0/1) в текст (Да/Нет) для эталонной структуры
        def score_to_text(score):
            return "Да" if score == 1 else "Нет"
        
        # 📊 ЭТАЛОННАЯ СТРУКТУРА ДАННЫХ (29 колонок)
        row_data = [
            # ОСНОВНАЯ ИНФОРМАЦИЯ (5 колонок A-E)
            datetime.now().strftime('%d.%m.%Y'),                    # A. Дата
            datetime.now().strftime('%H:%M'),                       # B. Время звонка
            f"{int(audio_duration//60)} мин {int(audio_duration%60)} с", # C. Длительность
            personal.get('admin_name', 'не указан'),                # D. Администратор
            "Целевой",                                              # E. Тип звонка
            
            # КРИТЕРИИ ОЦЕНКИ СКРИПТА (15 колонок F-T)
            score_to_text(script.get('приветствие', {}).get('score', 0)),     # F. Приветствие
            score_to_text(script.get('название_клиники', {}).get('score', 0)), # G. Название клиники
            score_to_text(script.get('фио_администратора', {}).get('score', 0)), # H. Админ представилась
            score_to_text(script.get('имя_пациента', {}).get('score', 0)),    # I. Имя пациента
            score_to_text(script.get('блок_опроса', {}).get('score', 0)),     # J. Блок опроса
            score_to_text(script.get('презентация_исследования', {}).get('score', 0)), # K. Презентация
            score_to_text(script.get('комплекс_предложен', {}).get('score', 0)), # L. Комплекс предложен
            score_to_text(script.get('цена_озвучена', {}).get('score', 0)),   # M. Цена озвучена
            score_to_text(script.get('структура_скрипта', {}).get('score', 0)), # N. Структура скрипта
            score_to_text(script.get('возражение_обработано', {}).get('score', 0)), # O. Возражение
            score_to_text(script.get('фио_записано', {}).get('score', 0)),    # P. ФИО пациента
            score_to_text(script.get('дата_рождения', {}).get('score', 0)),   # Q. Дата рождения
            score_to_text(script.get('номер_телефона', {}).get('score', 0)),  # R. Номер телефона
            score_to_text(script.get('дата_время_записи', {}).get('score', 0)), # S. Дата/время записи
            score_to_text(script.get('адрес_клиники', {}).get('score', 0)),   # T. Адрес клиники
            
            # ДОПОЛНИТЕЛЬНЫЕ КРИТЕРИИ (6 колонок U-Z)
            score_to_text(script.get('паспорт_документы', {}).get('score', 0)), # U. Паспорт и прошлые иссл.
            score_to_text(script.get('диск_озвучен', {}).get('score', 0)),    # V. Диск озвучен
            score_to_text(script.get('видеозаключение', {}).get('score', 0)), # W. Видеозаключение
            score_to_text(script.get('подготовка', {}).get('score', 0)),      # X. Подготовка
            score_to_text(script.get('вежливость', {}).get('score', 1)),      # Y. Приятный разговор
            score_to_text(script.get('профессионализм', {}).get('score', 1)), # Z. Улыбка в голосе
            
            # ИТОГОВЫЕ РЕЗУЛЬТАТЫ (3 колонки AA-AC)
            f"записался на {commercial.get('main_service', 'услугу')} по стоимости {commercial.get('total_cost', commercial.get('main_cost', 'неизвестно'))}" if recorded else "не записался", # AA. Итог
            "да" if recorded else "нет",                           # AB. Пациент записался
            self._generate_enhanced_comments(script, standardized_data, total_score, recorded) # AC. Комментарии
        ]
        
        return row_data
    
    def _generate_enhanced_comments(self, script_evaluation: Dict[str, Any], standardized_data: Dict[str, Any], total_score: int, recorded: bool) -> str:
        """🔍 РАСШИРЕННАЯ ГЕНЕРАЦИЯ КОММЕНТАРИЕВ С АНАЛИЗОМ НЕЙРОСЕТИ"""
        
        comments_sections = []
        
        # 1. УБИРАЕМ ОБЩИЕ ОЦЕНКИ - ТОЛЬКО КОНКРЕТНЫЕ ПРОБЛЕМЫ
        # (Общие фразы типа "отличная работа" не нужны)
        
        # 2. АНАЛИЗ ТОЛЬКО НЕСОБЛЮДЕННЫХ КРИТЕРИЕВ (соблюденные не упоминаем)
        problems = []
        
        for criterion, data in script_evaluation.items():
            if isinstance(data, dict) and 'score' in data:
                score = data.get('score', 0)
                comment = data.get('comment', '')
                
                # ПОКАЗЫВАЕМ ТОЛЬКО ПРОБЛЕМЫ (score = 0)
                if score == 0 and comment:
                    problems.append(comment)
        
        # Добавляем проблемы если есть
        if problems:
            comments_sections.append(f"НЕДОЧЕТЫ: {' | '.join(problems)}")
        
        # 3. АНАЛИЗ ИИ ИЗ JSON (комментарии нейросети)
        original_comment = script_evaluation.get('комментарии', '')
        if original_comment and len(original_comment) > 20:
            comments_sections.append(f"АНАЛИЗ ИИ: {original_comment}")
        
        # 4. БИЗНЕС-АНАЛИЗ И РЕКОМЕНДАЦИИ ИЗ JSON
        business_analysis = script_evaluation.get('бизнес_анализ', '')
        if business_analysis and len(business_analysis) > 20:
            # Ограничиваем длину для читаемости
            if len(business_analysis) > 400:
                business_analysis = business_analysis[:400] + "..."
            comments_sections.append(f"РЕКОМЕНДАЦИИ: {business_analysis}")
        
        # 5. СУБЪЕКТИВНЫЕ КРИТЕРИИ НЕ КОММЕНТИРУЕМ (невозможно объективно оценить по тексту)
        # Убираем из комментариев "Приятный разговор" и "Улыбка в голосе" 
        # так как они не могут быть объективно оценены из-за ошибок транскрипции/диаризации
        
        # Объединяем все секции
        if comments_sections:
            final_comment = " ║ ".join(comments_sections)
        else:
            # Если нет проблем и нет анализа ИИ - возвращаем пустой комментарий
            final_comment = ""
        
        # Ограничиваем итоговую длину комментария 
        if len(final_comment) > 1500:
            final_comment = final_comment[:1450] + "... [обрезано]"
        
        return final_comment

    def add_analysis_to_sheet(self, analysis_file: Path, audio_file: str) -> bool:
        """Добавление результатов анализа в Google Sheets"""
        try:
            if not self.gc or not self.worksheet:
                if not self.setup_credentials():
                    return False
            
            # Инициализируем заголовки если нужно
            if not self.initialize_headers():
                return False
            
            # Извлекаем данные для добавления
            row_data = self.extract_data_from_analysis(analysis_file, audio_file)
            
            if not row_data:
                logger.error("Не удалось извлечь данные для добавления в таблицу")
                return False
            
            # Находим следующую пустую строку (после заголовков)
            all_values = self.worksheet.get_all_values()
            next_row = len(all_values) + 1
            
            # 🔧 ЗАЩИТА: Проверяем что row_data соответствует эталонным 29 колонкам
            if len(row_data) != 29:
                logger.error(f"❌ ОШИБКА: row_data содержит {len(row_data)} элементов, ожидается 29!")
                logger.error(f"🔍 Первые 5 элементов: {row_data[:5]}")
                logger.error(f"🔍 Последние 5 элементов: {row_data[-5:]}")
                return False
            
            # Добавляем строку точно в столбцы A-AC (29 колонок)
            range_name = f'A{next_row}:AC{next_row}'
            self.worksheet.update(values=[row_data], range_name=range_name)
            
            # Применяем цветовое форматирование для результата (если используется старый метод)
            last_row = next_row
            
            # Колонка "Пациент записался" (индекс 26 = колонка AA)
            result_cell = f"AA{last_row}"  
            
            if len(row_data) > 26 and row_data[26] == 'да':  # Записался (эталонная структура)
                # Зеленый для успешных записей
                self.worksheet.format(result_cell, {
                    'backgroundColor': {'red': 0.8, 'green': 1, 'blue': 0.8}
                })
            else:
                # Красный для неуспешных
                self.worksheet.format(result_cell, {
                    'backgroundColor': {'red': 1, 'green': 0.8, 'blue': 0.8}
                })
            
            # Дополнительное форматирование для аналитических колонок
            if row_data[30]:  # Упущен из-за скрипта
                # Оранжевый для упущенных из-за скрипта (индекс 30 = колонка AE)
                lost_cell = f"AE{last_row}"
                self.worksheet.format(lost_cell, {
                    'backgroundColor': {'red': 1, 'green': 0.8, 'blue': 0.6}
                })
            
            # Форматирование соблюдения скрипта (индекс 33 = колонка AH)
            script_percent = float(row_data[33].replace('%', ''))
            script_cell = f"AH{last_row}"
            
            if script_percent >= 80:  # Хорошее соблюдение (80%+)
                self.worksheet.format(script_cell, {
                    'backgroundColor': {'red': 0.8, 'green': 1, 'blue': 0.8}
                })
            elif script_percent >= 60:  # Среднее соблюдение (60-79%)
                self.worksheet.format(script_cell, {
                    'backgroundColor': {'red': 1, 'green': 1, 'blue': 0.8}
                })
            else:  # Низкое соблюдение (<60%)
                self.worksheet.format(script_cell, {
                    'backgroundColor': {'red': 1, 'green': 0.8, 'blue': 0.8}
                })
            
            logger.info(f"✅ Данные добавлены в Google Sheets: строка {last_row}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка добавления в Google Sheets: {e}")
            return False
    
    def batch_import_from_directory(self, output_dir: Path) -> int:
        """Массовый импорт всех анализов из директории"""
        enhanced_dir = output_dir / "enhanced"
        
        if not enhanced_dir.exists():
            logger.error(f"Директория с анализами не найдена: {enhanced_dir}")
            return 0
        
        imported_count = 0
        
        for analysis_file in enhanced_dir.glob("*_unified_analysis.json"):
            # Определяем имя аудио файла из имени JSON файла
            audio_name = analysis_file.stem.replace("_unified_analysis", "") + ".mp3"
            
            if self.add_analysis_to_sheet(analysis_file, audio_name):
                imported_count += 1
                logger.info(f"✅ Импортирован: {audio_name}")
            else:
                logger.error(f"❌ Ошибка импорта: {audio_name}")
        
        logger.info(f"🎉 Импортировано {imported_count} анализов в Google Sheets")
        return imported_count



def setup_google_integration():
    """Настройка Google Sheets интеграции"""
    print("🔧 НАСТРОЙКА GOOGLE SHEETS ИНТЕГРАЦИИ v2.0")
    print("=" * 50)
    
    # Создаем папку для credentials
    credentials_dir = Path("credentials")
    credentials_dir.mkdir(exist_ok=True)
    
    credentials_file = credentials_dir / "google_credentials.json"
    
    if not credentials_file.exists():
        print(f"""
📋 ИНСТРУКЦИЯ ПО НАСТРОЙКЕ:

1. Перейдите в Google Cloud Console: https://console.cloud.google.com/
2. Создайте новый проект или выберите существующий
3. Включите Google Sheets API и Google Drive API
4. Создайте Service Account:
   - IAM & Admin > Service Accounts > Create Service Account
   - Скачайте JSON ключ
5. Сохраните JSON файл как: {credentials_file}
6. Предоставьте доступ к таблице:
   - Откройте вашу Google Sheets таблицу
   - Нажмите "Поделиться"
   - Добавьте email: scanovich-mri-leader@mythical-legend-457913-t6.iam.gserviceaccount.com
   - Дайте права "Редактор"

📊 НОВАЯ ТАБЛИЦА: https://docs.google.com/spreadsheets/d/1Fh7K3shckBk19XOlYMcTmqbck42Jys_JVpERS1v7R5o/edit
🎯 СИСТЕМА ОЦЕНКИ: 20 баллов по корпоративному скрипту
        """)
        return False
    
    return True


def test_single_file():
    """Тестирование одного файла анализа"""
    print("🧪 ТЕСТИРОВАНИЕ GOOGLE SHEETS ИНТЕГРАЦИИ")
    print("=" * 50)
    
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    integration = GoogleSheetsIntegration()
    
    # Проверяем подключение
    if not integration.setup_credentials():
        print("❌ Ошибка подключения к Google Sheets")
        return False
    
    # Находим тестовый файл
    test_file = Path("output/enhanced/[2025-05-08][12-22-22] вызов с 79166809864 на 78632850803_unified_analysis.json")
    
    if not test_file.exists():
        print(f"❌ Тестовый файл не найден: {test_file}")
        return False
    
    print(f"📁 Тестовый файл: {test_file.name}")
    
    # Извлекаем и показываем данные
    row_data = integration.extract_data_from_analysis(test_file, "test.mp3")
    
    if not row_data:
        print("❌ Не удалось извлечь данные")
        return False
    
    print(f"📊 Извлечено {len(row_data)} элементов данных (ожидается 29 для A-AC)")
    print(f"📊 Ожидается {len(integration.columns)} колонок")
    
    # 🔧 ОТЛАДКА: Проверяем размер row_data
    if len(row_data) != 29:
        print(f"⚠️ ВНИМАНИЕ: row_data содержит {len(row_data)} элементов вместо 29!")
    
    # Показываем соответствие данных заголовкам
    print("\n🔍 СООТВЕТСТВИЕ ДАННЫХ ЗАГОЛОВКАМ:")
    for i, (header, data) in enumerate(zip(integration.columns, row_data)):
        print(f"{i:2d}. {header:30} = {str(data)[:50]}")
    
    # Добавляем в таблицу
    if integration.add_analysis_to_sheet(test_file, "test.mp3"):
        print("✅ Данные успешно добавлены в Google Sheets!")
        return True
    else:
        print("❌ Ошибка добавления в Google Sheets")
        return False


if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        # Тестирование одного файла
        test_single_file()
    else:
        # Запуск настройки
        if setup_google_integration():
            # Тестирование интеграции
            integration = GoogleSheetsIntegration()
            
            if integration.setup_credentials():
                print("✅ Google Sheets интеграция v2.0 настроена успешно!")
                
                # Импорт существующих анализов
                output_dir = Path("output")
                if output_dir.exists():
                    count = integration.batch_import_from_directory(output_dir)
                    print(f"📊 Импортировано {count} анализов")
            else:
                print("❌ Ошибка настройки Google Sheets") 
