"""
Rate Limiting для защиты API от abuse.

Использует slowapi для ограничения количества запросов.
"""

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from .config import settings


def get_client_ip(request: Request) -> str:
    """
    Получить IP клиента для rate limiting.

    Учитывает X-Forwarded-For заголовок для работы за reverse proxy.

    Args:
        request: FastAPI Request

    Returns:
        str: IP адрес клиента
    """
    # Проверяем X-Forwarded-For для работы за nginx/cloudflare
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Берем первый IP (реальный клиент)
        return forwarded.split(",")[0].strip()

    return get_remote_address(request)


# Создаем limiter с функцией получения IP
limiter = Limiter(
    key_func=get_client_ip,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"],
    enabled=settings.rate_limit_enabled,
)


# Декораторы для разных лимитов
def limit_auth(limit: str = "5/minute"):
    """
    Лимит для auth эндпоинтов (более строгий).

    Args:
        limit: Лимит в формате "N/period"

    Returns:
        Decorator: Декоратор slowapi
    """
    return limiter.limit(limit)


def limit_write(limit: str = "30/minute"):
    """
    Лимит для write операций (POST, PUT, DELETE).

    Args:
        limit: Лимит в формате "N/period"

    Returns:
        Decorator: Декоратор slowapi
    """
    return limiter.limit(limit)


def limit_read(limit: str = "100/minute"):
    """
    Лимит для read операций (GET).

    Args:
        limit: Лимит в формате "N/period"

    Returns:
        Decorator: Декоратор slowapi
    """
    return limiter.limit(limit)
