#!/usr/bin/env python3
"""
🔄 UNIFIED DATA EXTRACTOR v1.0 для единой обработки данных
Автор: Scanovich.ai | Версия: 1.0

КРИТИЧЕСКАЯ ЗАДАЧА: Обеспечить справедливую оценку администраторов!
От стабильности этой системы зависят премии и депремирование сотрудников.

ОСНОВНЫЕ ФУНКЦИИ:
- Единая точка извлечения данных из LLM анализа
- Обязательная валидация структуры данных
- Стандартизированные fallback значения
- Гарантированная консистентность для HTML и Google Sheets
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

logger = logging.getLogger(__name__)


class UnifiedDataExtractor:
    """
    🏥 Единый экстрактор данных для обеспечения справедливой оценки администраторов
    
    КРИТИЧЕСКИ ВАЖНО:
    - Гарантирует одинаковую структуру данных для HTML и Google Sheets
    - Предотвращает случайные потери данных (weight, admin_name)
    - Обеспечивает справедливую оценку → корректные премии
    """
    
    def __init__(self):
        """Инициализация экстрактора с обязательными полями"""
        
        # 📋 ОБЯЗАТЕЛЬНЫЕ ПОЛЯ PERSONAL_INFO
        self.required_personal_fields = {
            'client_name': str,
            'phone_number': str, 
            'birth_date': (str, type(None)),
            'weight': (str, type(None)),
            'admin_name': (str, type(None))
        }
        
        # 📋 ОБЯЗАТЕЛЬНЫЕ ПОЛЯ COMMERCIAL_INFO
        self.required_commercial_fields = {
            'main_service': (str, type(None)),
            'main_cost': (str, type(None)),
            'total_cost': (str, type(None)),
            'appointment_date': (str, type(None)),
            'appointment_time': (str, type(None)),
            'clinic_address': (str, type(None)),
            'doctor_name': (str, type(None))
        }
        
        # 📋 СТАНДАРТИЗИРОВАННЫЕ FALLBACK ЗНАЧЕНИЯ
        self.fallback_values = {
            'personal_info': {
                'client_name': 'не указано',
                'phone_number': 'не указан',
                'birth_date': 'не указана',
                'weight': 'не указан',
                'admin_name': 'не указан'
            },
            'commercial_info': {
                'main_service': 'не указана',
                'main_cost': 'не указана',
                'total_cost': 'не указана',
                'appointment_date': 'не указана',
                'appointment_time': 'не указано',
                'clinic_address': 'не указан',
                'doctor_name': 'не указан'
            }
        }
        
        # 📊 ОБЯЗАТЕЛЬНЫЕ ПОЛЯ SCRIPT_EVALUATION (20 критериев) ✅
        self.required_script_criteria = [
            # ОСНОВНЫЕ КРИТЕРИИ СКРИПТА (15 критериев F-T)
            'приветствие', 'название_клиники', 'фио_администратора', 'имя_пациента',
            'блок_опроса', 'презентация_исследования', 'комплекс_предложен', 'цена_озвучена',
            'соблюден_алгоритм', 'возражение_обработано', 
            'фио_записано', 'дата_рождения', 'номер_телефона', 'дата_время_записи', 'адрес_клиники',
            
            # ДОПОЛНИТЕЛЬНЫЕ КРИТЕРИИ (5 критериев U-Y) - ОБЪЕКТИВНО ПРОВЕРЯЕМЫЕ
            'паспорт_документы', 'диск_озвучен', 'подготовка', 'вежливость', 'профессионализм'
        ]
    
    def extract_standardized_data(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        🎯 ГЛАВНАЯ ФУНКЦИЯ: Извлечение и стандартизация данных из LLM анализа
        
        Гарантирует:
        - Все обязательные поля присутствуют
        - Корректные типы данных
        - Одинаковую структуру для HTML и Google Sheets
        - Справедливую оценку администраторов
        """
        try:
            logger.info("🔄 Начало стандартизации данных...")
            
            # Извлекаем основной анализ
            analysis = analysis_result.get('analysis', {})
            if not analysis:
                raise ValueError("Отсутствует секция 'analysis' в результатах LLM")
            
            business_entities = analysis.get('business_entities', {})
            script_evaluation = analysis.get('script_evaluation', {})
            
            # 1. ВАЛИДАЦИЯ И СТАНДАРТИЗАЦИЯ PERSONAL_INFO
            personal_info = self._validate_and_fix_personal_info(
                business_entities.get('personal_info', {})
            )
            
            # 2. ВАЛИДАЦИЯ И СТАНДАРТИЗАЦИЯ COMMERCIAL_INFO
            commercial_info = self._validate_and_fix_commercial_info(
                business_entities.get('commercial_info', {})
            )
            
            # 3. ВАЛИДАЦИЯ И СТАНДАРТИЗАЦИЯ SCRIPT_EVALUATION
            script_evaluation = self._validate_and_fix_script_evaluation(script_evaluation)
            
            # 4. ИЗВЛЕЧЕНИЕ CALL_RESULT
            call_result = business_entities.get('call_result', {})
            
            # 5. РАСЧЕТ ОБЩЕЙ ОЦЕНКИ (критически важно!)
            total_score = self._calculate_total_score(script_evaluation)
            
            # 6. СОЗДАНИЕ СТАНДАРТИЗИРОВАННОЙ СТРУКТУРЫ
            standardized_data = {
                'personal_info': personal_info,
                'commercial_info': commercial_info, 
                'script_evaluation': script_evaluation,
                'call_result': call_result,
                'total_score': total_score,
                'audio_duration': analysis_result.get('audio_duration', 0),
                'corrected_transcription': analysis_result.get('corrected_transcription', ''),
                'validation_summary': {
                    'personal_fields_fixed': len([k for k, v in personal_info.items() if v == self.fallback_values['personal_info'].get(k)]),
                    'commercial_fields_fixed': len([k for k, v in commercial_info.items() if v == self.fallback_values['commercial_info'].get(k)]),
                    'script_criteria_count': len(script_evaluation),
                    'total_score_verified': total_score
                }
            }
            
            logger.info(f"✅ Стандартизация завершена. Общая оценка: {total_score}/20")
            logger.info(f"🔧 Исправлено полей: personal={standardized_data['validation_summary']['personal_fields_fixed']}, commercial={standardized_data['validation_summary']['commercial_fields_fixed']}")
            
            return standardized_data
            
        except Exception as e:
            logger.error(f"❌ Ошибка стандартизации данных: {e}")
            return self._create_emergency_fallback_data(analysis_result)
    
    def _validate_and_fix_personal_info(self, personal_info: Dict[str, Any]) -> Dict[str, Any]:
        """🔧 Валидация и исправление персональной информации"""
        
        fixed_info = {}
        fixes_count = 0
        
        for field, expected_type in self.required_personal_fields.items():
            value = personal_info.get(field)
            
            # Проверяем наличие и тип
            if value is None or (isinstance(expected_type, tuple) and type(value) not in expected_type) or (not isinstance(expected_type, tuple) and not isinstance(value, expected_type)):
                fixed_info[field] = self.fallback_values['personal_info'][field]
                fixes_count += 1
                logger.warning(f"🔧 Исправлено поле '{field}': {value} → {fixed_info[field]}")
            else:
                # Дополнительная очистка строк
                if isinstance(value, str):
                    value = value.strip()
                    if not value:  # Пустая строка
                        fixed_info[field] = self.fallback_values['personal_info'][field]
                        fixes_count += 1
                    else:
                        fixed_info[field] = value
                else:
                    fixed_info[field] = value
        
        if fixes_count > 0:
            logger.warning(f"⚠️ Personal info: исправлено {fixes_count} полей из {len(self.required_personal_fields)}")
        
        return fixed_info
    
    def _validate_and_fix_commercial_info(self, commercial_info: Dict[str, Any]) -> Dict[str, Any]:
        """🔧 Валидация и исправление коммерческой информации"""
        
        fixed_info = {}
        fixes_count = 0
        
        for field, expected_type in self.required_commercial_fields.items():
            value = commercial_info.get(field)
            
            # Проверяем наличие и тип
            if value is None or (isinstance(expected_type, tuple) and type(value) not in expected_type) or (not isinstance(expected_type, tuple) and not isinstance(value, expected_type)):
                fixed_info[field] = self.fallback_values['commercial_info'][field]
                fixes_count += 1
                logger.warning(f"🔧 Исправлено поле '{field}': {value} → {fixed_info[field]}")
            else:
                # Дополнительная очистка строк
                if isinstance(value, str):
                    value = value.strip()
                    if not value:  # Пустая строка
                        fixed_info[field] = self.fallback_values['commercial_info'][field]
                        fixes_count += 1
                    else:
                        fixed_info[field] = value
                else:
                    fixed_info[field] = value
        
        if fixes_count > 0:
            logger.warning(f"⚠️ Commercial info: исправлено {fixes_count} полей из {len(self.required_commercial_fields)}")
        
        return fixed_info
    
    def _validate_and_fix_script_evaluation(self, script_evaluation: Dict[str, Any]) -> Dict[str, Any]:
        """🔧 Валидация и исправление оценки скрипта (критически важно для премий!)"""
        
        fixed_evaluation = {}
        
        for criterion in self.required_script_criteria:
            criterion_data = script_evaluation.get(criterion, {})
            
            if not isinstance(criterion_data, dict):
                # Некорректная структура - создаем fallback
                fixed_evaluation[criterion] = {
                    'score': 0,
                    'comment': f'Данные отсутствуют - требует проверки администратора'
                }
                logger.warning(f"⚠️ Критерий '{criterion}': создан fallback с score=0")
            else:
                # Проверяем score
                score = criterion_data.get('score', 0)
                if not isinstance(score, (int, float)) or score not in [0, 1]:
                    score = 0
                    logger.warning(f"⚠️ Критерий '{criterion}': некорректный score, установлен 0")
                
                # Проверяем comment
                comment = criterion_data.get('comment', '')
                if not isinstance(comment, str):
                    comment = 'Комментарий отсутствует'
                
                fixed_evaluation[criterion] = {
                    'score': int(score),
                    'comment': comment
                }
        
        return fixed_evaluation
    
    def _calculate_total_score(self, script_evaluation: Dict[str, Any]) -> int:
        """📊 Точный расчет общей оценки (критически важно для премий!)"""
        
        total = 0
        criteria_count = 0
        
        for criterion, data in script_evaluation.items():
            if isinstance(data, dict) and 'score' in data:
                score = data['score']
                if isinstance(score, (int, float)) and score in [0, 1]:
                    total += int(score)
                    criteria_count += 1
        
        logger.info(f"📊 Общая оценка: {total}/{criteria_count} (из {len(self.required_script_criteria)} критериев)")
        
        return total
    
    def _create_emergency_fallback_data(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """🚨 Аварийная структура данных при критических ошибках"""
        
        logger.error("🚨 Создание аварийной структуры данных!")
        
        return {
            'personal_info': self.fallback_values['personal_info'].copy(),
            'commercial_info': self.fallback_values['commercial_info'].copy(),
            'script_evaluation': {criterion: {'score': 0, 'comment': 'Ошибка анализа - требует ручной проверки'} for criterion in self.required_script_criteria},
            'call_result': {'status': 'ошибка анализа', 'conversion': 'требует проверки', 'quality_score': 0},
            'total_score': 0,
            'audio_duration': analysis_result.get('audio_duration', 0),
            'corrected_transcription': analysis_result.get('corrected_transcription', ''),
            'validation_summary': {
                'emergency_fallback': True,
                'requires_manual_review': True,
                'personal_fields_fixed': len(self.fallback_values['personal_info']),
                'commercial_fields_fixed': len(self.fallback_values['commercial_info']),
                'script_criteria_count': len(self.required_script_criteria),
                'total_score_verified': 0
            }
        }
    
    def get_html_display_data(self, standardized_data: Dict[str, Any]) -> Dict[str, Any]:
        """📄 Данные для HTML отчета с правильным форматированием"""
        return {
            'personal_info': standardized_data['personal_info'],
            'commercial_info': standardized_data['commercial_info'],
            'script_evaluation': standardized_data['script_evaluation'],
            'call_result': standardized_data['call_result'],
            'total_score': standardized_data['total_score'],
            'corrected_transcription': standardized_data['corrected_transcription']
        }
    
    def get_google_sheets_data(self, standardized_data: Dict[str, Any], audio_file: str) -> List[Any]:
        """📊 Данные для Google Sheets в правильном порядке (35 колонок)"""
        
        personal = standardized_data['personal_info']
        commercial = standardized_data['commercial_info']
        script = standardized_data['script_evaluation']
        call_result = standardized_data['call_result']
        total_score = standardized_data['total_score']
        audio_duration = standardized_data['audio_duration']
        
        # Определяем записался ли клиент
        status = call_result.get('status', '').lower()
        recorded = 1 if any(word in status for word in ['записался', 'записан', 'запись']) else 0
        
        # Формируем строку данных (35 колонок)
        row_data = [
            # ОСНОВНАЯ ИНФОРМАЦИЯ О ЗВОНКЕ (4 колонки)
            datetime.now().strftime('%d.%m.%Y'),  # 1. Дата
            datetime.now().strftime('%H:%M'),     # 2. Время звонка
            f"{audio_duration/60:.1f} мин",       # 3. Длительность
            personal.get('admin_name', 'не указан'), # 4. Администратор
            
            # БЛОК I: ПРИВЕТСТВИЕ (4 критерия)
            script.get('приветствие', {}).get('score', 0),           # 5
            script.get('название_клиники', {}).get('score', 0),      # 6
            script.get('фио_администратора', {}).get('score', 0),    # 7
            script.get('имя_пациента', {}).get('score', 0),          # 8
            
            # БЛОК II: РАСКРЫВАЮЩИЕ ВОПРОСЫ (4 критерия)
            script.get('блок_опроса', {}).get('score', 0),           # 9
            script.get('презентация_исследования', {}).get('score', 0), # 10
            script.get('комплекс_предложен', {}).get('score', 0),    # 11
            script.get('цена_озвучена', {}).get('score', 0),         # 12
            
            # БЛОК III: ПРОДАЖА/ЗАПИСЬ (3 критерия)
            script.get('соблюден_алгоритм', {}).get('score', 0),     # 13
            script.get('возражение_обработано', {}).get('score', 0), # 14
            script.get('структура_скрипта', {}).get('score', 0),     # 15
            
            # ПЕРСОНАЛЬНАЯ ИНФОРМАЦИЯ (5 колонок)
            personal.get('client_name', ''),       # 16. ФИО клиента
            personal.get('birth_date', ''),        # 17. Дата рождения
            personal.get('phone_number', ''),      # 18. Телефон
            f"{commercial.get('appointment_date', '')} {commercial.get('appointment_time', '')}".strip(), # 19. Дата/время записи
            commercial.get('clinic_address', ''),  # 20. Адрес клиники
            
            # ДОПОЛНИТЕЛЬНЫЕ КРИТЕРИИ (4 критерия)
            script.get('паспорт_документы', {}).get('score', 0),     # 21
            script.get('диск_озвучен', {}).get('score', 0),          # 22
            script.get('видеозаключение', {}).get('score', 0),       # 23
            script.get('подготовка', {}).get('score', 0),            # 24
            
            # ИТОГОВЫЕ РЕЗУЛЬТАТЫ (4 колонки)
            total_score,                          # 25. Общая оценка
            'Да' if recorded else 'Нет',         # 26. Пациент записался
            '',                                   # 27. Комментарии
            'Записался' if recorded else 'Не записался', # 28. Итог
            
            # БИЗНЕС-АНАЛИТИКА (7 колонок)
            1,                                    # 29. Входящий звонок
            recorded,                             # 30. Записался (1/0)
            0,                                    # 31. Упущен из-за скрипта
            0,                                    # 32. Не записался при соблюдении
            f"{recorded * 100:.1f}%",             # 33. Конверсия %
            f"{(total_score/20)*100:.1f}%",       # 34. Соблюдение скрипта %
            call_result.get('recommendations', '') # 35. Бизнес-анализ
        ]
        
        return row_data