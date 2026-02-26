"""
CloudPBX RT Calls Downloader - Configuration module (pydantic-settings).

Loads from .env and config.yaml. DOWNLOAD_DIR for ASR integration: use ../../input
when running from voip/rostelcom to save directly to ASR input folder.
"""

from pathlib import Path
from typing import Optional

import os

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class CloudPBXConfig(BaseSettings):
    """CloudPBX API configuration."""

    model_config = SettingsConfigDict(env_prefix="CLOUDPBX_", extra="ignore")
    base_url: str = "https://p2.cloudpbx.rt.ru/webapi"
    login: Optional[str] = None
    password: Optional[str] = None
    domain: Optional[str] = None


class DownloadConfig(BaseSettings):
    """Download settings. DOWNLOAD_DIR: use ../../input for ASR integration."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")
    download_dir: Path = Field(default=Path("./downloads"))
    check_interval: int = Field(default=300, alias="CHECK_INTERVAL")
    lookback_hours: int = Field(default=24, alias="LOOKBACK_HOURS")

    @field_validator("download_dir", mode="before")
    @classmethod
    def validate_download_dir(cls, v):
        import os

        if v is None or (isinstance(v, Path) and str(v) == "."):
            v = os.getenv("DOWNLOAD_DIR", "./downloads")
        if isinstance(v, str):
            path = Path(v)
            path.mkdir(parents=True, exist_ok=True)
            return path
        return v


class FilterConfig(BaseSettings):
    """Call filters."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")
    min_duration_seconds: int = Field(default=180, alias="MIN_DURATION_SECONDS")
    only_incoming: bool = Field(default=True, alias="ONLY_INCOMING")
    records_per_page: int = Field(default=100, alias="RECORDS_PER_PAGE")


class DatabaseConfig(BaseSettings):
    """Database path."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")
    database_path: Path = Field(default=Path("./cloudpbx_calls.db"), alias="DATABASE_PATH")


class LoggingConfig(BaseSettings):
    """Logging settings."""

    model_config = SettingsConfigDict(env_prefix="LOG_", extra="ignore")
    level: str = Field(default="INFO", alias="LOG_LEVEL")
    format: str = "%(asctime)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s"
    log_file: Optional[str] = Field(default="watcher.log", alias="LOG_FILE")


class AppConfig(BaseSettings):
    """Main application config."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    cloudpbx: CloudPBXConfig = Field(default_factory=CloudPBXConfig)
    download: DownloadConfig = Field(default_factory=DownloadConfig)

    @model_validator(mode="after")
    def apply_download_dir_from_env(self):
        if "DOWNLOAD_DIR" in os.environ:
            path = Path(os.environ["DOWNLOAD_DIR"])
            path.mkdir(parents=True, exist_ok=True)
            self.download.download_dir = path
        return self
    filters: FilterConfig = Field(default_factory=FilterConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @classmethod
    def load_city_accounts(cls, max_cities: int = 16):
        """Load city accounts from CITY_N_* env vars."""
        import os

        configs = []
        for i in range(1, max_cities + 1):
            name = os.getenv(f"CITY_{i}_NAME")
            if not name:
                continue
            login = os.getenv(f"CITY_{i}_LOGIN")
            password = os.getenv(f"CITY_{i}_PASSWORD")
            domain = os.getenv(f"CITY_{i}_DOMAIN")
            if all([login, password, domain]):
                configs.append(
                    type(
                        "CityConfig",
                        (),
                        {
                            "name": name,
                            "login": login,
                            "password": password,
                            "domain": domain,
                        },
                    )()
                )
        return configs


_config_instance: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Singleton config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = AppConfig()
    return _config_instance
