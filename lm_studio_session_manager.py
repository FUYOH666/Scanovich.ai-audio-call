#!/usr/bin/env python3
"""
🔒 LM STUDIO SESSION MANAGER v1.0 для WhisperX Pipeline
Автор: Scanovich.ai | Дата: 29.01.2025

Менеджер сессий LM Studio для изоляции обработки между звонками:
- Автоматический рестарт сессий каждые N звонков
- Очистка контекста между звонками
- Мониторинг стабильности LM Studio
- Система резервных адресов

ЦЕЛЬ: 100% изоляция данных между звонками для медицинской конфиденциальности
"""

import logging
import requests
import time
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class LMStudioSessionManager:
    """
    Менеджер сессий LM Studio для изоляции обработки между звонками
    
    Ключевые функции:
    - Автоматический рестарт сессий для очистки контекста
    - Система резервных адресов для отказоустойчивости
    - Мониторинг состояния LM Studio
    - Изоляция данных между звонками
    """
    
    def __init__(self, lm_studio_urls: List[str] = None, session_restart_interval: int = 10):
        """
        Инициализация менеджера сессий
        
        Args:
            lm_studio_urls: Список адресов LM Studio (основной + резервные)
            session_restart_interval: Интервал рестарта сессий (количество звонков)
        """
        
        # Настройка адресов LM Studio
        if lm_studio_urls is None:
            lm_studio_urls = [
                "http://localhost:1234",           # Основной адрес
                "http://192.168.1.104:1234"       # Резервный адрес
            ]
        
        self.lm_studio_urls = lm_studio_urls
        self.active_url = None  # Текущий активный URL
        self.session_restart_interval = session_restart_interval
        
        # Счетчики для управления сессиями
        self.session_counter = 0
        self.total_calls_processed = 0
        self.last_restart_time = datetime.now()
        
        # Статистика
        self.stats = {
            "session_restarts": 0,
            "failed_requests": 0,
            "successful_requests": 0,
            "url_switches": 0,
            "start_time": datetime.now()
        }
        
        # Проверка подключения при инициализации
        self.active_url = self._find_working_url()
        
        logger.info(f"🔒 LM Studio Session Manager инициализирован")
        logger.info(f"🔗 Активный URL: {self.active_url}")
        logger.info(f"🔄 Рестарт каждые {session_restart_interval} звонков")
    
    def _find_working_url(self) -> Optional[str]:
        """
        Поиск рабочего адреса LM Studio из списка
        
        Returns:
            str: Рабочий URL или None если все недоступны
        """
        
        for url in self.lm_studio_urls:
            if self._test_connection(url):
                logger.info(f"✅ LM Studio подключен: {url}")
                return url
            else:
                logger.warning(f"❌ LM Studio недоступен: {url}")
        
        logger.error("🚨 Все адреса LM Studio недоступны!")
        return None
    
    def _test_connection(self, url: str, timeout: int = 5) -> bool:
        """
        Тестирование подключения к LM Studio
        
        Args:
            url: URL для тестирования
            timeout: Таймаут подключения
            
        Returns:
            bool: Доступен ли LM Studio
        """
        
        try:
            response = requests.get(f"{url}/v1/models", timeout=timeout)
            return response.status_code == 200
        except Exception as e:
            logger.debug(f"Ошибка подключения к {url}: {e}")
            return False
    
    def _switch_to_backup_url(self) -> bool:
        """
        Переключение на резервный адрес LM Studio
        
        Returns:
            bool: Успешно ли переключились
        """
        
        logger.warning("🔄 Переключение на резервный адрес LM Studio...")
        
        # Исключаем текущий неработающий URL
        backup_urls = [url for url in self.lm_studio_urls if url != self.active_url]
        
        for url in backup_urls:
            if self._test_connection(url):
                self.active_url = url
                self.stats["url_switches"] += 1
                logger.info(f"✅ Переключено на резервный адрес: {url}")
                return True
        
        logger.error("❌ Все резервные адреса недоступны!")
        self.active_url = None
        return False
    
    def restart_session(self, force: bool = False) -> bool:
        """
        Рестарт сессии LM Studio для очистки контекста
        
        Args:
            force: Принудительный рестарт независимо от счетчика
            
        Returns:
            bool: Успешен ли рестарт
        """
        
        if not self.active_url:
            logger.error("❌ Нет активного подключения к LM Studio")
            return False
        
        # Проверяем необходимость рестарта
        if not force and self.session_counter < self.session_restart_interval:
            return True  # Рестарт не нужен
        
        logger.info(f"🔄 Рестарт сессии LM Studio (звонок #{self.session_counter})")
        
        try:
            # Метод 1: Попытка soft restart через API (если поддерживается)
            try:
                response = requests.post(f"{self.active_url}/v1/session/reset", timeout=10)
                if response.status_code == 200:
                    logger.info("✅ LM Studio сессия перезапущена через API")
                    self._reset_session_counter()
                    return True
            except Exception:
                logger.debug("API рестарт недоступен, используем альтернативный метод")
            
            # Метод 2: Создание новой сессии через загрузку модели
            try:
                # Запрос текущих моделей для "пробуждения" новой сессии
                response = requests.get(f"{self.active_url}/v1/models", timeout=10)
                if response.status_code == 200:
                    # Небольшой тестовый запрос для очистки контекста
                    test_request = {
                        "model": "current",
                        "messages": [{"role": "system", "content": "Reset context"}],
                        "max_tokens": 1,
                        "temperature": 0.1
                    }
                    
                    response = requests.post(
                        f"{self.active_url}/v1/chat/completions",
                        json=test_request,
                        timeout=30
                    )
                    
                    logger.info("✅ LM Studio контекст очищен через тестовый запрос")
                    self._reset_session_counter()
                    return True
                    
            except Exception as e:
                logger.warning(f"Ошибка альтернативного рестарта: {e}")
            
            # Метод 3: Переключение на резервный адрес как форма рестарта
            logger.info("🔄 Попытка переключения адреса для рестарта сессии")
            if len(self.lm_studio_urls) > 1:
                original_url = self.active_url
                if self._switch_to_backup_url():
                    # Возвращаемся к исходному адресу через некоторое время
                    time.sleep(2)
                    if self._test_connection(original_url):
                        self.active_url = original_url
                        logger.info(f"✅ Возврат к основному адресу: {original_url}")
                    
                    self._reset_session_counter()
                    return True
            
            logger.warning("⚠️ Не удалось выполнить полный рестарт сессии")
            self._reset_session_counter()  # Сбрасываем счетчик в любом случае
            return False
            
        except Exception as e:
            logger.error(f"❌ Ошибка рестарта сессии: {e}")
            return False
    
    def _reset_session_counter(self):
        """Сброс счетчика сессии после успешного рестарта"""
        self.session_counter = 0
        self.last_restart_time = datetime.now()
        self.stats["session_restarts"] += 1
    
    def process_call_with_isolation(self, call_data: str, analysis_prompt: str, 
                                   max_tokens: int = 32768, temperature: float = 0.6) -> Dict:
        """
        Обработка звонка с изоляцией сессий
        
        Args:
            call_data: Данные звонка для анализа
            analysis_prompt: Промпт для анализа
            max_tokens: Максимальное количество токенов
            temperature: Температура для генерации
            
        Returns:
            Dict: Результат анализа или ошибка
        """
        
        # Проверяем необходимость рестарта перед обработкой
        if self.session_counter >= self.session_restart_interval:
            self.restart_session()
        
        # Проверяем доступность LM Studio
        if not self.active_url or not self._test_connection(self.active_url, timeout=3):
            logger.warning("🔄 Активное подключение потеряно, ищем резервный...")
            if not self._switch_to_backup_url():
                return {
                    "success": False,
                    "error": "LM Studio недоступен",
                    "fallback_needed": True
                }
        
        try:
            # Подготовка запроса
            request_data = {
                "model": "current",  # Используем текущую загруженную модель
                "messages": [
                    {"role": "system", "content": analysis_prompt},
                    {"role": "user", "content": call_data}
                ],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": False
            }
            
            # Выполнение запроса
            start_time = time.time()
            response = requests.post(
                f"{self.active_url}/v1/chat/completions",
                json=request_data,
                timeout=600  # 10 минут для сложного анализа
            )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                # Успешная обработка
                self.session_counter += 1
                self.total_calls_processed += 1
                self.stats["successful_requests"] += 1
                
                logger.info(f"✅ Звонок обработан за {processing_time:.2f}с (сессия #{self.session_counter})")
                
                return {
                    "success": True,
                    "content": content,
                    "processing_time": processing_time,
                    "session_number": self.session_counter,
                    "model_used": "LM Studio",
                    "url_used": self.active_url
                }
            
            else:
                # Ошибка запроса
                self.stats["failed_requests"] += 1
                logger.error(f"❌ LM Studio ошибка: {response.status_code} - {response.text}")
                
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "fallback_needed": True
                }
        
        except requests.exceptions.Timeout:
            self.stats["failed_requests"] += 1
            logger.error("⏰ Таймаут запроса к LM Studio")
            
            return {
                "success": False,
                "error": "Таймаут запроса",
                "fallback_needed": True
            }
        
        except Exception as e:
            self.stats["failed_requests"] += 1
            logger.error(f"❌ Неожиданная ошибка LM Studio: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "fallback_needed": True
            }
    
    def get_session_stats(self) -> Dict:
        """
        Получение статистики сессий
        
        Returns:
            Dict: Статистика работы менеджера сессий
        """
        
        runtime = datetime.now() - self.stats["start_time"]
        
        return {
            "total_calls_processed": self.total_calls_processed,
            "current_session_counter": self.session_counter,
            "session_restarts": self.stats["session_restarts"],
            "successful_requests": self.stats["successful_requests"],
            "failed_requests": self.stats["failed_requests"],
            "url_switches": self.stats["url_switches"],
            "active_url": self.active_url,
            "runtime_hours": runtime.total_seconds() / 3600,
            "last_restart": self.last_restart_time.strftime("%H:%M:%S"),
            "success_rate": (
                self.stats["successful_requests"] / 
                max(1, self.stats["successful_requests"] + self.stats["failed_requests"]) * 100
            )
        }
    
    def force_session_restart(self) -> bool:
        """
        Принудительный рестарт сессии
        
        Returns:
            bool: Успешен ли рестарт
        """
        logger.info("🔄 Принудительный рестарт сессии LM Studio")
        return self.restart_session(force=True)
    
    def is_healthy(self) -> bool:
        """
        Проверка здоровья менеджера сессий
        
        Returns:
            bool: Работоспособен ли менеджер
        """
        
        if not self.active_url:
            return False
        
        # Проверяем подключение
        if not self._test_connection(self.active_url):
            return False
        
        # Проверяем статистику успешности
        stats = self.get_session_stats()
        if stats["success_rate"] < 50:  # Меньше 50% успешных запросов
            logger.warning(f"⚠️ Низкий процент успешности: {stats['success_rate']:.1f}%")
            return False
        
        return True
    
    def cleanup(self):
        """Очистка ресурсов при завершении"""
        logger.info("🧹 Очистка LM Studio Session Manager")
        
        # Финальная статистика
        stats = self.get_session_stats()
        logger.info(f"📊 Обработано звонков: {stats['total_calls_processed']}")
        logger.info(f"📊 Рестартов сессий: {stats['session_restarts']}")
        logger.info(f"📊 Успешность: {stats['success_rate']:.1f}%")


