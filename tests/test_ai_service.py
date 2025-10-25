"""
ScanovichAI Portfolio - AI Service Tests

Unit и integration тесты для AI сервиса демонстрируют лучшие практики тестирования.

Author: Aleksandr Mordvinov
Email: contact@scanovich.ai
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import numpy as np
import torch
from httpx import AsyncClient

from src.ai_service_example import (
    PredictionRequest,
    PredictionResponse,
    ModelManager,
    SimpleModelManager,
    AIService,
    app
)


class TestModelManager:
    """Тесты для ModelManager"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.model_manager = SimpleModelManager(model_path="/test/models")

    @pytest.mark.asyncio
    async def test_model_initialization(self):
        """Тест инициализации модели"""
        # Arrange
        with patch.object(torch, 'cuda') as mock_cuda:
            mock_cuda.is_available.return_value = False

            # Act
            await self.model_manager.load_model()

            # Assert
            assert self.model_manager.model is not None
            assert self.model_manager.model_version == "demo-v1.0"
            assert self.model_manager.device == "cpu"

    @pytest.mark.asyncio
    async def test_gpu_detection(self):
        """Тест определения GPU"""
        # Arrange
        with patch.object(torch, 'cuda') as mock_cuda:
            mock_cuda.is_available.return_value = True
            mock_cuda.get_device_name.return_value = "NVIDIA RTX 5090"

            # Act
            await self.model_manager.load_model()

            # Assert
            assert self.model_manager.device == "cuda"
            mock_cuda.is_available.assert_called_once()

    @pytest.mark.asyncio
    async def test_model_prediction(self):
        """Тест предсказания модели"""
        # Arrange
        await self.model_manager.load_model()
        test_data = np.random.randn(1, 10)

        # Act
        result = await self.model_manager.predict(test_data)

        # Assert
        assert isinstance(result, dict)
        assert "class" in result
        assert "probabilities" in result
        assert "confidence" in result
        assert 0 <= result["confidence"] <= 1
        assert len(result["probabilities"]) == 5  # 5 классов в модели

    def test_health_check(self):
        """Тест проверки здоровья"""
        # Arrange
        self.model_manager.model = Mock()

        # Act
        health = asyncio.run(self.model_manager.health_check())

        # Assert
        assert health["status"] == "healthy"
        assert "device" in health
        assert "model_version" in health

    def test_health_check_unhealthy(self):
        """Тест проверки здоровья при отсутствии модели"""
        # Arrange
        self.model_manager.model = None

        # Act
        health = asyncio.run(self.model_manager.health_check())

        # Assert
        assert health["status"] == "unhealthy"


