"""
Pydantic-модели для валидации конфигурации.

Fail-fast подход: при некорректном конфиге приложение не запустится.
"""

from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ASRPreprocessingConfig(BaseModel):
    """Конфигурация предобработки аудио."""

    wake_signal: dict = Field(
        default={"enabled": True, "samples": 8000, "rms": 0.0504},
        description="Параметры wake-signal для улучшения распознавания",
    )
    normalize_volume: bool = Field(
        default=True, description="Нормализация громкости (peak normalization)"
    )
    target_sample_rate: int = Field(
        default=16000, ge=8000, le=48000, description="Целевая частота дискретизации"
    )


class ASRConfig(BaseModel):
    """Конфигурация ASR (Whisper)."""

    model: str = Field(default="large-v3", description="Модель Whisper")
    device: str = Field(default="cuda", description="Устройство (cuda/cpu)")
    compute_type: str = Field(default="float16", description="Тип вычислений")
    cpu_threads: int = Field(default=16, ge=1, le=64, description="Потоки CPU")
    beam_size: int = Field(default=1, ge=1, le=10, description="Beam size")
    temperature: List[float] = Field(
        default=[0.0, 0.1, 0.3], description="Temperature fallback"
    )
    vad_filter: bool = Field(default=False, description="VAD фильтр")
    initial_prompt: str = Field(default="", description="Initial prompt")
    language: str = Field(default="ru", description="Язык транскрипции")
    preprocessing: ASRPreprocessingConfig = Field(
        default_factory=ASRPreprocessingConfig
    )

    @field_validator("device")
    @classmethod
    def validate_device(cls, v: str) -> str:
        """Только CUDA, никаких fallback."""
        if v not in ["cuda", "cpu"]:
            raise ValueError(f"Неподдерживаемое устройство: {v}")
        return v


class VLLMConfig(BaseModel):
    """Конфигурация VLLM для постобработки."""

    enabled: bool = Field(default=True, description="Включить VLLM постобработку")
    base_url: str = Field(
        default="http://localhost:8000/v1", description="URL VLLM API"
    )
    model: str = Field(
        default="models/LLM-30B-A3B-Instruct-2507-AWQ-4bit", description="Модель"
    )
    temperature: float = Field(default=0.1, ge=0.0, le=2.0)
    max_tokens: int = Field(default=8000, ge=100, le=32000)
    timeout: int = Field(default=120, ge=10, le=600, description="Таймаут в секундах")
    retry_attempts: int = Field(default=3, ge=1, le=10)
    retry_delay: float = Field(default=2.0, ge=0.5, le=10.0)


class CleanupConfig(BaseModel):
    """Конфигурация автоочистки."""

    enabled: bool = Field(default=True)
    input_retention_days: int = Field(default=30, ge=1, le=365)
    compress_after_days: int = Field(default=7, ge=1, le=180)
    max_disk_usage_percent: int = Field(default=80, ge=50, le=95)
    schedule_hour: int = Field(default=3, ge=0, le=23)
    archive_path: str = Field(default="./archive")


class PerformanceConfig(BaseModel):
    """Конфигурация производительности."""

    gpu_memory_fraction: float = Field(default=0.6, ge=0.1, le=1.0)
    concurrent_tasks: int = Field(default=1, ge=1, le=10)
    batch_size: int = Field(default=1, ge=1, le=16)


class PathsConfig(BaseModel):
    """Конфигурация путей."""

    input: str = Field(default="./input")
    output: str = Field(default="./output")
    metadata: str = Field(default="./metadata")
    archive: str = Field(default="./archive")
    logs: str = Field(default="./logs")


