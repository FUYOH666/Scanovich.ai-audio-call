#!/usr/bin/env python3
"""
CloudPBX RT Call Records Downloader - Автоматический загрузчик записей звонков
Версия для CloudPBX Ростелеком

Автор: Aleksandr Mordvinov
Проект: CloudPBX Calls Downloader
Политика: НИКАКИХ fallback/заглушек. Только реальные модули и проверяемые зависимости.
"""

import os
import sys
import time
import json
import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

from cloudpbx_auth import CloudPBXAuth
from config import get_config, AppConfig


class CallRecord:
    """Модель записи звонка CloudPBX RT"""

    def __init__(self, data: dict):
        """
        Инициализация записи звонка из JSON данных CloudPBX.
        
        Args:
            data: Словарь с данными звонка из API
        """
        self.id = str(data.get('id', ''))
        self.call_type = data.get('callType', 1)
        self.date_time = data.get('dateTime', '')
        self.duration_str = data.get('duration', '0 сек.')
        
        # Направление звонка
        direction_data = data.get('direction', {})
        self.direction_type = direction_data.get('image', '')  # 'group', 'out', 'group_skip'
        self.direction_title = direction_data.get('title', '')
        
        # Абоненты
        abonent_a = data.get('abonentA', {}).get('peerInfo', {})
        abonent_b = data.get('abonentB', {}).get('peerInfo', {})
        
        self.caller = abonent_a.get('caller', 'unknown')
        self.caller_number = abonent_a.get('callerNumber', 'unknown')
        self.callee = abonent_b.get('caller', 'unknown')
        self.callee_number = abonent_b.get('callerNumber', 'unknown')
        
        # Запись звонка
        record_data = data.get('record')
        if record_data:
            self.has_record = True
            self.record_call_id = record_data.get('callId', self.id)
            self.duration_seconds = record_data.get('duration', 0)
        else:
            self.has_record = False
            self.record_call_id = None
            self.duration_seconds = 0
        
        self.ext_line_number = data.get('extLineNumber', '')
        self.group_name = data.get('groupName')
    
    def is_incoming(self) -> bool:
        """Проверить, является ли звонок входящим (групповым)."""
        return self.direction_type in ['group', 'group_skip']
    
    def is_answered(self) -> bool:
        """Проверить, был ли звонок отвечен (есть запись)."""
        return self.has_record
    
    def get_readable_filename(self) -> str:
        """
        Создать читаемое имя файла.
        
        Формат: YYYY-MM-DD_HH-MM-SS_{caller}_{duration}sec.mp3
        """
        try:
            # Парсим дату из формата "2025-10-21 18:50:52+05:00"
            dt_str = self.date_time.split('+')[0].strip()
            dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
            
            date_part = dt.strftime('%Y-%m-%d_%H-%M-%S')
            caller_clean = self.caller_number.replace('+', '').replace(' ', '')[:15]
            duration = self.duration_seconds
            
            filename = f"{date_part}_{caller_clean}_{duration}sec.mp3"
            
            return filename
        except Exception as e:
            # Fallback на ID
            logging.warning(f"Ошибка генерации имени файла: {e}")
            return f"call_{self.id}.mp3"


