#!/usr/bin/env python3
"""
CloudPBX RT Authentication Module
Модуль аутентификации для личного кабинета CloudPBX Ростелеком

Автор: Aleksandr Mordvinov
Проект: CloudPBX Calls Downloader
"""

import base64
import json
import logging
import requests
from typing import Optional, Dict

# Настройка логирования с pathname:lineno
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(pathname)s:%(lineno)d - %(message)s',
)
logger = logging.getLogger(__name__)


class CloudPBXAuth:
    """
    Класс для аутентификации в CloudPBX RT.
    
    Использует JWT токены для авторизации запросов.
    """
    
    BASE_URL = "https://p2.cloudpbx.rt.ru/webapi"
    AUTH_ENDPOINT = "/auth"
    
    def __init__(self, login: Optional[str] = None, password: Optional[str] = None, domain: Optional[str] = None):
        """
        Инициализация клиента аутентификации.
        
        Args:
            login: Логин пользователя (опционально)
            password: Пароль (не сохраняется в памяти класса)
            domain: Домен ВАТС (например, XXXXXX.XX.rt.ru)
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
        })
        
        self.login = login
        self.domain = domain
        self._token = None
        self._refresh_token = None
        self.user_id = None
        self.domain_id = None
        self.is_authenticated = False
        
        # НЕ сохраняем пароль в памяти класса по соображениям безопасности
        self._password = None
    
    def _extract_base_url_from_token(self, token: str) -> Optional[str]:
        """
        Извлекает BASE_URL из JWT токена (поле iss - issuer).
        
        Это позволяет автоматически определить правильный сервер CloudPBX:
        - p1.cloudpbx.rt.ru - старые версии (серверы .16, .17, .18)
        - p2.cloudpbx.rt.ru - новые версии (серверы .20, .21, .29)
        
        Args:
            token: JWT токен
        
        Returns:
            Optional[str]: BASE_URL из токена или None если не удалось извлечь
        """
        try:
            parts = token.split('.')
            if len(parts) >= 2:
                # Декодируем payload (вторая часть JWT)
                payload_part = parts[1]
                
                # Добавляем padding если необходимо
                padding = len(payload_part) % 4
                if padding:
                    payload_part += '=' * (4 - padding)
                
                # Декодируем base64
                payload_bytes = base64.urlsafe_b64decode(payload_part)
                payload_json = json.loads(payload_bytes)
                
                # Извлекаем issuer (iss)
                iss = payload_json.get('iss')
                
                if iss:
                    logger.info(f"🎯 Автоопределён сервер из JWT токена: {iss}")
                    return iss
                else:
                    logger.warning("Поле 'iss' отсутствует в JWT токене")
            else:
                logger.warning(f"Неверный формат JWT токена: {len(parts)} частей вместо 3")
                
        except Exception as e:
            logger.warning(f"Не удалось извлечь iss из токена: {e}")
        
        return None
    
    def authenticate(self, login: Optional[str] = None, password: Optional[str] = None, domain: Optional[str] = None) -> bool:
        """
        Выполнить аутентификацию в CloudPBX RT.
        
        Args:
            login: Логин пользователя
            password: Пароль (ОБЯЗАТЕЛЬНО, не сохраняется)
            domain: Домен ВАТС
        
        Returns:
            bool: True если аутентификация успешна, False иначе
        
        Raises:
            ValueError: Если не указаны обязательные параметры
        """
        # Используем переданные параметры или сохранённые
        _login = login or self.login
        _domain = domain or self.domain
        
        if not all([_login, password, _domain]):
            raise ValueError("Необходимы все параметры: login, password, domain")
        
        # ВАЖНО: CloudPBX использует form data (не JSON!) и поле "username" (не "login")
        payload = {
            "username": _login,
            "password": password,
            "domain": _domain
        }
        
        try:
            logger.info(f"Аутентификация для пользователя: {_login[:3]}*** в домене: {_domain}")
            
            response = self.session.post(
                f"{self.BASE_URL}{self.AUTH_ENDPOINT}",
                data=payload,  # data (form) вместо json!
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Сохраняем токены и данные пользователя
                self._token = data.get('token')
                self._refresh_token = data.get('refresh_token')
                self.user_id = data.get('user_id')
                self.domain_id = data.get('domain_id')
                self.is_authenticated = True
                
                # 🔥 АВТООПРЕДЕЛЕНИЕ СЕРВЕРА ИЗ JWT ТОКЕНА
                # Извлекаем 'iss' (issuer) из токена для определения правильного сервера
                detected_base_url = self._extract_base_url_from_token(self._token)
                
                if detected_base_url and detected_base_url != self.BASE_URL:
                    logger.info(f"🔄 Переключение BASE_URL: {self.BASE_URL} → {detected_base_url}")
                    self.BASE_URL = detected_base_url
                elif detected_base_url == self.BASE_URL:
                    logger.debug(f"✅ BASE_URL совпадает с issuer токена: {self.BASE_URL}")
                else:
                    logger.warning(f"⚠️  Не удалось определить сервер из токена, используем {self.BASE_URL}")
                
                # Обновляем заголовок Authorization для последующих запросов
                self.session.headers.update({
                    'Authorization': f'Bearer {self._token}'
                })
                
                logger.info(f"✅ Успешная аутентификация. User ID: {self.user_id}, Domain ID: {self.domain_id}")
                logger.debug(f"JWT токен получен (первые 20 символов): {self._token[:20]}...")
                
                return True
            else:
                logger.error(f"❌ Ошибка аутентификации: HTTP {response.status_code}")
                logger.debug(f"Response: {response.text[:500]}")
                self.is_authenticated = False
                return False
                
        except requests.RequestException as e:
            logger.error(f"❌ Сетевая ошибка при аутентификации: {e}")
            self.is_authenticated = False
            return False
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка при аутентификации: {e}")
            self.is_authenticated = False
            return False
    
    def refresh_access_token(self) -> bool:
        """
        Обновить access token используя refresh token.
        
        Returns:
            bool: True если токен успешно обновлён
        """
        if not self._refresh_token:
            logger.error("Refresh token отсутствует")
            return False
        
        try:
            # Endpoint для обновления токена (из найденного в JS)
            response = self.session.post(
                f"{self.BASE_URL}/auth/refresh_token",
                json={"refresh_token": self._refresh_token},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self._token = data.get('token')
                
                # Обновляем заголовок
                self.session.headers.update({
                    'Authorization': f'Bearer {self._token}'
                })
                
                logger.info("✅ Access token успешно обновлён")
                return True
            else:
                logger.error(f"Ошибка обновления токена: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка при обновлении токена: {e}")
            return False
    
    def logout(self):
        """Выход из системы и очистка токенов."""
        self._token = None
        self._refresh_token = None
        self.user_id = None
        self.domain_id = None
        self.is_authenticated = False
        
        # Удаляем Authorization заголовок
        if 'Authorization' in self.session.headers:
            del self.session.headers['Authorization']
        
        logger.info("✅ Выход выполнен, токены очищены")
    
    def get(self, endpoint: str, params: Optional[Dict] = None, **kwargs) -> requests.Response:
        """
        Выполнить GET запрос с автоматической проверкой аутентификации.
        
        Args:
            endpoint: API endpoint (например, '/domain/call_history')
            params: Query параметры
            **kwargs: Дополнительные параметры для requests.get
        
        Returns:
            requests.Response: Ответ от сервера
        
        Raises:
            ValueError: Если пользователь не аутентифицирован
        """
        if not self.is_authenticated:
            raise ValueError("Требуется аутентификация. Вызовите authenticate() сначала.")
        
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = self.session.get(url, params=params, **kwargs)
            
            # Если 401 - пробуем обновить токен
            if response.status_code == 401:
                logger.warning(f"Получен 401 при запросе к {endpoint}")
                logger.debug(f"Response headers: {dict(response.headers)}")
                logger.debug(f"Response body: {response.text[:500]}")
                
                # Пробуем повторить запрос БЕЗ обновления токена (может это временный глюк)
                logger.info("Повторный запрос без обновления токена...")
                response_retry = self.session.get(url, params=params, **kwargs)
                
                if response_retry.status_code == 401:
                    # Только тогда пробуем refresh
                    logger.warning("Повторный запрос тоже 401, пробуем обновить токен...")
                    if self.refresh_access_token():
                        # Повторяем запрос с новым токеном
                        response = self.session.get(url, params=params, **kwargs)
                    else:
                        logger.error("Не удалось обновить токен, используем исходный response")
                        response = response_retry
                else:
                    logger.info(f"Повторный запрос успешен: {response_retry.status_code}")
                    response = response_retry
            
            return response
            
        except requests.RequestException as e:
            logger.error(f"Ошибка GET запроса к {endpoint}: {e}")
            raise
    
    def post(self, endpoint: str, json: Optional[Dict] = None, **kwargs) -> requests.Response:
        """
        Выполнить POST запрос с автоматической проверкой аутентификации.
        
        Args:
            endpoint: API endpoint
            json: JSON данные для отправки
            **kwargs: Дополнительные параметры для requests.post
        
        Returns:
            requests.Response: Ответ от сервера
        
        Raises:
            ValueError: Если пользователь не аутентифицирован
        """
        if not self.is_authenticated:
            raise ValueError("Требуется аутентификация. Вызовите authenticate() сначала.")
        
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = self.session.post(url, json=json, **kwargs)
            
            # Если 401 - пробуем обновить токен
            if response.status_code == 401:
                logger.warning("Получен 401, пробуем обновить токен...")
                if self.refresh_access_token():
                    # Повторяем запрос с новым токеном
                    response = self.session.post(url, json=json, **kwargs)
            
            return response
            
        except requests.RequestException as e:
            logger.error(f"Ошибка POST запроса к {endpoint}: {e}")
            raise
    
    def check_auth_status(self) -> bool:
        """
        Проверить статус аутентификации.
        
        Returns:
            bool: True если пользователь аутентифицирован
        """
        return self.is_authenticated and self._token is not None


def main():
    """Пример использования модуля аутентификации."""
    from config import get_config
    
    config = get_config()
    cloudpbx_config = config.cloudpbx
    
    if not all([cloudpbx_config.login, cloudpbx_config.password, cloudpbx_config.domain]):
        logger.error(
            "Не установлены переменные окружения: CLOUDPBX_LOGIN, CLOUDPBX_PASSWORD, CLOUDPBX_DOMAIN",
        )
        return
    
    # Создаём экземпляр клиента
    auth = CloudPBXAuth(
        login=cloudpbx_config.login,
        domain=cloudpbx_config.domain,
    )
    
    # Выполняем аутентификацию
    if auth.authenticate(password=cloudpbx_config.password):
        print(f"✅ Аутентификация успешна!")
        print(f"User ID: {auth.user_id}")
        print(f"Domain ID: {auth.domain_id}")
        print(f"Токен (первые 30 символов): {auth._token[:30]}...")
        
        # Пример GET запроса
        try:
            response = auth.get('/domain/settings')
            if response.status_code == 200:
                print(f"✅ Тестовый GET запрос выполнен успешно")
        except Exception as e:
            print(f"Ошибка при тестовом запросе: {e}")
        
        # Выход
        auth.logout()
    else:
        print("❌ Ошибка аутентификации")


if __name__ == "__main__":
    main()

