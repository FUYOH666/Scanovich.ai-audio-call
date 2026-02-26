#!/usr/bin/env python3
"""
Stranzit Audio Downloader - Authentication Module
Аутентификация в личном кабинете lk.stranzit.ru
"""

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import logging

# Настройка логирования с pathname:lineno
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(pathname)s:%(lineno)d - %(message)s',
)
logger = logging.getLogger(__name__)

class StranzitAuth:
    """Класс для аутентификации в личном кабинете Stranzit"""

    BASE_URL = "https://lk.stranzit.ru"
    LOGIN_URL = urljoin(BASE_URL, "/Account/Login")

    def __init__(self, username=None, password=None):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        # ⚠️  Никогда не храним пароль в памяти класса
        # Используем только при вызове login()
        self.username = username
        self._password = None  # Не храним пароль постоянно
        self.is_authenticated = False

    def set_credentials(self, username, password):
        """Безопасная установка credentials (пароль не сохраняется в классе)"""
        self.username = username
        # Пароль передается только в метод login()

    def get_login_page(self):
        """Получить страницу логина и извлечь CSRF токен"""
        try:
            logger.info("Получаем страницу логина...")
            response = self.session.get(self.LOGIN_URL)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')

            # Ищем CSRF токен
            token_input = soup.find('input', {'name': '__RequestVerificationToken'})
            if not token_input:
                raise ValueError("CSRF токен не найден")

            token = token_input.get('value')
            logger.info(f"CSRF токен получен: {token[:20]}...")

            return token, soup

        except requests.RequestException as e:
            logger.error(f"Ошибка при получении страницы логина: {e}")
            raise

    def login(self, username=None, password=None):
        """Выполнить вход в систему

        Args:
            username: логин (опционально, если уже установлен)
            password: пароль (ОБЯЗАТЕЛЬНО, не сохраняется в классе)
        """
        if username:
            self.username = username

        if not password:
            raise ValueError("Пароль обязателен для входа")

        if not self.username:
            raise ValueError("Логин не указан")

        try:
            # Получаем токен
            token, soup = self.get_login_page()

            # Подготавливаем данные для входа
            login_data = {
                'Login': self.username,
                'Password': password,  # Используем переданный пароль
                'RememberMe': 'false',  # или 'true' для запоминания
                '__RequestVerificationToken': token
            }

            # Определяем action URL из формы
            form = soup.find('form')
            if form and form.get('action'):
                action_url = urljoin(self.BASE_URL, form['action'])
            else:
                action_url = self.LOGIN_URL

            logger.info(f"Выполняем вход для пользователя: {self.username[:3]}***")  # Маскируем логин в логах
            response = self.session.post(action_url, data=login_data, allow_redirects=True)

            # Проверяем успешность входа
            # Успешный вход может перенаправлять на /Services или другие страницы
            if (response.url != self.LOGIN_URL and
                "Login" not in response.url and
                response.status_code == 200):
                self.is_authenticated = True
                logger.info("✅ Успешный вход в систему")
                logger.debug(f"Перенаправлено на: {response.url}")
                return True
            else:
                logger.error("❌ Вход не удался")
                logger.debug(f"URL после входа: {response.url}, Status: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Ошибка при входе: {e}")
            return False

    def check_auth_status(self):
        """Проверить статус аутентификации"""
        try:
            response = self.session.get(urljoin(self.BASE_URL, "/Account"))
            if response.url != self.LOGIN_URL:  # Если не редиректинуло на логин
                self.is_authenticated = True
                return True
            else:
                self.is_authenticated = False
                return False
        except Exception as e:
            logger.error(f"Ошибка при проверке статуса: {e}")
            return False

    def logout(self):
        """Выход из системы"""
        try:
            logout_url = urljoin(self.BASE_URL, "/Account/LogOff")
            self.session.get(logout_url)
            self.is_authenticated = False
            logger.info("✅ Выход выполнен")
        except Exception as e:
            logger.error(f"Ошибка при выходе: {e}")

    def get_page(self, url, **kwargs):
        """Получить страницу с проверкой аутентификации"""
        if not self.is_authenticated:
            raise ValueError("Не выполнена аутентификация")

        try:
            response = self.session.get(url, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"Ошибка при получении страницы {url}: {e}")
            raise


def main():
    """Пример использования"""
    # Пример использования (замените на реальные credentials)
    auth = StranzitAuth()

    # Для тестирования раскомментируйте и укажите credentials
    # if auth.login("your_username", "your_password"):
    #     print("Успешная аутентификация!")
    #
    #     # Пример получения защищенной страницы
    #     try:
    #         response = auth.get_page(urljoin(auth.BASE_URL, "/Home"))
    #         print(f"Главная страница: {len(response.text)} символов")
    #     except Exception as e:
    #         print(f"Ошибка: {e}")
    #
    #     auth.logout()
    # else:
    #     print("Ошибка аутентификации")

    print("Модуль аутентификации готов к использованию")
    print("Для использования:")
    print("1. Укажите логин и пароль")
    print("2. Вызовите auth.login(username, password)")
    print("3. Используйте auth.get_page(url) для получения страниц")


if __name__ == "__main__":
    main()
