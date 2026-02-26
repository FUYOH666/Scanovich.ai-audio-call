#!/usr/bin/env python3
"""
CloudPBX RT Multi-Account Downloader - Оркестратор для параллельной загрузки из всех городов
Версия для CloudPBX Ростелеком

Автор: Aleksandr Mordvinov
Проект: CloudPBX Calls Downloader
Политика: НИКАКИХ fallback/заглушек. Только реальные модули и проверяемые зависимости.
"""

import os
import sys
import time
import signal
import logging
import multiprocessing
from datetime import datetime
from typing import List, Dict

from config import AppConfig
from call_records_watcher import CallRecordsDownloader


class CityAccount:
    """Модель аккаунта города с параметрами подключения."""
    
    def __init__(self, city_id: int, name: str, login: str, password: str, domain: str):
        """
        Инициализация аккаунта города.
        
        Args:
            city_id: ID города (1-16)
            name: Название города
            login: Логин CloudPBX
            password: Пароль CloudPBX
            domain: Домен CloudPBX
        """
        self.city_id = city_id
        self.name = name
        self.login = login
        self.password = password
        self.domain = domain
    
    def __repr__(self):
        return f"CityAccount(id={self.city_id}, name={self.name}, domain={self.domain})"
    
    def is_valid(self) -> bool:
        """Проверка валидности учетных данных."""
        return all([
            self.name,
            self.login,
            self.password and self.password != 'ЗАПОЛНИТЕ_ПАРОЛЬ',
            self.domain
        ])


def load_city_accounts() -> List[CityAccount]:
    """
    Загрузить все аккаунты городов из переменных окружения.
    
    Returns:
        List[CityAccount]: Список аккаунтов городов
    """
    accounts = []
    city_configs = AppConfig.load_city_accounts(max_cities=16)
    
    for city_id in range(1, 17):  # 16 городов
        # Ищем конфигурацию для этого city_id
        account_config = None
        for i, cfg in enumerate(city_configs):
            # Проверяем по переменным окружения для точного соответствия
            if (os.getenv(f'CITY_{city_id}_NAME') == cfg.name and
                os.getenv(f'CITY_{city_id}_LOGIN') == cfg.login and
                os.getenv(f'CITY_{city_id}_DOMAIN') == cfg.domain):
                account_config = cfg
                break
        
        if account_config:
            account = CityAccount(
                city_id,
                account_config.name or f'City-{city_id}',
                account_config.login or '',
                account_config.password or '',
                account_config.domain or '',
            )
            if account.is_valid():
                accounts.append(account)
            else:
                logging.warning(f"Пропуск города {city_id} ({account_config.name}): некорректные учетные данные")
        else:
            # Fallback на прямую загрузку из переменных окружения
            name = os.getenv(f'CITY_{city_id}_NAME')
            login = os.getenv(f'CITY_{city_id}_LOGIN')
            password = os.getenv(f'CITY_{city_id}_PASSWORD')
            domain = os.getenv(f'CITY_{city_id}_DOMAIN')
            
            if name and login and password and domain:
                account = CityAccount(city_id, name, login, password, domain)
                if account.is_valid():
                    accounts.append(account)
                else:
                    logging.warning(f"Пропуск города {city_id} ({name}): некорректные учетные данные")
            else:
                logging.debug(f"Город {city_id}: переменные окружения не найдены или неполные")
    
    return accounts


def run_city_downloader(city_id: int, city_name: str, once: bool = False):
    """
    Запустить downloader для одного города в отдельном процессе.
    
    Args:
        city_id: ID города
        city_name: Название города
        once: True для одного цикла, False для непрерывного режима
    """
    # Настройка логирования для этого процесса с pathname:lineno
    logger = logging.getLogger(f'City-{city_id}')
    logger.setLevel(logging.INFO)
    
    # Файл лога для города
    log_file = f'watcher_city_{city_id}.log'
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(pathname)s:%(lineno)d - %(message)s')
    )
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(
        logging.Formatter(f'[{city_name}] %(asctime)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s')
    )
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    try:
        logger.info(f"Запуск загрузчика для города: {city_name} (ID: {city_id})")
        
        # Создаем downloader для этого города
        downloader = CallRecordsDownloader(city_id=city_id)
        
        if once:
            # Один цикл
            downloaded = downloader.run_once()
            logger.info(f"Завершено. Загружено файлов: {downloaded}")
        else:
            # Непрерывный режим
            downloader.run_continuous()
            
    except KeyboardInterrupt:
        logger.info(f"Остановка загрузчика для города {city_name}")
    except Exception as e:
        logger.error(f"Критическая ошибка в загрузчике города {city_name}: {e}", exc_info=True)
        sys.exit(1)