class DatabaseManager:
    """Менеджер базы данных для отслеживания загруженных файлов"""

    def __init__(self, db_path: str = "./cloudpbx_calls.db"):
        """
        Инициализация менеджера БД.
        
        Args:
            db_path: Путь к файлу SQLite базы данных
        """
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Инициализация базы данных с таблицей загруженных записей."""
        with sqlite3.connect(self.db_path) as conn:
            # Создаем таблицу если её нет
            conn.execute('''
                CREATE TABLE IF NOT EXISTS downloaded_records (
                    id TEXT PRIMARY KEY,
                    call_id TEXT,
                    caller TEXT,
                    duration_seconds INTEGER,
                    date_time TEXT,
                    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    local_path TEXT,
                    file_size INTEGER
                )
            ''')
            
            # Проверяем наличие новых колонок и добавляем их если нет (миграция)
            cursor = conn.execute("PRAGMA table_info(downloaded_records)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'city_name' not in columns:
                logging.info("Миграция БД: добавление колонки city_name")
                conn.execute('ALTER TABLE downloaded_records ADD COLUMN city_name TEXT')
            
            if 'domain' not in columns:
                logging.info("Миграция БД: добавление колонки domain")
                conn.execute('ALTER TABLE downloaded_records ADD COLUMN domain TEXT')
            
            # Создаем индекс для быстрого поиска по городу и домену
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_city_domain 
                ON downloaded_records(city_name, domain)
            ''')
            
            conn.commit()

    def is_record_downloaded(self, call_id: str) -> bool:
        """
        Проверить, была ли запись уже загружена.
        
        Args:
            call_id: ID звонка
            
        Returns:
            bool: True если запись уже загружена
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT id FROM downloaded_records WHERE call_id = ?",
                (call_id,)
            )
            return cursor.fetchone() is not None

    def mark_record_downloaded(self, record: CallRecord, local_path: str, file_size: int, 
                               city_name: str = None, domain: str = None):
        """
        Отметить запись как загруженную.
        
        Args:
            record: Объект CallRecord
            local_path: Локальный путь к сохраненному файлу
            file_size: Размер файла в байтах
            city_name: Название города
            domain: Домен CloudPBX
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO downloaded_records
                (id, call_id, caller, duration_seconds, date_time, local_path, file_size, city_name, domain)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                record.id,
                record.record_call_id,
                record.caller_number,
                record.duration_seconds,
                record.date_time,
                local_path,
                file_size,
                city_name,
                domain
            ))
            conn.commit()

    def get_stats(self) -> dict:
        """
        Получить статистику загрузок.
        
        Returns:
            dict: Статистика (total_downloaded, downloaded_today, total_size_mb)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT COUNT(*), SUM(file_size) FROM downloaded_records")
            total, total_size = cursor.fetchone()

            cursor = conn.execute(
                "SELECT COUNT(*) FROM downloaded_records WHERE downloaded_at >= date('now', 'start of day')"
            )
            today = cursor.fetchone()[0]

            return {
                'total_downloaded': total or 0,
                'downloaded_today': today or 0,
                'total_size_mb': round((total_size or 0) / 1024 / 1024, 2)
            }


