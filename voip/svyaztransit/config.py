"""
Stranzit Audio Downloader - Configuration module (pydantic-settings).

DOWNLOAD_DIR: use ../../input for ASR integration when running from voip/svyaztransit.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class StranzitConfig(BaseSettings):
    """Stranzit LK credentials."""

    model_config = SettingsConfigDict(env_prefix="STRANZIT_", extra="ignore")
    username: Optional[str] = None
    password: Optional[str] = None


class DownloadConfig(BaseSettings):
    """Download settings."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")
    download_dir: Path = Field(default=Path("./downloads"))

    @field_validator("download_dir", mode="before")
    @classmethod
    def validate_download_dir(cls, v):
        if v is None or (isinstance(v, Path) and str(v) == "."):
            v = os.getenv("DOWNLOAD_DIR", "./downloads")
        if isinstance(v, str):
            path = Path(v)
            path.mkdir(parents=True, exist_ok=True)
            return path
        return v

    check_interval: int = Field(default=300, alias="CHECK_INTERVAL")


class FilterConfig(BaseSettings):
    """Call record filters."""

    model_config = SettingsConfigDict(env_prefix="CALL_FILTER_", extra="ignore")
    start: str = Field(default="today_start", alias="START")
    end: str = Field(default="now", alias="END")
    direction: str = Field(default="incoming", alias="DIRECTION")
    duration_op: str = Field(default=">=", alias="DURATION_OP")
    duration: str = Field(default="00:03:00", alias="DURATION")
    records_per_page: int = Field(default=50, alias="RECORDS_PER_PAGE")
    phone_number: Optional[str] = Field(default=None, alias="PHONE_NUMBER")


class DatabaseConfig(BaseSettings):
    """Database path."""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")
    database_path: Path = Field(default=Path("./stranzit_calls.db"), alias="DATABASE_PATH")


class LoggingConfig(BaseSettings):
    """Logging settings."""

    model_config = SettingsConfigDict(env_prefix="LOG_", extra="ignore")
    level: str = Field(default="INFO", alias="LEVEL")
    format: str = "%(asctime)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s"
    log_file: Optional[str] = Field(default="watcher.log", alias="FILE")


class AppConfig(BaseSettings):
    """Main application config."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    stranzit: StranzitConfig = Field(default_factory=StranzitConfig)
    download: DownloadConfig = Field(default_factory=DownloadConfig)
    filters: FilterConfig = Field(default_factory=FilterConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    @model_validator(mode="after")
    def apply_download_dir_from_env(self):
        if "DOWNLOAD_DIR" in os.environ:
            path = Path(os.environ["DOWNLOAD_DIR"])
            path.mkdir(parents=True, exist_ok=True)
            self.download.download_dir = path
        return self


_config_instance: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """Singleton config instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = AppConfig()
    return _config_instance
