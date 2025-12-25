"""
Конфигурация логирования.

Настраивает структурированное логирование для приложения.
"""

import logging
import sys
from typing import Any

from .config import settings


class CustomFormatter(logging.Formatter):
    """
    Кастомный форматтер для логов.
    
    Добавляет цвета для разных уровней логирования в development.
    """
    
    grey = "\x1b[38;20m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    green = "\x1b[32;20m"
    
    format_str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    FORMATS = {
        logging.DEBUG: grey + format_str + reset,
        logging.INFO: green + format_str + reset,
        logging.WARNING: yellow + format_str + reset,
        logging.ERROR: red + format_str + reset,
        logging.CRITICAL: bold_red + format_str + reset,
    }
    
    def format(self, record: logging.LogRecord) -> str:
        """Форматировать запись лога."""
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


def setup_logging() -> None:
    """
    Настроить логирование приложения.
    
    В development использует цветной вывод.
    В production использует JSON формат.
    """
    # Получить уровень логирования
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Создать handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    
    # Выбрать форматтер в зависимости от окружения
    if settings.is_production:
        formatter = logging.Formatter(
            '{"time": "%(asctime)s", "name": "%(name)s", '
            '"level": "%(levelname)s", "message": "%(message)s"}',
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
    else:
        formatter = CustomFormatter()
    
    handler.setFormatter(formatter)
    
    # Настроить root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers = [handler]
    
    # Уменьшить verbose логи от библиотек
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.debug else logging.WARNING
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # Лог о запуске
    logger = logging.getLogger(__name__)
    logger.info(
        "Logging configured",
        extra={
            "level": settings.log_level,
            "environment": settings.environment,
        }
    )


def get_logger(name: str) -> logging.Logger:
    """
    Получить logger с указанным именем.
    
    Args:
        name: Имя логгера (обычно __name__)
        
    Returns:
        logging.Logger: Настроенный логгер
    """
    return logging.getLogger(name)