class CallRecordsDownloader:
    """Основной класс загрузчика записей звонков CloudPBX RT"""

    def __init__(self, city_name: str = None, login: str = None, password: str = None, 
                 domain: str = None, city_id: int = None):
        """
        Инициализация загрузчика с параметрами из конфигурации или явными аргументами.
        
        Args:
            city_name: Название города (для логирования)
            login: Логин CloudPBX (если None, берется из конфигурации)
            password: Пароль CloudPBX (если None, берется из конфигурации)
            domain: Домен CloudPBX (если None, берется из конфигурации)
            city_id: ID города (для загрузки из CITY_N_* переменных)
        """
        # Загружаем конфигурацию
        config = get_config()
        
        # Если указан city_id, загружаем параметры из CITY_N_* переменных
        if city_id is not None:
            # Прямая загрузка из переменных окружения для city_id
            self.city_name = os.getenv(f'CITY_{city_id}_NAME', f'City-{city_id}')
            self.login = os.getenv(f'CITY_{city_id}_LOGIN')
            self.password = os.getenv(f'CITY_{city_id}_PASSWORD')
            self.domain = os.getenv(f'CITY_{city_id}_DOMAIN')
        else:
            # Используем явные параметры или конфигурацию
            cloudpbx_config = config.cloudpbx
            self.city_name = city_name or cloudpbx_config.login or 'Unknown'
            self.login = login or cloudpbx_config.login
            self.password = password or cloudpbx_config.password
            self.domain = domain or cloudpbx_config.domain
        
        if not all([self.login, self.password, self.domain]):
            raise ValueError(
                f"Не установлены обязательные переменные для города '{self.city_name}': "
                f"login, password, domain"
            )
        
        # Настройки загрузки из конфигурации
        download_config = config.download
        filter_config = config.filters
        db_config = config.database
        log_config = config.logging
        
        self.download_dir = download_config.download_dir
        self.check_interval = download_config.check_interval
        self.min_duration = filter_config.min_duration_seconds
        self.only_incoming = filter_config.only_incoming
        self.lookback_hours = download_config.lookback_hours
        
        # Инициализация компонентов
        self.auth = CloudPBXAuth(login=self.login, domain=self.domain)
        self.db = DatabaseManager(str(db_config.database_path))
        
        # Настройка логирования с pathname:lineno
        log_format = log_config.format
        log_handlers = [logging.StreamHandler()]
        if log_config.log_file:
            log_handlers.append(logging.FileHandler(log_config.log_file))
        else:
            log_handlers.append(logging.FileHandler('watcher.log'))
        
        logging.basicConfig(
            level=getattr(logging, log_config.level),
            format=log_format,
            handlers=log_handlers,
            force=True,  # Перезаписываем существующую конфигурацию
        )
        self.logger = logging.getLogger(__name__)
        
        # Создание директории для загрузок (уже создается в валидаторе)
        
        self.logger.info(f"Инициализация загрузчика CloudPBX RT для города: {self.city_name}")
        self.logger.info(f"Домен: {self.domain}")
        self.logger.info(f"Минимальная длительность: {self.min_duration}с ({self.min_duration//60} мин)")
        self.logger.info(f"Только входящие: {self.only_incoming}")
        self.logger.info(f"Папка загрузок: {self.download_dir}")

    def authenticate(self) -> bool:
        """
        Выполнить вход в систему.
        
        Returns:
            bool: True если вход успешен
        """
        try:
            if self.auth.authenticate(password=self.password):
                self.logger.info("✅ Успешная аутентификация")
                return True
            else:
                self.logger.error("❌ Ошибка аутентификации")
                return False
        except Exception as e:
            self.logger.error(f"❌ Критическая ошибка при аутентификации: {e}")
            return False

    def get_call_history(self, hours_back: int = 24) -> List[CallRecord]:
        """
        Получить историю звонков за указанный период.
        
        Args:
            hours_back: Количество часов назад от текущего момента
            
        Returns:
            List[CallRecord]: Список записей звонков
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(hours=hours_back)
        
        params = {
            'dateStart': start_date.strftime('%Y-%m-%d %H:%M:%S'),
            'dateEnd': end_date.strftime('%Y-%m-%d %H:%M:%S'),
            'offset': 0,
            'count': 100,  # Получаем больше записей
        }
        
        self.logger.info(f"Запрос истории звонков: {params['dateStart']} - {params['dateEnd']}")
        
        try:
            response = self.auth.get('/domain/call_history', params=params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                calls_data = data.get('data', [])
                
                records = [CallRecord(call_data) for call_data in calls_data]
                self.logger.info(f"Получено {len(records)} записей звонков")
                
                return records
            else:
                self.logger.error(f"Ошибка получения истории: {response.status_code}")
                return []
                
        except Exception as e:
            self.logger.error(f"Ошибка при запросе истории: {e}")
            return []

    def filter_records(self, records: List[CallRecord]) -> List[CallRecord]:
        """
        Фильтровать записи по критериям (длительность, направление).
        
        Args:
            records: Список всех записей
            
        Returns:
            List[CallRecord]: Отфильтрованный список
        """
        filtered = []
        
        for record in records:
            # Проверка наличия записи
            if not record.is_answered():
                continue
            
            # Проверка длительности
            if record.duration_seconds < self.min_duration:
                continue
            
            # Проверка направления (если включен фильтр)
            if self.only_incoming and not record.is_incoming():
                continue
            
            filtered.append(record)
        
        self.logger.info(
            f"Отфильтровано: {len(filtered)} из {len(records)} "
            f"(длительность ≥{self.min_duration}с, входящие: {self.only_incoming})"
        )
        
        return filtered

    def download_record(self, record: CallRecord) -> Optional[str]:
        """
        Скачать запись звонка.
        
        Args:
            record: Объект CallRecord для скачивания
            
        Returns:
            Optional[str]: Путь к сохраненному файлу или None при ошибке
        """
        if not record.record_call_id:
            self.logger.warning(f"Нет record_call_id для звонка {record.id}")
            return None
        
        try:
            endpoint = f'/domain/call_history/{record.record_call_id}/record'
            
            response = self.auth.get(endpoint, timeout=60)
            
            if response.status_code == 200:
                filename = record.get_readable_filename()
                filepath = os.path.join(self.download_dir, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                file_size = os.path.getsize(filepath)
                self.logger.info(
                    f"✅ Скачано: {filename} "
                    f"({file_size / 1024:.1f} KB, {record.duration_seconds}с)"
                )
                
                return filepath
            else:
                self.logger.error(
                    f"❌ Ошибка скачивания {record.id}: "
                    f"HTTP {response.status_code}"
                )
                return None
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка при скачивании {record.id}: {e}")
            return None

    def process_new_records(self, records: List[CallRecord]) -> int:
        """
        Обработать новые записи и скачать их.
        
        Args:
            records: Список записей для обработки
            
        Returns:
            int: Количество успешно скачанных файлов
        """
        downloaded_count = 0
        
        for record in records:
            # Проверяем, не скачан ли уже
            if self.db.is_record_downloaded(record.record_call_id):
                self.logger.debug(f"Запись {record.id} уже загружена, пропускаем")
                continue
            
            self.logger.info(
                f"🎵 [{self.city_name}] Новая запись: {record.caller_number} → {record.callee_number}, "
                f"{record.duration_seconds}с, {record.direction_title}"
            )
            
            # Скачиваем
            filepath = self.download_record(record)
            
            if filepath:
                file_size = os.path.getsize(filepath)
                self.db.mark_record_downloaded(record, filepath, file_size, 
                                              city_name=self.city_name, domain=self.domain)
                downloaded_count += 1
                
                # Небольшая пауза между загрузками
                time.sleep(1)
        
        return downloaded_count

    def run_once(self) -> int:
        """
        Один цикл проверки и загрузки.
        
        Returns:
            int: Количество скачанных файлов
        """
        self.logger.info(f"🔍 [{self.city_name}] Запуск цикла проверки...")
        
        # Аутентификация
        if not self.authenticate():
            self.logger.error("Не удалось войти в систему")
            return 0
        
        # Получаем историю
        records = self.get_call_history(hours_back=self.lookback_hours)
        
        if not records:
            self.logger.info("Нет записей звонков")
            return 0
        
        # Фильтруем
        filtered = self.filter_records(records)
        
        if not filtered:
            self.logger.info("Нет записей, соответствующих критериям")
            return 0
        
        # Обрабатываем
        downloaded = self.process_new_records(filtered)
        
        # Статистика
        stats = self.db.get_stats()
        self.logger.info(
            f"📊 [{self.city_name}] Цикл завершен: загружено {downloaded} файлов. "
            f"Всего в базе: {stats['total_downloaded']} ({stats['total_size_mb']} MB)"
        )
        
        return downloaded

    def run_continuous(self):
        """Непрерывный режим работы с периодическими проверками."""
        self.logger.info("🚀 Запуск непрерывного режима (Ctrl+C для остановки)")
        self.logger.info(f"Интервал проверки: {self.check_interval} секунд ({self.check_interval//60} мин)")
        
        try:
            while True:
                try:
                    downloaded = self.run_once()
                    
                    if downloaded > 0:
                        stats = self.db.get_stats()
                        self.logger.info(
                            f"📈 Сегодня загружено: {stats['downloaded_today']} файлов"
                        )
                    
                except Exception as e:
                    self.logger.error(f"❌ Ошибка в цикле: {e}")
                    # Продолжаем работу несмотря на ошибку
                
                self.logger.info(f"⏰ Ожидание {self.check_interval}с до следующей проверки...")
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            self.logger.info("🛑 Остановка загрузчика (Ctrl+C)")
            self.auth.logout()
        except Exception as e:
            self.logger.error(f"❌ Критическая ошибка: {e}")
            self.auth.logout()
            sys.exit(1)

    def health_check(self) -> dict:
        """
        Проверка состояния системы (health check).
        
        Returns:
            dict: Статус системы с информацией о версиях, подключениях и конфигурации
        """
        import sys
        import sqlite3
        import requests
        
        health = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "versions": {
                "python": sys.version.split()[0],
                "requests": requests.__version__,
            },
            "configuration": {
                "city_name": self.city_name,
                "domain": self.domain,
                "download_dir": str(self.download_dir),
                "check_interval": self.check_interval,
                "min_duration": self.min_duration,
                "only_incoming": self.only_incoming,
                "lookback_hours": self.lookback_hours,
            },
            "checks": {},
        }
        
        # Проверка базы данных
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM downloaded_records")
                total_records = cursor.fetchone()[0]
            health["checks"]["database"] = {
                "status": "ok",
                "path": str(self.db.db_path),
                "total_records": total_records,
            }
        except Exception as e:
            health["checks"]["database"] = {
                "status": "error",
                "error": str(e),
            }
            health["status"] = "degraded"
        
        # Проверка директории загрузок
        try:
            download_path = Path(self.download_dir)
            if download_path.exists() and download_path.is_dir():
                # Проверяем доступность записи
                test_file = download_path / ".health_check"
                test_file.touch()
                test_file.unlink()
                health["checks"]["download_dir"] = {
                    "status": "ok",
                    "path": str(download_path),
                    "writable": True,
                }
            else:
                health["checks"]["download_dir"] = {
                    "status": "error",
                    "error": "Directory does not exist",
                }
                health["status"] = "degraded"
        except Exception as e:
            health["checks"]["download_dir"] = {
                "status": "error",
                "error": str(e),
            }
            health["status"] = "degraded"
        
        # Проверка подключения к CloudPBX API
        try:
            if self.auth.is_authenticated:
                health["checks"]["cloudpbx_auth"] = {
                    "status": "ok",
                    "authenticated": True,
                    "base_url": self.auth.BASE_URL,
                }
            else:
                # Пробуем аутентифицироваться
                if self.authenticate():
                    health["checks"]["cloudpbx_auth"] = {
                        "status": "ok",
                        "authenticated": True,
                        "base_url": self.auth.BASE_URL,
                    }
                else:
                    health["checks"]["cloudpbx_auth"] = {
                        "status": "error",
                        "authenticated": False,
                        "error": "Authentication failed",
                    }
                    health["status"] = "unhealthy"
        except Exception as e:
            health["checks"]["cloudpbx_auth"] = {
                "status": "error",
                "error": str(e),
            }
            health["status"] = "unhealthy"
        
        return health


def main():
    """Главная функция - точка входа приложения."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='CloudPBX RT Call Records Downloader - Загрузчик записей звонков'
    )
    parser.add_argument(
        '--once',
        action='store_true',
        help='Запустить один цикл и выйти (по умолчанию: непрерывный режим)'
    )
    parser.add_argument(
        '--hours',
        type=int,
        help='Количество часов назад для поиска (переопределяет LOOKBACK_HOURS из .env)'
    )
    parser.add_argument(
        '--city-id',
        type=int,
        help='ID города (1-16) для загрузки из CITY_N_* переменных окружения'
    )
    parser.add_argument(
        '--health',
        action='store_true',
        help='Выполнить health check и вывести статус системы'
    )
    
    args = parser.parse_args()
    
    # Health check команда
    if args.health:
        try:
            downloader = CallRecordsDownloader(city_id=args.city_id if args.city_id else None)
            health = downloader.health_check()
            
            print("\n=== Health Check ===")
            print(f"Status: {health['status']}")
            print(f"Timestamp: {health['timestamp']}")
            print("\nVersions:")
            for key, value in health['versions'].items():
                print(f"  {key}: {value}")
            print("\nConfiguration:")
            for key, value in health['configuration'].items():
                if key != 'password':  # Не показываем пароль
                    print(f"  {key}: {value}")
            print("\nChecks:")
            for check_name, check_result in health['checks'].items():
                status = check_result.get('status', 'unknown')
                print(f"  {check_name}: {status}")
                if 'error' in check_result:
                    print(f"    Error: {check_result['error']}")
                elif check_name == 'database' and 'total_records' in check_result:
                    print(f"    Total records: {check_result['total_records']}")
                elif check_name == 'download_dir' and 'writable' in check_result:
                    print(f"    Writable: {check_result['writable']}")
                elif check_name == 'cloudpbx_auth' and 'authenticated' in check_result:
                    print(f"    Authenticated: {check_result['authenticated']}")
                    print(f"    Base URL: {check_result.get('base_url', 'N/A')}")
            
            sys.exit(0 if health['status'] == 'healthy' else 1)
        except Exception as e:
            print(f"❌ Ошибка при выполнении health check: {e}")
            sys.exit(1)
    
    try:
        # Создаем downloader с указанием city_id если он передан
        downloader = CallRecordsDownloader(city_id=args.city_id if args.city_id else None)
        
        # Переопределяем lookback_hours если указано
        if args.hours:
            downloader.lookback_hours = args.hours
        
        if args.once:
            # Один цикл
            downloaded = downloader.run_once()
            print(f"\n✅ Завершено. Загружено файлов: {downloaded}")
            sys.exit(0)
        else:
            # Непрерывный режим
            downloader.run_continuous()
            
    except ValueError as e:
        print(f"❌ Ошибка конфигурации: {e}")
        print("Проверьте файл .env и установите все необходимые переменные")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
