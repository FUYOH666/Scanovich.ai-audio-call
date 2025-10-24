"""
Менеджер филиалов и нормализация данных.

Функции:
- Парсинг branches.yaml
- Извлечение списка адресов и администраторов
- Валидация и нормализация адресов
- Связывание администраторов с филиалами
"""

import logging
from pathlib import Path
from typing import Dict, List, Set

import yaml

logger = logging.getLogger(__name__)


class BranchesManager:
    """Менеджер филиалов и администраторов."""

    def __init__(self, branches_yaml_path: str = "branches.yaml"):
        """
        Инициализация менеджера филиалов.

        Args:
            branches_yaml_path: Путь к branches.yaml

        Raises:
            FileNotFoundError: Если branches.yaml не найден
        """
        self.branches_yaml_path = Path(branches_yaml_path)
        self.branches_data = {}
        self.addresses = []
        self.admins = set()
        self.admin_to_branches = {}  # {admin_name: [branch_addresses]}
        
        self._load_branches()
        
        logger.info(
            f"✓ BranchesManager инициализирован: {len(self.addresses)} филиалов, "
            f"{len(self.admins)} уникальных админов"
        )

    def _load_branches(self):
        """Загрузить и распарсить branches.yaml."""
        if not self.branches_yaml_path.exists():
            raise FileNotFoundError(f"branches.yaml не найден: {self.branches_yaml_path}")

        try:
            with open(self.branches_yaml_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)

            self.branches_data = data.get("branches", {})
            
            # Извлечение адресов
            self.addresses = list(self.branches_data.keys())
            
            # Извлечение уникальных админов
            for branch_address, branch_info in self.branches_data.items():
                admins_list = branch_info.get("admins", [])
                
                for admin in admins_list:
                    self.admins.add(admin)
                    
                    # Связывание админа с филиалом
                    if admin not in self.admin_to_branches:
                        self.admin_to_branches[admin] = []
                    self.admin_to_branches[admin].append(branch_address)
            
            logger.info(f"Загружено {len(self.addresses)} филиалов из branches.yaml")
            logger.debug(f"Уникальные администраторы: {sorted(self.admins)}")

        except Exception as e:
            logger.error(f"Ошибка загрузки branches.yaml: {e}")
            raise RuntimeError(f"Не удалось загрузить branches.yaml: {e}") from e

    def get_all_addresses(self) -> List[str]:
        """
        Получить список всех адресов филиалов.

        Returns:
            List[str]: Список адресов
        """
        return self.addresses

    def get_all_admins(self) -> List[str]:
        """
        Получить список всех уникальных администраторов.

        Returns:
            List[str]: Список имён (отсортирован)
        """
        return sorted(self.admins)

    def get_equipment_for_address(self, address: str) -> List[str]:
        """
        Получить список оборудования для филиала.

        Args:
            address: Адрес филиала

        Returns:
            List[str]: Список оборудования (например, ["1.5T", "3T"])
        """
        branch_info = self.branches_data.get(address, {})
        return branch_info.get("equipment", [])

    def get_branches_for_admin(self, admin_name: str) -> List[str]:
        """
        Получить список филиалов, где работает администратор.

        Args:
            admin_name: Имя администратора

        Returns:
            List[str]: Список адресов филиалов
        """
        return self.admin_to_branches.get(admin_name, [])

    def validate_admin(self, admin_name: str) -> bool:
        """
        Проверить, существует ли администратор в базе.

        Args:
            admin_name: Имя администратора

        Returns:
            bool: True если администратор найден
        """
        return admin_name in self.admins

    def normalize_address(self, raw_address: str) -> str:
        """
        Нормализовать адрес к стандартному виду из branches.yaml.

        Использует простое сопоставление по ключевым словам.

        Args:
            raw_address: Сырой адрес из транскрипции

        Returns:
            str: Нормализованный адрес или исходный, если не найдено совпадение
        """
        if not raw_address:
            return raw_address

        raw_lower = raw_address.lower()

        # Поиск совпадений по ключевым словам
        for standard_address in self.addresses:
            standard_lower = standard_address.lower()
            
            # Простое совпадение: если в raw_address есть часть стандартного адреса
            # Например: "Город, улица Примерная" → "ул. Ивана Попова д.1Б"
            
            # Извлекаем ключевые слова из стандартного адреса (убираем "ул.", "д.", "зд." и т.п.)
            import re
            key_parts = re.findall(r'[а-яё]+', standard_lower)
            
            # Проверяем, есть ли хотя бы 2 ключевых слова в raw_address
            matches = sum(1 for part in key_parts if part in raw_lower)
            
            if matches >= 2:
                logger.debug(f"Нормализация адреса: '{raw_address}' → '{standard_address}'")
                return standard_address

        # Если не найдено совпадение - возвращаем исходный адрес
        logger.debug(f"Адрес не распознан, оставляем как есть: '{raw_address}'")
        return raw_address

    def format_for_prompt(self) -> str:
        """
        Форматировать данные филиалов для добавления в VLLM промпт.

        Returns:
            str: Отформатированный текст для промпта
        """
        # Список адресов
        addresses_text = "\n".join(
            [f"{i+1}. {addr}" for i, addr in enumerate(self.addresses)]
        )
        
        # Список админов (в одну строку, через запятую)
        admins_text = ", ".join(sorted(self.admins))
        
        prompt_section = f"""
ВАЖНО - АДРЕСА ФИЛИАЛОВ (нормализуй распознанные адреса к этим вариантам):
{addresses_text}

ВАЖНО - СОТРУДНИКИ/ОПЕРАТОРЫ (исправляй имена к этим вариантам):
{admins_text}

Если в транскрипции упоминается адрес - ОБЯЗАТЕЛЬНО нормализуй его к ближайшему из списка выше.
Если упоминается имя администратора - исправь к правильному варианту из списка.
"""
        return prompt_section.strip()

