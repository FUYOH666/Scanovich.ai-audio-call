"""
Базовые тесты основного загрузчика

Автор: Aleksandr Mordvinov
Проект: CloudPBX Calls Downloader
"""

import pytest
import os
from call_records_watcher import CallRecord, DatabaseManager


def test_call_record_initialization():
    """Тест инициализации CallRecord из JSON данных"""
    test_data = {
        'id': 'test_call_123',
        'callType': 1,
        'dateTime': '2025-01-15 14:30:45+05:00',
        'duration': '3 мин. 21 сек.',
        'direction': {
            'image': 'group',
            'title': 'Групповой'
        },
        'abonentA': {
            'peerInfo': {
                'caller': '+79991234567',
                'callerNumber': '+79991234567'
            }
        },
        'abonentB': {
            'peerInfo': {
                'caller': '79991234568',
                'callerNumber': '79991234568'
            }
        },
        'record': {
            'callId': 'test_call_123',
            'duration': 201
        }
    }
    
    record = CallRecord(test_data)
    
    assert record.id == 'test_call_123'
    assert record.has_record == True
    assert record.duration_seconds == 201
    assert record.caller_number == '+79991234567'
    assert record.callee_number == '79991234568'


def test_call_record_is_incoming():
    """Тест определения входящего звонка"""
    # Входящий звонок
    incoming_data = {
        'id': '1',
        'direction': {'image': 'group'},
        'record': {'duration': 100}
    }
    record = CallRecord(incoming_data)
    assert record.is_incoming() == True
    
    # Исходящий звонок
    outgoing_data = {
        'id': '2',
        'direction': {'image': 'out'},
        'record': {'duration': 100}
    }
    record = CallRecord(outgoing_data)
    assert record.is_incoming() == False


def test_call_record_is_answered():
    """Тест определения отвеченного звонка"""
    # Отвеченный
    answered_data = {
        'id': '1',
        'direction': {'image': 'group'},
        'record': {'callId': '1', 'duration': 100}
    }
    record = CallRecord(answered_data)
    assert record.is_answered() == True
    
    # Пропущенный
    missed_data = {
        'id': '2',
        'direction': {'image': 'group_skip'},
        'record': None
    }
    record = CallRecord(missed_data)
    assert record.is_answered() == False


def test_call_record_filename_generation():
    """Тест генерации читаемого имени файла"""
    test_data = {
        'id': '123',
        'dateTime': '2025-01-15 14:30:45+05:00',
        'direction': {'image': 'group'},
        'abonentA': {'peerInfo': {'callerNumber': '+79991234567'}},
        'abonentB': {'peerInfo': {'callerNumber': '79991234568'}},
        'record': {
            'callId': '123',
            'duration': 201
        }
    }
    
    record = CallRecord(test_data)
    filename = record.get_readable_filename()
    
    assert filename == '2025-01-15_14-30-45_79991234567_201sec.mp3'


def test_database_manager_initialization(tmp_path):
    """Тест инициализации базы данных"""
    db_path = tmp_path / "test.db"
    db = DatabaseManager(str(db_path))
    
    assert os.path.exists(db_path)


def test_database_manager_record_tracking(tmp_path):
    """Тест отслеживания загруженных записей"""
    db_path = tmp_path / "test.db"
    db = DatabaseManager(str(db_path))
    
    # Создаем тестовую запись
    test_data = {
        'id': '123',
        'dateTime': '2025-01-15 14:30:45+05:00',
        'direction': {'image': 'group'},
        'abonentA': {'peerInfo': {'callerNumber': '+79991234567'}},
        'abonentB': {'peerInfo': {'callerNumber': '79991234568'}},
        'record': {
            'callId': '123',
            'duration': 201
        }
    }
    record = CallRecord(test_data)
    
    # Проверяем, что запись не загружена
    assert db.is_record_downloaded('123') == False
    
    # Помечаем как загруженную
    db.mark_record_downloaded(record, '/test/path.mp3', 12345)
    
    # Проверяем, что запись загружена
    assert db.is_record_downloaded('123') == True


def test_database_manager_stats(tmp_path):
    """Тест получения статистики"""
    db_path = tmp_path / "test.db"
    db = DatabaseManager(str(db_path))
    
    # Начальная статистика
    stats = db.get_stats()
    assert stats['total_downloaded'] == 0
    assert stats['total_size_mb'] == 0.0
    
    # Добавляем запись
    test_data = {
        'id': '123',
        'dateTime': '2025-01-15 14:30:45+05:00',
        'direction': {'image': 'group'},
        'abonentA': {'peerInfo': {'callerNumber': '+79991234567'}},
        'abonentB': {'peerInfo': {'callerNumber': '79991234568'}},
        'record': {
            'callId': '123',
            'duration': 201
        }
    }
    record = CallRecord(test_data)
    db.mark_record_downloaded(record, '/test/path.mp3', 1024 * 1024)  # 1 MB
    
    # Проверяем статистику
    stats = db.get_stats()
    assert stats['total_downloaded'] == 1
    assert stats['total_size_mb'] == 1.0

