"""
ScanovichAI Portfolio - Data Processor Tests

Unit тесты для модуля обработки данных демонстрируют лучшие практики.

Author: Aleksandr Mordvinov
Email: contact@scanovich.ai
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch
import tempfile
import json

from src.data_processor_example import (
    DataProcessor,
    AnalyticsEngine,
    ProcessingConfig,
    DataQualityReport
)


class TestProcessingConfig:
    """Тесты конфигурации обработки"""

    def test_default_config(self):
        """Тест конфигурации по умолчанию"""
        config = ProcessingConfig()

        assert config.batch_size == 1000
        assert config.max_features == 1000
        assert config.validation_split == 0.2
        assert config.random_state == 42
        assert config.scaling_method == "standard"
        assert config.missing_value_strategy == "mean"

    def test_custom_config(self):
        """Тест пользовательской конфигурации"""
        config = ProcessingConfig(
            batch_size=500,
            missing_value_strategy="median",
            scaling_method="minmax"
        )

        assert config.batch_size == 500
        assert config.missing_value_strategy == "median"
        assert config.scaling_method == "minmax"


class TestDataProcessor:
    """Тесты процессора данных"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.config = ProcessingConfig(
            batch_size=100,
            missing_value_strategy="mean",
            scaling_method="standard"
        )
        self.processor = DataProcessor(self.config)

    def test_analyze_data_quality(self):
        """Тест анализа качества данных"""
        # Arrange
        np.random.seed(42)
        data = pd.DataFrame({
            'feature_1': np.random.normal(0, 1, 100),
            'feature_2': np.random.normal(5, 2, 100),
            'category': np.random.choice(['A', 'B', 'C'], 100)
        })

        # Act
        quality_report = self.processor.analyze_data_quality(data)

        # Assert
        assert isinstance(quality_report, DataQualityReport)
        assert quality_report.total_rows == 100
        assert quality_report.total_columns == 3
        assert quality_report.duplicates == 0  # Нет дубликатов в случайных данных
        assert quality_report.quality_score > 0.8  # Высокое качество
        assert 'feature_1' in quality_report.data_types
        assert 'feature_2' in quality_report.missing_values

    def test_analyze_data_quality_with_missing(self):
        """Тест анализа качества с пропущенными значениями"""
        # Arrange
        data = pd.DataFrame({
            'feature_1': [1, 2, np.nan, 4, 5] * 20,
            'feature_2': [1, 2, 3, 4, np.nan] * 20,
            'category': ['A', 'B', 'C', 'A', 'B'] * 20
        })

        # Act
        quality_report = self.processor.analyze_data_quality(data)

        # Assert
        assert quality_report.missing_values['feature_1'] == 20
        assert quality_report.missing_values['feature_2'] == 20
        assert quality_report.missing_percentage['feature_1'] == 20.0
        assert quality_report.quality_score < 0.9  # Низкое качество из-за пропусков

    def test_preprocess_data_numerical(self):
        """Тест предобработки числовых данных"""
        # Arrange
        data = pd.DataFrame({
            'feature_1': np.random.normal(0, 1, 100),
            'feature_2': np.random.normal(5, 2, 100),
            'target': np.random.choice([0, 1], 100)
        })

        # Act
        features, targets = self.processor.preprocess_data(data, 'target')

        # Assert
        assert self.processor.is_fitted is True
        assert len(self.processor.feature_columns) == 2
        assert self.processor.target_column == 'target'
        assert features.shape == (100, 2)
        assert targets.shape == (100,)

        # Проверяем масштабирование (среднее ≈ 0, std ≈ 1)
        assert abs(features.values.mean()) < 0.1
        assert abs(features.values.std() - 1.0) < 0.1

    def test_preprocess_data_categorical(self):
        """Тест предобработки категориальных данных"""
        # Arrange
        data = pd.DataFrame({
            'category': ['A', 'B', 'C', 'A', 'B'] * 20,
            'numeric': np.random.normal(0, 1, 100),
            'target': np.random.choice([0, 1], 100)
        })

        # Act
        features, targets = self.processor.preprocess_data(data, 'target')

        # Assert
        assert self.processor.is_fitted is True
        assert 'category' in self.processor.encoders
        assert features.shape == (100, 2)

        # Проверяем кодирование категориальных признаков
        unique_values = np.unique(features.iloc[:, 0].values)
        assert len(unique_values) <= 3  # Максимум 3 категории

    def test_handle_missing_values_mean(self):
        """Тест обработки пропусков средним"""
        # Arrange
        data = pd.DataFrame({
            'feature_1': [1, 2, np.nan, 4, 5],
            'feature_2': [1, 2, 3, 4, np.nan]
        })

        # Act
        processed = self.processor._handle_missing_values(data)

        # Assert
        assert processed['feature_1'].isnull().sum() == 0
        assert processed['feature_2'].isnull().sum() == 0

        # Проверяем что пропуски заполнены средним
        expected_mean_1 = (1 + 2 + 4 + 5) / 4  # 3.0
        assert processed.loc[2, 'feature_1'] == expected_mean_1

    def test_handle_missing_values_mode(self):
        """Тест обработки пропусков модой"""
        # Arrange
        self.config.missing_value_strategy = "mode"
        processor = DataProcessor(self.config)

        data = pd.DataFrame({
            'category': ['A', 'B', 'A', 'A', np.nan]
        })

        # Act
        processed = processor._handle_missing_values(data)

        # Assert
        assert processed['category'].isnull().sum() == 0
        assert processed.loc[4, 'category'] == 'A'  # Мода = 'A'

    def test_prepare_training_data(self):
        """Тест подготовки данных для обучения"""
        # Arrange
        data = pd.DataFrame({
            'feature_1': np.random.normal(0, 1, 100),
            'feature_2': np.random.normal(5, 2, 100),
            'target': np.random.choice([0, 1], 100)
        })

        # Act
        X_train, X_val, y_train, y_val = self.processor.prepare_training_data(data, 'target')

        # Assert
        assert X_train.shape[0] == 80  # 80% для обучения
        assert X_val.shape[0] == 20    # 20% для валидации
        assert y_train.shape[0] == 80
        assert y_val.shape[0] == 20

        # Проверяем что данные масштабированы
        assert abs(X_train.mean()) < 0.1
        assert abs(X_train.std() - 1.0) < 0.1

    def test_transform_for_inference(self):
        """Тест преобразования для инференса"""
        # Arrange
        train_data = pd.DataFrame({
            'feature_1': np.random.normal(0, 1, 50),
            'feature_2': np.random.normal(5, 2, 50)
        })

        self.processor.preprocess_data(train_data)

        test_data = pd.DataFrame({
            'feature_1': [1.0, 2.0],
            'feature_2': [6.0, 7.0]
        })

        # Act
        transformed = self.processor.transform_for_inference(test_data)

        # Assert
        assert transformed.shape == (2, 2)
        # Проверяем что данные масштабированы теми же параметрами
        assert abs(transformed.mean()) < 1.0  # Может быть не 0 из-за разных данных

    def test_save_load_state(self):
        """Тест сохранения и загрузки состояния"""
        # Arrange
        train_data = pd.DataFrame({
            'feature_1': np.random.normal(0, 1, 50),
            'feature_2': np.random.normal(5, 2, 50)
        })

        self.processor.preprocess_data(train_data)

        # Act & Assert
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            self.processor.save_preprocessing_state(f.name)

            # Проверяем что файл создан
            import os
            assert os.path.exists(f.name)

            # Создаем новый процессор и загружаем состояние
            new_processor = DataProcessor()
            new_processor.load_preprocessing_state(f.name)

            # Проверяем что состояние восстановлено
            assert new_processor.is_fitted is True
            assert len(new_processor.feature_columns) == 2
            assert new_processor.config.batch_size == self.config.batch_size

    def test_unfitted_processor_error(self):
        """Тест ошибки при использовании неподготовленного процессора"""
        # Arrange
        data = pd.DataFrame({
            'feature_1': [1, 2, 3],
            'target': [0, 1, 0]
        })

        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            self.processor.prepare_training_data(data, 'target')

        assert "must be fitted" in str(exc_info.value).lower()

        with pytest.raises(ValueError) as exc_info:
            self.processor.transform_for_inference(data)

        assert "must be fitted" in str(exc_info.value).lower()