class MultiAccountOrchestrator:
    """Оркестратор для управления загрузкой из нескольких аккаунтов параллельно."""
    
    def __init__(self):
        """Инициализация оркестратора."""
        self.processes: Dict[int, multiprocessing.Process] = {}
        self.accounts: List[CityAccount] = []
        self.running = False
        
        # Настройка логирования с pathname:lineno
        config = AppConfig()
        log_config = config.logging
        log_format = log_config.format
        
        logging.basicConfig(
            level=getattr(logging, log_config.level),
            format=log_format,
            handlers=[
                logging.FileHandler('multi_account_orchestrator.log'),
                logging.StreamHandler()
            ],
            force=True,  # Перезаписываем существующую конфигурацию
        )
        self.logger = logging.getLogger('Orchestrator')
        
        # Обработка сигналов для graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Обработчик сигналов для graceful shutdown."""
        self.logger.info(f"Получен сигнал {signum}, запускаем остановку...")
        self.stop_all()
        sys.exit(0)
    
    def load_accounts(self) -> int:
        """
        Загрузить аккаунты городов.
        
        Returns:
            int: Количество загруженных аккаунтов
        """
        self.accounts = load_city_accounts()
        self.logger.info(f"Загружено {len(self.accounts)} аккаунтов городов")
        
        for account in self.accounts:
            self.logger.info(f"  - {account.name} (ID: {account.city_id}, Domain: {account.domain})")
        
        return len(self.accounts)
    
    def start_all(self, once: bool = False, delay_between_starts: int = 3):
        """
        Запустить загрузчики для всех городов параллельно.
        
        Args:
            once: True для одного цикла, False для непрерывного режима
            delay_between_starts: Задержка в секундах между запуском процессов (защита от rate limit)
        """
        if not self.accounts:
            self.logger.error("Нет загруженных аккаунтов. Запустите load_accounts() сначала.")
            return
        
        self.running = True
        self.logger.info(f"Запуск загрузчиков для {len(self.accounts)} городов...")
        self.logger.info(f"Задержка между запусками: {delay_between_starts}с (защита от rate limiting)")
        
        for i, account in enumerate(self.accounts):
            self._start_city_process(account, once)
            
            # Добавляем задержку между запусками (кроме последнего)
            if i < len(self.accounts) - 1:
                self.logger.info(f"Ожидание {delay_between_starts}с перед запуском следующего города...")
                time.sleep(delay_between_starts)
        
        self.logger.info(f"✅ Все {len(self.processes)} процессов запущены")
    
    def _start_city_process(self, account: CityAccount, once: bool = False):
        """
        Запустить процесс для одного города.
        
        Args:
            account: Аккаунт города
            once: Режим одного цикла
        """
        process = multiprocessing.Process(
            target=run_city_downloader,
            args=(account.city_id, account.name, once),
            name=f'City-{account.city_id}-{account.name}'
        )
        process.start()
        self.processes[account.city_id] = process
        self.logger.info(f"Запущен процесс для {account.name} (PID: {process.pid})")
    
    def monitor_processes(self):
        """Мониторинг и автоматический перезапуск упавших процессов."""
        self.logger.info("Начало мониторинга процессов (Ctrl+C для остановки)")
        
        try:
            while self.running:
                time.sleep(30)  # Проверка каждые 30 секунд
                
                for city_id, process in list(self.processes.items()):
                    if not process.is_alive():
                        exit_code = process.exitcode
                        account = next((a for a in self.accounts if a.city_id == city_id), None)
                        
                        if account:
                            if exit_code == 0:
                                self.logger.info(
                                    f"Процесс {account.name} завершился нормально (код: {exit_code})"
                                )
                            else:
                                self.logger.warning(
                                    f"Процесс {account.name} упал (код: {exit_code}). "
                                    f"Перезапуск через 10 секунд..."
                                )
                                time.sleep(10)
                                self._start_city_process(account, once=False)
                
        except KeyboardInterrupt:
            self.logger.info("Остановка мониторинга (Ctrl+C)")
            self.stop_all()
    
    def stop_all(self):
        """Остановить все процессы."""
        self.running = False
        self.logger.info("Остановка всех процессов...")
        
        for city_id, process in self.processes.items():
            if process.is_alive():
                account = next((a for a in self.accounts if a.city_id == city_id), None)
                city_name = account.name if account else f'City-{city_id}'
                
                self.logger.info(f"Остановка процесса {city_name} (PID: {process.pid})")
                process.terminate()
        
        # Ждем завершения всех процессов
        for process in self.processes.values():
            process.join(timeout=10)
            if process.is_alive():
                self.logger.warning(f"Принудительная остановка процесса (PID: {process.pid})")
                process.kill()
                process.join()
        
        self.logger.info("✅ Все процессы остановлены")
    
    def get_status(self) -> Dict[int, Dict]:
        """
        Получить статус всех процессов.
        
        Returns:
            Dict: Статус каждого города
        """
        status = {}
        
        for account in self.accounts:
            process = self.processes.get(account.city_id)
            
            if process:
                status[account.city_id] = {
                    'name': account.name,
                    'pid': process.pid,
                    'alive': process.is_alive(),
                    'exitcode': process.exitcode
                }
            else:
                status[account.city_id] = {
                    'name': account.name,
                    'pid': None,
                    'alive': False,
                    'exitcode': None
                }
        
        return status
    
    def print_status(self):
        """Вывести статус всех процессов."""
        status = self.get_status()
        
        print("\n" + "=" * 80)
        print(f"Статус Multi-Account Downloader ({datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")
        print("=" * 80)
        
        for city_id, info in status.items():
            alive_icon = "✅" if info['alive'] else "❌"
            print(f"{alive_icon} [{city_id:2d}] {info['name']:20s} | PID: {info['pid']} | Alive: {info['alive']}")
        
        print("=" * 80 + "\n")