class TestAIService:
    """Тесты для AIService"""

    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.model_manager = SimpleModelManager(model_path="/test/models")
        self.ai_service = AIService(self.model_manager)

    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """Тест инициализации сервиса"""
        # Arrange & Act
        await self.ai_service.initialize()

        # Assert
        assert self.ai_service.is_ready is True
        assert self.ai_service.model_manager.model is not None

    @pytest.mark.asyncio
    async def test_process_request_success(self):
        """Тест успешной обработки запроса"""
        # Arrange
        await self.ai_service.initialize()
        request = PredictionRequest(
            data=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
            model_version="latest",
            confidence_threshold=0.5
        )

        # Act
        response = await self.ai_service.process_request(request)

        # Assert
        assert isinstance(response, PredictionResponse)
        assert isinstance(response.prediction, dict)
        assert 0 <= response.confidence <= 1
        assert response.processing_time >= 0
        assert response.model_version == "demo-v1.0"

    @pytest.mark.asyncio
    async def test_process_request_not_ready(self):
        """Тест обработки запроса при неготовности сервиса"""
        # Arrange
        request = PredictionRequest(data=[1.0, 2.0, 3.0, 4.0, 5.0])

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await self.ai_service.process_request(request)

        assert "not ready" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Тест проверки здоровья сервиса"""
        # Arrange & Act
        health = await self.ai_service.health_check()

        # Assert
        assert isinstance(health, dict)
        assert "service_status" in health
        assert "model" in health

    @pytest.mark.asyncio
    async def test_health_check_ready(self):
        """Тест проверки здоровья готового сервиса"""
        # Arrange
        await self.ai_service.initialize()

        # Act
        health = await self.ai_service.health_check()

        # Assert
        assert health["service_status"] == "ready"
        assert health["model"]["status"] == "healthy"


@pytest.mark.integration
class TestAIAPI:
    """Интеграционные тесты API"""

    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        """Тест health endpoint"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/health")

        assert response.status_code == 200
        assert "service_status" in response.json()

    @pytest.mark.asyncio
    async def test_predict_endpoint(self):
        """Тест predict endpoint"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/predict", json={
                "data": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
                "model_version": "latest"
            })

        assert response.status_code == 200
        data = response.json()
        assert "prediction" in data
        assert "confidence" in data
        assert "processing_time" in data

    @pytest.mark.asyncio
    async def test_models_endpoint(self):
        """Тест models endpoint"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/models")

        assert response.status_code == 200
        data = response.json()
        assert "models" in data
        assert "device" in data
        assert "status" in data

    @pytest.mark.asyncio
    async def test_root_endpoint(self):
        """Тест корневого endpoint"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data


class TestDataValidation:
    """Тесты валидации данных"""

    def test_prediction_request_validation(self):
        """Тест валидации PredictionRequest"""
        # Valid request
        request = PredictionRequest(
            data=[1.0, 2.0, 3.0],
            model_version="latest",
            confidence_threshold=0.7
        )
        assert len(request.data) == 3
        assert request.model_version == "latest"
        assert request.confidence_threshold == 0.7

    def test_prediction_request_invalid_data(self):
        """Тест валидации с неправильными данными"""
        # Invalid - empty data
        with pytest.raises(Exception):
            PredictionRequest(data=[], model_version="latest")

        # Invalid - wrong confidence threshold
        with pytest.raises(Exception):
            PredictionRequest(
                data=[1.0, 2.0, 3.0],
                confidence_threshold=1.5  # > 1.0
            )

    def test_prediction_response_validation(self):
        """Тест валидации PredictionResponse"""
        response = PredictionResponse(
            prediction={"class": 1, "probabilities": [0.1, 0.9]},
            confidence=0.9,
            processing_time=0.5,
            model_version="demo-v1.0"
        )

        assert response.confidence == 0.9
        assert response.processing_time == 0.5
        assert response.model_version == "demo-v1.0"
        assert response.prediction["class"] == 1


class TestErrorHandling:
    """Тесты обработки ошибок"""

    @pytest.mark.asyncio
    async def test_model_prediction_error(self):
        """Тест обработки ошибок в предсказании"""
        # Arrange
        model_manager = SimpleModelManager(model_path="/test/models")
        await model_manager.load_model()

        # Monkey patch для вызова ошибки
        async def mock_predict_error(data):
            raise ValueError("Model prediction failed")

        model_manager.predict = mock_predict_error

        # Act & Assert
        with pytest.raises(Exception) as exc_info:
            await model_manager.predict(np.array([[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]]))

        assert "prediction failed" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_service_initialization_error(self):
        """Тест обработки ошибок инициализации"""
        # Arrange
        model_manager = Mock()
        model_manager.load_model = AsyncMock(side_effect=Exception("Model loading failed"))

        service = AIService(model_manager)

        # Act & Assert
        with pytest.raises(Exception):
            await service.initialize()

        assert service.is_ready is False

    def test_invalid_json_request(self):
        """Тест обработки неправильного JSON"""
        # This would be tested in integration tests with actual HTTP client
        pass


class TestPerformance:
    """Тесты производительности"""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_prediction_performance(self):
        """Тест производительности предсказания"""
        # Arrange
        service = AIService(SimpleModelManager("/test/models"))
        await service.initialize()

        request = PredictionRequest(
            data=[1.0] * 10,
            model_version="latest"
        )

        # Act
        import time
        start_time = time.time()
        response = await service.process_request(request)
        end_time = time.time()

        # Assert
        processing_time = end_time - start_time
        assert processing_time < 1.0  # Должно быть быстрее 1 секунды
        assert response.processing_time < 1.0

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Тест параллельных запросов"""
        # Arrange
        service = AIService(SimpleModelManager("/test/models"))
        await service.initialize()

        # Act
        tasks = []
        for i in range(5):
            request = PredictionRequest(
                data=[float(i)] * 10,
                model_version="latest"
            )
            task = service.process_request(request)
            tasks.append(task)

        responses = await asyncio.gather(*tasks)

        # Assert
        assert len(responses) == 5
        for response in responses:
            assert isinstance(response, PredictionResponse)
            assert response.confidence >= 0
            assert response.confidence <= 1


# Фикстуры для тестов
@pytest.fixture
def sample_prediction_request():
    """Фикстура для тестового запроса"""
    return PredictionRequest(
        data=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0],
        model_version="test",
        confidence_threshold=0.8
    )


@pytest.fixture
def mock_model():
    """Фикстура для мок модели"""
    model = Mock()
    model.return_value = torch.tensor([[0.1, 0.2, 0.7, 0.05, 0.95]])
    return model


# Параметризованные тесты
@pytest.mark.parametrize("device", ["cpu", "cuda"])
@pytest.mark.parametrize("model_version", ["v1.0", "v2.0", "latest"])
@pytest.mark.asyncio
async def test_model_device_versions(device, model_version):
    """Параметризованный тест для разных устройств и версий"""
    with patch.object(torch, 'cuda') as mock_cuda:
        mock_cuda.is_available.return_value = device == "cuda"

        model_manager = SimpleModelManager("/test/models", device="auto")
        await model_manager.load_model()

        assert model_manager.device == device
        assert model_manager.model_version == "demo-v1.0"
