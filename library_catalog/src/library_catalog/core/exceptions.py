"""
Базовые исключения приложения.

Содержит базовые классы исключений и обработчики для FastAPI.
"""

from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class AppException(Exception):
    """
    Базовое исключение приложения.
    
    Все пользовательские исключения должны наследоваться от этого класса.
    
    Attributes:
        message: Сообщение об ошибке
        status_code: HTTP код ответа
        details: Дополнительные детали ошибки
    """
    
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class NotFoundException(AppException):
    """
    Исключение: Ресурс не найден.
    
    Используется когда запрашиваемый ресурс не существует в БД.
    """
    
    def __init__(self, resource: str, identifier: Any):
        super().__init__(
            message=f"{resource} with id '{identifier}' not found",
            status_code=404,
            details={"resource": resource, "identifier": str(identifier)},
        )


class ValidationException(AppException):
    """
    Исключение: Ошибка валидации.
    
    Используется для ошибок валидации бизнес-правил.
    """
    
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=400,
            details=details,
        )


class ConflictException(AppException):
    """
    Исключение: Конфликт.
    
    Используется когда операция приводит к конфликту (например, дублирование).
    """
    
    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            message=message,
            status_code=409,
            details=details,
        )


class ExternalServiceException(AppException):
    """
    Исключение: Ошибка внешнего сервиса.
    
    Используется при ошибках обращения к внешним API.
    """
    
    def __init__(self, service: str, message: str):
        super().__init__(
            message=f"{service} error: {message}",
            status_code=503,
            details={"service": service},
        )


def register_exception_handlers(app: FastAPI) -> None:
    """
    Зарегистрировать обработчики исключений для FastAPI.
    
    Args:
        app: Экземпляр FastAPI приложения
    """
    
    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request,
        exc: AppException,
    ) -> JSONResponse:
        """Обработчик для AppException и его подклассов."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.message,
                "type": exc.__class__.__name__,
                **exc.details,
            },
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request,
        exc: Exception,
    ) -> JSONResponse:
        """Обработчик для неперехваченных исключений."""
        import logging
        logger = logging.getLogger(__name__)
        logger.exception("Unhandled exception: %s", exc)
        
        return JSONResponse(
            status_code=500,
            content={
                "detail": "Internal server error",
                "type": "InternalError",
            },
        )