class LoggingConfig(BaseModel):
    """Конфигурация логирования."""

    level: str = Field(default="INFO")
    format: str = Field(
        default="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    files: dict = Field(
        default={"main": "logs/asr-watcher.log", "errors": "logs/errors.log"}
    )
    rotation: dict = Field(default={"max_bytes": 10485760, "backup_count": 5})

    @field_validator("level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Валидация уровня логирования."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Уровень логирования должен быть одним из {valid_levels}")
        return v.upper()


class QualityAnalysisConfig(BaseModel):
    """Конфигурация анализа качества обслуживания."""

    enabled: bool = Field(default=False, description="Включить анализ качества")
    auto_analyze: bool = Field(
        default=False, description="Автоматический анализ после транскрипции"
    )
    provider: str = Field(default="openrouter")
    model: str = Field(default="anthropic/claude-sonnet-4.5")
    api_key_env: str = Field(default="OPENROUTER_API_KEY")
    base_url: str = Field(default="https://openrouter.ai/api/v1")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    max_tokens: int = Field(default=16000, ge=1000, le=64000)
    timeout: int = Field(default=180, ge=30, le=600)
    retry_attempts: int = Field(default=3, ge=1, le=10)
    scripts: dict = Field(
        default={
            "script_type_a": "script_evaluation_type_A.md",
            "script_type_b": "script_evaluation_type_B.md",
        }
    )
    paths: dict = Field(
        default={
            "individual": "./quality_analysis/individual",
            "aggregated": "./quality_analysis/aggregated",
            "reports": "./quality_analysis/reports",
        }
    )


class GoogleSheetsConfig(BaseModel):
    """Конфигурация Google Sheets интеграции."""

    enabled: bool = Field(default=False)
    credentials_path: str = Field(default="./credentials/google_credentials.json")
    spreadsheet_id: str = Field(default="")
    worksheet_dashboard: str = Field(default="📊 Dashboard")
    worksheet_calls: str = Field(default="📞 Все звонки")
    worksheet_trends: str = Field(default="📈 Тренды")
    batch_sync_time: str = Field(default="23:00")
    dashboard_update_interval: int = Field(default=60, ge=10, le=1440)
    trends_update_day: str = Field(default="monday")


class AnalyticsConfig(BaseModel):
    """Конфигурация аналитики."""

    enabled: bool = Field(default=True)
    db_path: str = Field(default="./analytics/analytics.db")
    required_criteria: List[int] = Field(default=list(range(1, 21)))
    optional_criteria: List[int] = Field(default=list(range(21, 31)))
    err_rate_critical: float = Field(default=0.85, ge=0.0, le=1.0)
    miss_rate_critical: float = Field(default=0.80, ge=0.0, le=1.0)
    telegram: dict = Field(
        default={
            "enabled": False,
            "bot_token": "",
            "chat_id": "",
            "daily_time": "09:00",
            "weekly_day": "monday",
            "weekly_time": "10:00",
        }
    )


class SecurityConfig(BaseModel):
    """Конфигурация безопасности."""

    allowed_extensions: List[str] = Field(
        default=[".mp3", ".wav", ".m4a", ".ogg", ".flac"]
    )
    max_file_size_mb: int = Field(default=100, ge=1, le=1000)
    rate_limit_per_hour: int = Field(default=1000, ge=1, le=10000)


class AppConfig(BaseSettings):
    """Главная конфигурация приложения."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    asr: ASRConfig = Field(default_factory=ASRConfig)
    vllm: VLLMConfig = Field(default_factory=VLLMConfig)
    cleanup: CleanupConfig = Field(default_factory=CleanupConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    quality_analysis: QualityAnalysisConfig = Field(
        default_factory=QualityAnalysisConfig
    )
    analytics: AnalyticsConfig = Field(default_factory=AnalyticsConfig)
    google_sheets: GoogleSheetsConfig = Field(default_factory=GoogleSheetsConfig)

    def ensure_directories(self) -> None:
        """Создать необходимые директории."""
        for path_str in [
            self.paths.input,
            self.paths.output,
            self.paths.metadata,
            self.paths.archive,
            self.paths.logs,
        ]:
            Path(path_str).mkdir(parents=True, exist_ok=True)
        
        # Директории для анализа качества
        if self.quality_analysis.enabled or True:  # Всегда создавать
            for path_str in self.quality_analysis.paths.values():
                Path(path_str).mkdir(parents=True, exist_ok=True)