class TestAnalyticsEngine:
    """Тесты движка аналитики"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.analytics = AnalyticsEngine()

    def test_log_prediction(self):
        """Тест логирования предсказаний"""
        # Act
        self.analytics.log_prediction(
            prediction_id="test_1",
            model_version="v1.0",
            confidence=0.95,
            processing_time=0.5
        )

        # Assert
        assert len(self.analytics.predictions_history) == 1
        record = self.analytics.predictions_history[0]

        assert record["id"] == "test_1"
        assert record["model_version"] == "v1.0"
        assert record["confidence"] == 0.95
        assert record["processing_time"] == 0.5
        assert "timestamp" in record

    def test_calculate_metrics_empty(self):
        """Тест расчета метрик при пустой истории"""
        # Act
        metrics = self.analytics.calculate_metrics()

        # Assert
        assert "message" in metrics
        assert "No predictions" in metrics["message"]

    def test_calculate_metrics_with_data(self):
        """Тест расчета метрик с данными"""
        from datetime import datetime, timedelta

        # Arrange
        base_time = datetime.now()
        for i in range(5):
            self.analytics.log_prediction(
                prediction_id=f"pred_{i}",
                model_version="v1.0",
                confidence=0.8 + i * 0.04,  # 0.8, 0.84, 0.88, 0.92, 0.96
                processing_time=0.1 + i * 0.1,  # 0.1, 0.2, 0.3, 0.4, 0.5
                timestamp=base_time - timedelta(minutes=i)
            )

        # Act
        metrics = self.analytics.calculate_metrics(timedelta(hours=1))

        # Assert
        assert metrics["total_predictions"] == 5
        assert metrics["avg_confidence"] == 0.88  # (0.8 + 0.84 + 0.88 + 0.92 + 0.96) / 5
        assert metrics["min_confidence"] == 0.8
        assert metrics["max_confidence"] == 0.96
        assert metrics["avg_processing_time"] == 0.3  # (0.1 + 0.2 + 0.3 + 0.4 + 0.5) / 5
        assert "v1.0" in metrics["model_versions"]

    def test_generate_report(self):
        """Тест генерации отчета"""
        # Arrange
        self.analytics.log_prediction("test", "v1.0", 0.95, 0.5)

        # Act
        self.analytics.calculate_metrics(timedelta(hours=1))
        report = self.analytics.generate_report()

        # Assert
        assert isinstance(report, str)
        assert "AI Analytics Report" in report
        assert "Total Predictions: 1" in report
        assert "Average Confidence: 0.950" in report
        assert "v1.0" in report

    def test_generate_report_no_metrics(self):
        """Тест генерации отчета без метрик"""
        # Act
        report = self.analytics.generate_report()

        # Assert
        assert "No metrics available" in report


class TestDataQualityReport:
    """Тесты отчета о качестве данных"""

    def test_quality_score_calculation(self):
        """Тест расчета балла качества"""
        # Arrange
        data = pd.DataFrame({
            'good_feature': [1, 2, 3, 4, 5] * 20,  # Нет пропусков, нет выбросов
            'bad_feature': [1, 2, np.nan, 4, 5] * 20  # 20% пропусков
        })

        processor = DataProcessor()

        # Act
        report = processor.analyze_data_quality(data)

        # Assert
        assert 0 <= report.quality_score <= 1
        assert report.missing_values['bad_feature'] == 20
        assert report.missing_percentage['bad_feature'] == 20.0

    def test_outliers_detection(self):
        """Тест обнаружения выбросов"""
        # Arrange
        # Создаем данные с выбросами
        normal_data = np.random.normal(0, 1, 98)
        outlier_data = np.array([10, -10])  # Выбросы
        data = np.concatenate([normal_data, outlier_data])

        df = pd.DataFrame({'feature': data})
        processor = DataProcessor()

        # Act
        report = processor.analyze_data_quality(df)

        # Assert
        assert report.outliers['feature'] == 2  # Два выброса
        assert report.quality_score < 1.0  # Качество снижено из-за выбросов


class TestIntegration:
    """Интеграционные тесты"""

    def test_end_to_end_processing(self):
        """Тест полного цикла обработки"""
        # Arrange
        np.random.seed(42)
        data = pd.DataFrame({
            'feature_1': np.random.normal(0, 1, 100),
            'feature_2': np.random.normal(5, 2, 100),
            'category': np.random.choice(['A', 'B', 'C'], 100),
            'target': np.random.choice([0, 1], 100)
        })

        # Добавляем пропуски и дубликаты
        data.loc[0:10, 'feature_1'] = np.nan
        data.loc[50:55, 'category'] = np.nan
        data = pd.concat([data, data.iloc[0:5]], ignore_index=True)  # Дубликаты

        processor = DataProcessor()

        # Act
        # 1. Анализ качества
        quality_before = processor.analyze_data_quality(data)
        print(f"Quality before: {quality_before.quality_score:.3f}")

        # 2. Предварительная обработка
        features, targets = processor.preprocess_data(data, 'target')

        # 3. Подготовка данных для обучения
        X_train, X_val, y_train, y_val = processor.prepare_training_data(data, 'target')

        # 4. Проверка качества после обработки
        processed_data = pd.concat([features, targets], axis=1)
        quality_after = processor.analyze_data_quality(processed_data)
        print(f"Quality after: {quality_after.quality_score:.3f}")

        # Assert
        assert quality_before.quality_score < quality_after.quality_score
        assert features.shape[1] == 3  # feature_1, feature_2, category
        assert X_train.shape[0] + X_val.shape[0] == 100  # 100 строк (дубликаты удалены)
        assert self.processor.is_fitted is True

    def test_state_persistence(self):
        """Тест сохранения состояния процессора"""
        # Arrange
        data = pd.DataFrame({
            'feature_1': np.random.normal(0, 1, 50),
            'feature_2': np.random.normal(5, 2, 50),
            'target': np.random.choice([0, 1], 50)
        })

        processor = DataProcessor()
        processor.preprocess_data(data, 'target')

        # Act
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            processor.save_preprocessing_state(f.name)

            # Создаем новый процессор
            new_processor = DataProcessor()
            new_processor.load_preprocessing_state(f.name)

            # Проверяем что состояние восстановлено
            test_data = data.iloc[:5].drop('target', axis=1)
            transformed_new = new_processor.transform_for_inference(test_data)

        # Assert
        assert new_processor.is_fitted is True
        assert len(new_processor.feature_columns) == 2
        assert transformed_new.shape == (5, 2)


# Фикстуры
@pytest.fixture
def sample_dataframe():
    """Фикстура с тестовыми данными"""
    np.random.seed(42)
    return pd.DataFrame({
        'numeric_1': np.random.normal(0, 1, 100),
        'numeric_2': np.random.normal(5, 2, 100),
        'categorical': np.random.choice(['A', 'B', 'C'], 100),
        'target': np.random.choice([0, 1], 100)
    })


@pytest.fixture
def processor_with_config():
    """Фикстура процессора с пользовательской конфигурацией"""
    config = ProcessingConfig(
        batch_size=50,
        missing_value_strategy="median",
        validation_split=0.3
    )
    return DataProcessor(config)