def main():
    """Главная функция - точка входа приложения."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='CloudPBX RT Multi-Account Downloader - Параллельная загрузка из всех городов'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Запустить один цикл для всех городов и выйти (по умолчанию: непрерывный режим)'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Показать статус работающих процессов и выйти'
    )
    parser.add_argument(
        '--cities',
        type=str,
        help='Список ID городов через запятую (например: 1,5,10). По умолчанию: все города'
    )
    parser.add_argument(
        '--delay',
        type=int,
        default=3,
        help='Задержка в секундах между запуском процессов (по умолчанию: 3, для защиты от rate limit)'
    )
    parser.add_argument(
        '--health',
        action='store_true',
        help='Выполнить health check для всех городов и вывести статус системы'
    )
    
    args = parser.parse_args()
    
    try:
        orchestrator = MultiAccountOrchestrator()
        
        # Загружаем аккаунты
        count = orchestrator.load_accounts()
        
        if count == 0:
            print("❌ Не найдено валидных аккаунтов в .env файле")
            print("Убедитесь, что переменные CITY_N_* правильно заполнены")
            sys.exit(1)
        
        # Фильтрация по указанным городам
        if args.cities:
            city_ids = [int(x.strip()) for x in args.cities.split(',')]
            orchestrator.accounts = [a for a in orchestrator.accounts if a.city_id in city_ids]
            orchestrator.logger.info(f"Фильтр: выбрано {len(orchestrator.accounts)} городов")
        
        if args.status:
            # Показать статус
            orchestrator.print_status()
            sys.exit(0)
        
        if args.health:
            # Health check для всех городов
            print("\n=== Health Check для всех городов ===")
            for account in orchestrator.accounts:
                try:
                    downloader = CallRecordsDownloader(city_id=account.city_id)
                    health = downloader.health_check()
                    print(f"\n[{account.city_id}] {account.name}:")
                    print(f"  Status: {health['status']}")
                    for check_name, check_result in health['checks'].items():
                        status = check_result.get('status', 'unknown')
                        print(f"    {check_name}: {status}")
                        if 'error' in check_result:
                            print(f"      Error: {check_result['error']}")
                except Exception as e:
                    print(f"\n[{account.city_id}] {account.name}: ERROR - {e}")
            sys.exit(0)
        
        # Запускаем все процессы с задержкой
        orchestrator.start_all(once=args.once, delay_between_starts=args.delay)
        
        if args.once:
            # В режиме --once ждем завершения всех процессов
            orchestrator.logger.info("Ожидание завершения всех процессов...")
            for process in orchestrator.processes.values():
                process.join()
            
            orchestrator.logger.info("✅ Все процессы завершены")
            orchestrator.print_status()
        else:
            # Непрерывный режим с мониторингом
            orchestrator.monitor_processes()
        
    except KeyboardInterrupt:
        print("\n🛑 Остановка оркестратора (Ctrl+C)")
        if 'orchestrator' in locals():
            orchestrator.stop_all()
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Для multiprocessing на Linux
    multiprocessing.set_start_method('spawn', force=True)
    main()