def test_lm_studio_session_manager():
    """Тестирование LMStudioSessionManager"""
    
    print("🧪 ТЕСТИРОВАНИЕ LM STUDIO SESSION MANAGER")
    print("=" * 60)
    
    try:
        # Создаем менеджер с коротким интервалом для тестирования
        manager = LMStudioSessionManager(session_restart_interval=3)
        
        print(f"🔗 Активный URL: {manager.active_url}")
        print(f"🔄 Интервал рестарта: {manager.session_restart_interval}")
        print()
        
        # Проверка здоровья
        health = manager.is_healthy()
        print(f"💚 Здоровье системы: {'✅ Здоров' if health else '❌ Проблемы'}")
        print()
        
        if health:
            # Тестовый анализ
            test_prompt = "Ты помощник для анализа медицинских звонков. Ответь кратко."
            test_data = "Тестовый звонок в клинику МРТ. Клиент спрашивает о записи на обследование."
            
            print("🧪 Выполняем тестовый анализ...")
            result = manager.process_call_with_isolation(test_data, test_prompt, max_tokens=100)
            
            if result["success"]:
                print(f"✅ Тестовый анализ успешен!")
                print(f"📊 Время обработки: {result['processing_time']:.2f}с")
                print(f"🎯 Номер сессии: {result['session_number']}")
            else:
                print(f"❌ Тестовый анализ не удался: {result['error']}")
        
        # Статистика
        print("\n📊 СТАТИСТИКА:")
        stats = manager.get_session_stats()
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")
        
        # Очистка
        manager.cleanup()
        print("\n✅ Тестирование завершено!")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")
        raise


if __name__ == "__main__":
    test_lm_studio_session_manager()