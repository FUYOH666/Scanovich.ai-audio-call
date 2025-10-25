"""
ScanovichAI Portfolio - AI Service Example

Этот модуль демонстрирует архитектуру и лучшие практики разработки AI сервисов.
Представляет собой шаблон для создания production-ready AI решений.

Author: Aleksandr Mordvinov
Email: contact@scanovich.ai
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

import numpy as np
from pydantic import BaseModel, Field
import torch
from fastapi import FastAPI, HTTPException, Depends
from prometheus_client import Counter, Histogram, Gauge

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Метрики для мониторинга
REQUESTS_TOTAL = Counter('ai_requests_total', 'Total AI requests', ['service', 'model'])
INFERENCE_TIME = Histogram('ai_inference_seconds', 'AI inference time')
ACTIVE_MODELS = Gauge('ai_active_models', 'Active AI models')


class PredictionRequest(BaseModel):
    """Запрос на предсказание"""
    data: List[float] = Field(..., description="Входные данные для модели")
    model_version: Optional[str] = Field("latest", description="Версия модели")
    confidence_threshold: Optional[float] = Field(0.5, description="Порог уверенности")


class PredictionResponse(BaseModel):
    """Ответ модели"""
    prediction: Dict[str, Any] = Field(..., description="Результат предсказания")
    confidence: float = Field(..., description="Уверенность предсказания")
    processing_time: float = Field(..., description="Время обработки")
    model_version: str = Field(..., description="Версия использованной модели")


class ModelManager(ABC):
    """Абстрактный класс для управления AI моделями"""

    def __init__(self, model_path: str, device: str = "auto"):
        self.model_path = model_path
        self.device = self._get_device(device)
        self.model = None
        self.model_version = "unknown"

    def _get_device(self, device: str) -> str:
        """Определение устройства для вычислений"""
        if device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device

    @abstractmethod
    async def load_model(self) -> None:
        """Загрузка модели"""
        pass

    @abstractmethod
    async def predict(self, data: np.ndarray) -> Dict[str, Any]:
        """Предсказание модели"""
        pass

    async def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья модели"""
        return {
            "status": "healthy" if self.model is not None else "unhealthy",
            "device": self.device,
            "model_version": self.model_version
        }


class SimpleModelManager(ModelManager):
    """Пример простой модели для демонстрации"""

    async def load_model(self) -> None:
        """Загрузка простой модели"""
        logger.info(f"Loading model from {self.model_path}")

        # В реальности здесь была бы загрузка обученной модели
        # Для примера создаем простую модель
        self.model = torch.nn.Sequential(
            torch.nn.Linear(10, 50),
            torch.nn.ReLU(),
            torch.nn.Linear(50, 5),
            torch.nn.Softmax(dim=1)
        ).to(self.device)

        self.model_version = "demo-v1.0"
        ACTIVE_MODELS.inc()

        logger.info(f"Model loaded successfully on {self.device}")

    async def predict(self, data: np.ndarray) -> Dict[str, Any]:
        """Предсказание модели"""
        start_time = asyncio.get_event_loop().time()

        try:
            # Преобразование данных
            tensor_data = torch.tensor(data, dtype=torch.float32).to(self.device)

            # Инференс
            with torch.no_grad():
                prediction = self.model(tensor_data)
                probabilities = prediction.cpu().numpy()

            # Обработка результатов
            max_prob = float(np.max(probabilities))
            predicted_class = int(np.argmax(probabilities))

            result = {
                "class": predicted_class,
                "probabilities": probabilities.tolist(),
                "confidence": max_prob
            }

            # Метрики
            INFERENCE_TIME.observe(asyncio.get_event_loop().time() - start_time)
            REQUESTS_TOTAL.labels(service="ai_service", model=self.model_version).inc()

            return result

        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


class AIService:
    """Основной AI сервис"""

    def __init__(self, model_manager: ModelManager):
        self.model_manager = model_manager
        self.is_ready = False

    async def initialize(self) -> None:
        """Инициализация сервиса"""
        logger.info("Initializing AI service...")
        await self.model_manager.load_model()
        self.is_ready = True
        logger.info("AI service initialized successfully")

    async def process_request(self, request: PredictionRequest) -> PredictionResponse:
        """Обработка запроса"""
        if not self.is_ready:
            raise HTTPException(status_code=503, detail="Service not ready")

        start_time = asyncio.get_event_loop().time()

        try:
            # Преобразование данных
            data_array = np.array(request.data).reshape(1, -1)

            # Получение предсказания
            prediction = await self.model_manager.predict(data_array)

            processing_time = asyncio.get_event_loop().time() - start_time

            return PredictionResponse(
                prediction=prediction,
                confidence=prediction["confidence"],
                processing_time=processing_time,
                model_version=self.model_manager.model_version
            )

        except Exception as e:
            logger.error(f"Request processing error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

    async def health_check(self) -> Dict[str, Any]:
        """Проверка здоровья сервиса"""
        model_health = await self.model_manager.health_check()
        return {
            "service_status": "ready" if self.is_ready else "initializing",
            "model": model_health
        }


# FastAPI приложение
app = FastAPI(
    title="ScanovichAI Portfolio - AI Service Example",
    description="Пример AI сервиса демонстрирующий лучшие практики разработки",
    version="1.0.0"
)


async def get_ai_service() -> AIService:
    """Dependency injection для AI сервиса"""
    # В реальности здесь была бы инициализация из конфигурации
    model_manager = SimpleModelManager(model_path="/models/demo")
    service = AIService(model_manager)

    if not service.is_ready:
        await service.initialize()

    return service


@app.get("/")
async def root():
    """Корневой endpoint"""
    return {"message": "ScanovichAI Portfolio API", "version": "1.0.0"}


@app.get("/health")
async def health_check(service: AIService = Depends(get_ai_service)):
    """Проверка здоровья сервиса"""
    return await service.health_check()


@app.post("/predict", response_model=PredictionResponse)
async def predict(
    request: PredictionRequest,
    service: AIService = Depends(get_ai_service)
) -> PredictionResponse:
    """Предсказание модели"""
    return await service.process_request(request)


@app.get("/models")
async def get_models(service: AIService = Depends(get_ai_service)):
    """Информация о моделях"""
    return {
        "models": [service.model_manager.model_version],
        "device": service.model_manager.device,
        "status": "ready" if service.is_ready else "initializing"
    }


if __name__ == "__main__":
    """Запуск сервиса"""
    import uvicorn

    # Настройка логирования для production
    uvicorn.run(
        "ai_service_example:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        access_log=True,
        log_level="info"
    )
