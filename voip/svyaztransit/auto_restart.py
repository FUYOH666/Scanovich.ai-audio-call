#!/usr/bin/env python3
"""
Автоматический перезапуск watcher при сбоях
Мониторит процесс watcher и перезапускает при необходимости
"""

import os
import time
import psutil
import subprocess
import logging
from datetime import datetime, timedelta
from config import get_config

# Настройка логирования с pathname:lineno
config = get_config()
log_config = config.logging

logging.basicConfig(
    level=getattr(logging, log_config.level),
    format=log_config.format,
    handlers=[
        logging.FileHandler('auto_restart.log'),
        logging.StreamHandler()
    ],
    force=True,  # Перезаписываем существующую конфигурацию
)
logger = logging.getLogger(__name__)

class WatcherRestarter:
    """Класс для мониторинга и перезапуска watcher процесса"""

    def __init__(self):
        self.script_path = os.path.join(os.getcwd(), 'run_watcher.sh')
        self.process_name = 'call_records_watcher.py'
        self.check_interval = 30  # Проверка каждые 30 секунд
        self.restart_delay = 5    # Задержка перед перезапуском
        self.max_restarts_per_hour = 10  # Максимум перезапусков в час

        # Статистика перезапусков
        self.restart_count = 0
        self.last_restart_time = None

    def is_watcher_running(self) -> bool:
        """Проверить, запущен ли процесс watcher"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.info['cmdline'] and self.process_name in ' '.join(proc.info['cmdline']):
                    return True
        except Exception as e:
            logger.warning(f"Ошибка при проверке процессов: {e}")

        return False

    def should_restart(self) -> bool:
        """Определить, нужно ли перезапустить процесс"""
        now = datetime.now()

        # Проверка максимального количества перезапусков в час
        if self.restart_count >= self.max_restarts_per_hour:
            if self.last_restart_time and (now - self.last_restart_time).seconds < 3600:
                logger.warning(f"Превышен лимит перезапусков ({self.max_restarts_per_hour}) в час")
                return False

        # Сброс счетчика если прошел час
        if self.last_restart_time and (now - self.last_restart_time).seconds >= 3600:
            self.restart_count = 0
            logger.info("Счетчик перезапусков сброшен")

        return True

    def restart_watcher(self) -> bool:
        """Перезапустить watcher процесс"""
        if not self.should_restart():
            return False

        try:
            logger.info("Перезапуск watcher процесса...")

            # Завершить существующие процессы
            self.kill_existing_processes()

            # Подождать немного
            time.sleep(self.restart_delay)

            # Запустить новый процесс
            if os.path.exists(self.script_path):
                logger.info(f"Запуск скрипта: {self.script_path}")
                subprocess.Popen([self.script_path],
                               stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL)
            else:
                logger.error(f"Скрипт не найден: {self.script_path}")
                return False

            self.restart_count += 1
            self.last_restart_time = datetime.now()

            logger.info(f"Watcher перезапущен (перезапуск #{self.restart_count})")
            return True

        except Exception as e:
            logger.error(f"Ошибка при перезапуске watcher: {e}")
            return False

    def kill_existing_processes(self):
        """Завершить существующие процессы watcher"""
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                if proc.info['cmdline'] and self.process_name in ' '.join(proc.info['cmdline']):
                    logger.info(f"Завершение процесса PID {proc.info['pid']}")
                    proc.terminate()

                    # Подождать завершения
                    try:
                        proc.wait(timeout=10)
                    except psutil.TimeoutExpired:
                        logger.warning(f"Процесс {proc.info['pid']} не завершился, принудительное завершение")
                        proc.kill()

        except Exception as e:
            logger.warning(f"Ошибка при завершении процессов: {e}")

    def check_and_restart(self):
        """Проверить статус и перезапустить при необходимости"""
        if not self.is_watcher_running():
            logger.warning("Процесс watcher не найден, пытаюсь перезапустить...")
            self.restart_watcher()
        else:
            logger.debug("Процесс watcher работает нормально")

    def run(self):
        """Основной цикл мониторинга"""
        logger.info("🚀 Запуск мониторинга watcher процессов")
        logger.info(f"Интервал проверки: {self.check_interval} секунд")
        logger.info(f"Максимум перезапусков в час: {self.max_restarts_per_hour}")

        try:
            while True:
                self.check_and_restart()
                time.sleep(self.check_interval)

        except KeyboardInterrupt:
            logger.info("🛑 Остановка мониторинга")
        except Exception as e:
            logger.error(f"Критическая ошибка в мониторинге: {e}")

def main():
    """Главная функция"""
    restarter = WatcherRestarter()
    restarter.run()

if __name__ == "__main__":
    main()
