"""
Базовые тесты модуля аутентификации CloudPBX RT

Автор: Aleksandr Mordvinov
Проект: CloudPBX Calls Downloader
"""

import pytest
from cloudpbx_auth import CloudPBXAuth


def test_cloudpbx_auth_initialization():
    """Тест инициализации класса аутентификации"""
    auth = CloudPBXAuth(login="test_user", domain="XXXXXX.XX.rt.ru")
    
    assert auth.login == "test_user"
    assert auth.domain == "XXXXXX.XX.rt.ru"
    assert auth.is_authenticated == False
    assert auth._token is None


def test_cloudpbx_auth_base_url():
    """Тест правильности базового URL"""
    auth = CloudPBXAuth()
    
    assert auth.BASE_URL == "https://p2.cloudpbx.rt.ru/webapi"
    assert auth.AUTH_ENDPOINT == "/auth"


def test_cloudpbx_auth_session_headers():
    """Тест наличия обязательных заголовков"""
    auth = CloudPBXAuth()
    
    assert 'User-Agent' in auth.session.headers
    assert 'Accept' in auth.session.headers
    assert auth.session.headers['Accept'] == 'application/json, text/plain, */*'


def test_cloudpbx_auth_authenticate_without_password():
    """Тест что authenticate требует пароль"""
    auth = CloudPBXAuth(login="test", domain="XXXXXX.XX.rt.ru")
    
    with pytest.raises(ValueError, match="Необходимы все параметры"):
        auth.authenticate()


def test_cloudpbx_auth_authenticate_without_login():
    """Тест что authenticate требует логин"""
    auth = CloudPBXAuth()
    
    with pytest.raises(ValueError, match="Необходимы все параметры"):
        auth.authenticate(password="test123")


def test_cloudpbx_auth_check_status_before_auth():
    """Тест проверки статуса до аутентификации"""
    auth = CloudPBXAuth()
    
    assert auth.check_auth_status() == False


def test_cloudpbx_auth_logout():
    """Тест выхода из системы"""
    auth = CloudPBXAuth(login="test", domain="XXXXXX.XX.rt.ru")
    
    # Симулируем аутентификацию
    auth._token = "fake_token"
    auth.is_authenticated = True
    auth.session.headers['Authorization'] = 'Bearer fake_token'
    
    # Выход
    auth.logout()
    
    assert auth._token is None
    assert auth.is_authenticated == False
    assert 'Authorization' not in auth.session.headers

