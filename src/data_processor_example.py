"""
ScanovichAI Portfolio - Data Processing Example

Модуль демонстрирует лучшие практики обработки и анализа данных в AI системах.

Author: Aleksandr Mordvinov
Email: contact@scanovich.ai
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json

import pandas as pd
import numpy as np
from pydantic import BaseModel, Field, validator
import torch
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ProcessingConfig:
    """Конфигурация обработки данных"""
    batch_size: int = 1000
    max_features: int = 1000
    validation_split: float = 0.2
    random_state: int = 42
    scaling_method: str = "standard"
    missing_value_strategy: str = "mean"


class DataQualityReport(BaseModel):
    """Отчет о качестве данных"""
    total_rows: int = Field(..., description="Общее количество строк")
    total_columns: int = Field(..., description="Общее количество колонок")
    missing_values: Dict[str, int] = Field(..., description="Пропущенные значения по колонкам")
    missing_percentage: Dict[str, float] = Field(..., description="Процент пропусков по колонкам")
    data_types: Dict[str, str] = Field(..., description="Типы данных по колонкам")
    duplicates: int = Field(..., description="Количество дубликатов")
    outliers: Dict[str, int] = Field(..., description="Количество выбросов по колонкам")
    quality_score: float = Field(..., description="Общий балл качества данных (0-1)")


class DataProcessor:
    """Процессор данных для AI систем"""

    def __init__(self, config: ProcessingConfig = None):
        self.config = config or ProcessingConfig()
        self.scalers = {}
        self.encoders = {}
        self.feature_columns = []
        self.target_column = None
        self.is_fitted = False

    def analyze_data_quality(self, data: pd.DataFrame) -> DataQualityReport:
        """Анализ качества данных"""
        logger.info(f"Analyzing data quality for {len(data)} rows")

        # Пропущенные значения
        missing_values = data.isnull().sum().to_dict()
        missing_percentage = (data.isnull().sum() / len(data) * 100).to_dict()

        # Дубликаты
        duplicates = data.duplicated().sum()

        # Выбросы (IQR метод)
        outliers = {}
        for col in data.select_dtypes(include=[np.number]).columns:
            Q1 = data[col].quantile(0.25)
            Q3 = data[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outliers[col] = ((data[col] < lower_bound) | (data[col] > upper_bound)).sum()

        # Общий балл качества
        quality_score = self._calculate_quality_score(missing_percentage, duplicates, outliers, len(data))

        return DataQualityReport(
            total_rows=len(data),
            total_columns=len(data.columns),
            missing_values=missing_values,
            missing_percentage=missing_percentage,
            data_types=data.dtypes.astype(str).to_dict(),
            duplicates=duplicates,
            outliers=outliers,
            quality_score=quality_score
        )

    def _calculate_quality_score(
        self,
        missing_percentage: Dict[str, float],
        duplicates: int,
        outliers: Dict[str, int],
        total_rows: int
    ) -> float:
        """Расчет общего балла качества данных"""
        # Штраф за пропуски
        max_missing_penalty = sum(1.0 for v in missing_percentage.values() if v > 50)
        missing_penalty = sum(min(v/100, 1.0) for v in missing_percentage.values()) / len(missing_percentage)

        # Штраф за дубликаты
        duplicate_penalty = min(duplicates / total_rows, 1.0) if total_rows > 0 else 0

        # Штраф за выбросы
        outlier_penalty = sum(min(count / total_rows, 0.1) for count in outliers.values()) / len(outliers) if outliers else 0

        # Общий балл (чем ниже штрафы, тем выше качество)
        total_penalty = (missing_penalty + duplicate_penalty + outlier_penalty) / 3
        return max(0.0, 1.0 - total_penalty)

    def preprocess_data(
        self,
        data: pd.DataFrame,
        target_column: Optional[str] = None,
        fit: bool = True
    ) -> Tuple[pd.DataFrame, Optional[pd.Series]]:
        """Предварительная обработка данных"""
        logger.info(f"Preprocessing data with shape {data.shape}")

        # Копирование данных
        processed_data = data.copy()

        # Обработка пропущенных значений
        processed_data = self._handle_missing_values(processed_data)

        # Определение признаков и цели
        if target_column and target_column in processed_data.columns:
            self.target_column = target_column
            feature_data = processed_data.drop(columns=[target_column])
            target_data = processed_data[target_column]
        else:
            feature_data = processed_data
            target_data = None

        # Кодирование категориальных признаков
        feature_data = self._encode_categorical_features(feature_data, fit)

        # Масштабирование числовых признаков
        feature_data = self._scale_numerical_features(feature_data, fit)

        self.feature_columns = feature_data.columns.tolist()
        self.is_fitted = True

        logger.info(f"Preprocessing completed. Features: {len(self.feature_columns)}")

        return feature_data, target_data

    def _handle_missing_values(self, data: pd.DataFrame) -> pd.DataFrame:
        """Обработка пропущенных значений"""
        processed_data = data.copy()

        for column in processed_data.columns:
            if processed_data[column].isnull().sum() > 0:
                if self.config.missing_value_strategy == "mean" and processed_data[column].dtype in ['int64', 'float64']:
                    processed_data[column].fillna(processed_data[column].mean(), inplace=True)
                elif self.config.missing_value_strategy == "median" and processed_data[column].dtype in ['int64', 'float64']:
                    processed_data[column].fillna(processed_data[column].median(), inplace=True)
                elif self.config.missing_value_strategy == "mode":
                    processed_data[column].fillna(processed_data[column].mode().iloc[0], inplace=True)
                elif self.config.missing_value_strategy == "drop":
                    processed_data.dropna(subset=[column], inplace=True)
                else:
                    # Для категориальных или по умолчанию - наиболее частое значение
                    processed_data[column].fillna(processed_data[column].mode().iloc[0], inplace=True)

        return processed_data

    def _encode_categorical_features(self, data: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """Кодирование категориальных признаков"""
        processed_data = data.copy()
        categorical_columns = processed_data.select_dtypes(include=['object']).columns

        for col in categorical_columns:
            if fit:
                self.encoders[col] = LabelEncoder()
                processed_data[col] = self.encoders[col].fit_transform(processed_data[col].astype(str))
            else:
                if col in self.encoders:
                    processed_data[col] = self.encoders[col].transform(processed_data[col].astype(str))
                else:
                    # Для новых данных используем most frequent value
                    processed_data[col] = processed_data[col].astype(str).map(
                        lambda x: list(processed_data[col].astype(str).mode())[0] if pd.isna(x) else x
                    )

        return processed_data

    def _scale_numerical_features(self, data: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """Масштабирование числовых признаков"""
        processed_data = data.copy()
        numerical_columns = processed_data.select_dtypes(include=['int64', 'float64']).columns

        for col in numerical_columns:
            if fit:
                if self.config.scaling_method == "standard":
                    self.scalers[col] = StandardScaler()
                    processed_data[col] = self.scalers[col].fit_transform(processed_data[col].values.reshape(-1, 1)).flatten()
                # Добавьте другие методы масштабирования по необходимости
            else:
                if col in self.scalers:
                    processed_data[col] = self.scalers[col].transform(processed_data[col].values.reshape(-1, 1)).flatten()

        return processed_data

    def prepare_training_data(
        self,
        data: pd.DataFrame,
        target_column: str,
        validation_split: Optional[float] = None
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Подготовка данных для обучения модели"""
        if not self.is_fitted:
            raise ValueError("DataProcessor must be fitted before preparing training data")

        # Предварительная обработка
        features, targets = self.preprocess_data(data, target_column, fit=False)

        # Разделение на train/validation
        split_ratio = validation_split or self.config.validation_split
        X_train, X_val, y_train, y_val = train_test_split(
            features.values,
            targets.values,
            test_size=split_ratio,
            random_state=self.config.random_state,
            stratify=targets.values if len(targets.unique()) < 20 else None
        )

        logger.info(f"Training data prepared: {X_train.shape[0]} train, {X_val.shape[0]} validation samples")

        return X_train, X_val, y_train, y_val

    def transform_for_inference(self, data: pd.DataFrame) -> np.ndarray:
        """Преобразование данных для инференса"""
        if not self.is_fitted:
            raise ValueError("DataProcessor must be fitted before transforming data")

        features, _ = self.preprocess_data(data, fit=False)
        return features.values

    def save_preprocessing_state(self, filepath: str) -> None:
        """Сохранение состояния предобработки"""
        state = {
            "config": self.config.__dict__,
            "scalers": {k: v.__dict__ if hasattr(v, '__dict__') else str(v) for k, v in self.scalers.items()},
            "encoders": {k: v.__dict__ if hasattr(v, '__dict__') else str(v) for k, v in self.encoders.items()},
            "feature_columns": self.feature_columns,
            "target_column": self.target_column,
            "is_fitted": self.is_fitted
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

        logger.info(f"Preprocessing state saved to {filepath}")

    def load_preprocessing_state(self, filepath: str) -> None:
        """Загрузка состояния предобработки"""
        with open(filepath, 'r', encoding='utf-8') as f:
            state = json.load(f)

        self.config = ProcessingConfig(**state["config"])
        # В реальности здесь была бы загрузка scalers и encoders
        self.feature_columns = state["feature_columns"]
        self.target_column = state["target_column"]
        self.is_fitted = state["is_fitted"]

        logger.info(f"Preprocessing state loaded from {filepath}")


class AnalyticsEngine:
    """Движок аналитики для обработки результатов AI"""

    def __init__(self):
        self.metrics = {}
        self.predictions_history = []

    def log_prediction(
        self,
        prediction_id: str,
        model_version: str,
        confidence: float,
        processing_time: float,
        timestamp: Optional[datetime] = None
    ) -> None:
        """Логирование предсказания"""
        if timestamp is None:
            timestamp = datetime.now()

        prediction_record = {
            "id": prediction_id,
            "model_version": model_version,
            "confidence": confidence,
            "processing_time": processing_time,
            "timestamp": timestamp.isoformat()
        }

        self.predictions_history.append(prediction_record)
        logger.info(f"Prediction logged: {prediction_id} (confidence: {confidence:.3f})")

    def calculate_metrics(self, time_window: timedelta = timedelta(hours=1)) -> Dict[str, Any]:
        """Расчет метрик за период"""
        cutoff_time = datetime.now() - time_window
        recent_predictions = [
            p for p in self.predictions_history
            if datetime.fromisoformat(p["timestamp"]) > cutoff_time
        ]

        if not recent_predictions:
            return {"message": "No predictions in time window"}

        confidences = [p["confidence"] for p in recent_predictions]
        processing_times = [p["processing_time"] for p in recent_predictions]

        metrics = {
            "total_predictions": len(recent_predictions),
            "avg_confidence": np.mean(confidences),
            "median_confidence": np.median(confidences),
            "min_confidence": np.min(confidences),
            "max_confidence": np.max(confidences),
            "avg_processing_time": np.mean(processing_times),
            "median_processing_time": np.median(processing_times),
            "time_window_hours": time_window.total_seconds() / 3600,
            "model_versions": list(set(p["model_version"] for p in recent_predictions))
        }

        self.metrics = metrics
        return metrics

    def generate_report(self) -> str:
        """Генерация аналитического отчета"""
        if not self.metrics:
            return "No metrics available. Run calculate_metrics() first."

        report = f"""
# 📊 AI Analytics Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📈 Performance Metrics

- **Total Predictions:** {self.metrics['total_predictions']}
- **Average Confidence:** {self.metrics['avg_confidence']:.3f}
- **Median Confidence:** {self.metrics['median_confidence']:.3f}
- **Processing Time:** {self.metrics['avg_processing_time']:.3f}s avg

## 🔄 Model Usage

- **Active Models:** {', '.join(self.metrics['model_versions'])}
- **Time Window:** {self.metrics['time_window_hours']:.1f} hours

## ⚡ Performance Insights

"""
        if self.metrics['avg_confidence'] < 0.7:
            report += "⚠️ **Low confidence detected** - consider model retraining or data quality review\n"
        if self.metrics['avg_processing_time'] > 1.0:
            report += "⚠️ **High processing time** - consider model optimization\n"

        report += "\n*Report generated by ScanovichAI Analytics Engine*"

        return report


# Пример использования
async def main():
    """Демонстрация использования"""
    logger.info("Starting data processing example...")

    # Создание тестовых данных
    np.random.seed(42)
    n_samples = 1000

    data = pd.DataFrame({
        'feature_1': np.random.normal(0, 1, n_samples),
        'feature_2': np.random.normal(5, 2, n_samples),
        'category': np.random.choice(['A', 'B', 'C'], n_samples),
        'target': np.random.choice([0, 1], n_samples, p=[0.7, 0.3])
    })

    # Добавление пропущенных значений
    data.loc[np.random.choice(n_samples, 50, replace=False), 'feature_1'] = np.nan
    data.loc[np.random.choice(n_samples, 30, replace=False), 'category'] = np.nan

    # Инициализация процессора
    config = ProcessingConfig(
        batch_size=100,
        missing_value_strategy="mean",
        scaling_method="standard"
    )

    processor = DataProcessor(config)
    analytics = AnalyticsEngine()

    # Анализ качества данных
    quality_report = processor.analyze_data_quality(data)
    print(f"Data Quality Score: {quality_report.quality_score:.2f}")
    print(f"Missing values: {sum(quality_report.missing_values.values())}")

    # Предварительная обработка
    X_train, X_val, y_train, y_val = processor.prepare_training_data(data, 'target')

    print(f"Training data shape: {X_train.shape}")
    print(f"Validation data shape: {X_val.shape}")

    # Имитация предсказаний
    for i in range(10):
        prediction_id = f"pred_{i}"
        confidence = np.random.uniform(0.5, 0.95)
        processing_time = np.random.uniform(0.1, 2.0)

        analytics.log_prediction(
            prediction_id=prediction_id,
            model_version="demo-v1.0",
            confidence=confidence,
            processing_time=processing_time
        )

        await asyncio.sleep(0.1)  # Имитация асинхронной обработки

    # Расчет метрик
    metrics = analytics.calculate_metrics(timedelta(minutes=5))
    print(f"Average confidence: {metrics['avg_confidence']:.3f}")

    # Генерация отчета
    report = analytics.generate_report()
    print(report)

    # Сохранение состояния
    processor.save_preprocessing_state("preprocessing_state.json")

    logger.info("Data processing example completed successfully")


if __name__ == "__main__":
    asyncio.run(main())
