#!/usr/bin/env python3
"""
Health Check для Stranzit Audio Downloader
Проверяет состояние системы и отправляет отчеты
"""

import os
import json
import psutil
import requests
from datetime import datetime, timedelta
from pathlib import Path
from config import get_config

def check_disk_space(download_dir=None):
    """Проверить свободное место на диске"""
    if download_dir is None:
        config = get_config()
        download_dir = config.download.download_dir
    try:
        stat = os.statvfs(download_dir)
        total_gb = (stat.f_blocks * stat.f_frsize) / (1024**3)
        free_gb = (stat.f_bavail * stat.f_frsize) / (1024**3)
        used_gb = ((stat.f_blocks - stat.f_bavail) * stat.f_frsize) / (1024**3)
        usage_percent = ((stat.f_blocks - stat.f_bavail) / stat.f_blocks) * 100

        return {
            'status': 'ok' if free_gb > 1.0 else 'warning' if free_gb > 0.5 else 'critical',
            'total_gb': round(total_gb, 1),
            'free_gb': round(free_gb, 1),
            'used_gb': round(used_gb, 1),
            'usage_percent': round(usage_percent, 1)
        }
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def check_process_status():
    """Проверить статус процессов watcher"""
    try:
        watcher_processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
            if proc.info['cmdline'] and 'call_records_watcher.py' in ' '.join(proc.info['cmdline']):
                watcher_processes.append({
                    'pid': proc.info['pid'],
                    'started': datetime.fromtimestamp(proc.info['create_time']).isoformat(),
                    'memory_mb': round(proc.memory_info().rss / 1024 / 1024, 1),
                    'cpu_percent': proc.cpu_percent()
                })

        return {
            'status': 'ok' if watcher_processes else 'warning',
            'processes': watcher_processes,
            'count': len(watcher_processes)
        }
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def check_database(db_path=None):
    """Проверить состояние базы данных"""
    if db_path is None:
        config = get_config()
        db_path = config.database.database_path
    try:
        if not os.path.exists(db_path):
            return {'status': 'warning', 'message': 'База данных не найдена'}

        # Подключение к БД
        import sqlite3
        conn = sqlite3.connect(db_path)

        # Статистика
        cursor = conn.execute("SELECT COUNT(*) FROM downloaded_records")
        total_records = cursor.fetchone()[0]

        cursor = conn.execute("SELECT COUNT(*) FROM downloaded_records WHERE downloaded_at >= date('now', '-1 day')")
        today_records = cursor.fetchone()[0]

        # Последняя запись
        cursor = conn.execute("SELECT downloaded_at FROM downloaded_records ORDER BY downloaded_at DESC LIMIT 1")
        last_download = cursor.fetchone()

        conn.close()

        return {
            'status': 'ok',
            'total_records': total_records,
            'today_records': today_records,
            'last_download': last_download[0] if last_download else None
        }
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def check_downloads_dir(download_dir=None):
    """Проверить директорию загрузок"""
    if download_dir is None:
        config = get_config()
        download_dir = config.download.download_dir
    try:
        if not os.path.exists(download_dir):
            return {'status': 'ok', 'files_count': 0, 'total_size_mb': 0}

        total_size = 0
        files_count = 0

        for file_path in Path(download_dir).glob("*.mp3"):
            total_size += file_path.stat().st_size
            files_count += 1

        return {
            'status': 'ok',
            'files_count': files_count,
            'total_size_mb': round(total_size / 1024 / 1024, 1)
        }
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def check_log_files():
    """Проверить логи"""
    try:
        log_files = ['watcher.log', 'watcher.log.1', 'watcher.log.2', 'watcher.log.3', 'watcher.log.4']
        total_size = 0

        for log_file in log_files:
            if os.path.exists(log_file):
                total_size += os.path.getsize(log_file)

        return {
            'status': 'ok',
            'total_size_mb': round(total_size / 1024 / 1024, 1)
        }
    except Exception as e:
        return {'status': 'error', 'error': str(e)}

def send_webhook_notification(data):
    """Отправить уведомление на webhook"""
    webhook_url = os.getenv('WEBHOOK_URL')
    if not webhook_url:
        return False

    try:
        response = requests.post(
            webhook_url,
            json=data,
            timeout=10,
            headers={'Content-Type': 'application/json'}
        )
        return response.status_code < 400
    except Exception as e:
        print(f"Ошибка отправки webhook: {e}")
        return False

def main():
    """Основная функция проверки"""
    print("🔍 Health Check для Stranzit Audio Downloader")
    print("=" * 50)

    checks = {
        'disk_space': check_disk_space(),
        'process_status': check_process_status(),
        'database': check_database(),
        'downloads': check_downloads_dir(),
        'logs': check_log_files()
    }

    # Определение общего статуса
    overall_status = 'ok'
    for check_name, check_result in checks.items():
        if check_result.get('status') == 'error':
            overall_status = 'error'
            break
        elif check_result.get('status') == 'critical':
            overall_status = 'critical'
        elif check_result.get('status') == 'warning' and overall_status == 'ok':
            overall_status = 'warning'

    # Вывод результатов
    print(f"📊 Общий статус: {'✅ OK' if overall_status == 'ok' else '⚠️ WARNING' if overall_status == 'warning' else '❌ CRITICAL/ERROR'}")
    print()

    for check_name, check_result in checks.items():
        status_icon = {'ok': '✅', 'warning': '⚠️', 'critical': '🚨', 'error': '❌'}[check_result['status']]
        print(f"{status_icon} {check_name.replace('_', ' ').title()}:")
        for key, value in check_result.items():
            if key != 'status':
                print(f"   {key}: {value}")
        print()

    # Отправка уведомления при проблемах
    if overall_status in ['warning', 'critical', 'error']:
        notification_data = {
            'event': 'health_check_alert',
            'status': overall_status,
            'timestamp': datetime.now().isoformat(),
            'checks': checks
        }

        if send_webhook_notification(notification_data):
            print("📤 Уведомление отправлено")
        else:
            print("❌ Не удалось отправить уведомление")

    return overall_status

if __name__ == "__main__":
    main()
