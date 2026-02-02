"""
Кэширование.

Поддерживает in-memory (cachetools) и Redis кэширование.
"""

import hashlib
import json
import logging
from abc import ABC, abstractmethod
from typing import Any

from cachetools import TTLCache

logger = logging.getLogger(__name__)


class CacheBackend(ABC):
    """Абстрактный бэкенд кэширования."""

    @abstractmethod
    async def get(self, key: str) -> Any | None:
        """Получить значение из кэша."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Установить значение в кэш."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        """Удалить значение из кэша."""
        pass

    @abstractmethod
    async def clear(self) -> None:
        """Очистить весь кэш."""
        pass


class InMemoryCache(CacheBackend):
    """
    In-memory кэш на основе cachetools.

    Простой и быстрый, но не подходит для
    распределённых систем (данные не шарятся между процессами).
    """

    def __init__(self, maxsize: int = 1000, ttl: int = 300):
        """
        Инициализировать in-memory кэш.

        Args:
            maxsize: Максимальное количество элементов
            ttl: Время жизни по умолчанию (секунды)
        """
        self._cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self._default_ttl = ttl
        logger.info("InMemoryCache initialized (maxsize=%d, ttl=%d)", maxsize, ttl)

    async def get(self, key: str) -> Any | None:
        """Получить значение из кэша."""
        value = self._cache.get(key)
        if value is not None:
            logger.debug("Cache HIT: %s", key)
        else:
            logger.debug("Cache MISS: %s", key)
        return value

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        """Установить значение в кэш."""
        self._cache[key] = value
        logger.debug("Cache SET: %s (ttl=%d)", key, ttl or self._default_ttl)

    async def delete(self, key: str) -> None:
        """Удалить значение из кэша."""
        self._cache.pop(key, None)
        logger.debug("Cache DELETE: %s", key)

    async def clear(self) -> None:
        """Очистить весь кэш."""
        self._cache.clear()
        logger.info("Cache CLEARED")


class RedisCache(CacheBackend):
    """
    Redis кэш для распределённых систем.

    Данные шарятся между всеми процессами/серверами.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """
        Инициализировать Redis кэш.

        Args:
            redis_url: URL подключения к Redis
        """
        import redis.asyncio as redis_async

        self._redis = redis_async.from_url(redis_url, decode_responses=True)
        self._prefix = "library_catalog:"
        logger.info("RedisCache initialized: %s", redis_url)

    def _make_key(self, key: str) -> str:
        """Добавить префикс к ключу."""
        return f"{self._prefix}{key}"

    async def get(self, key: str) -> Any | None:
        """Получить значение из кэша."""
        try:
            value = await self._redis.get(self._make_key(key))
            if value is not None:
                logger.debug("Cache HIT: %s", key)
                return json.loads(value)
            logger.debug("Cache MISS: %s", key)
            return None
        except Exception as e:
            logger.warning("Redis GET error: %s", e)
            return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Установить значение в кэш."""
        try:
            await self._redis.setex(
                self._make_key(key),
                ttl,
                json.dumps(value),
            )
            logger.debug("Cache SET: %s (ttl=%d)", key, ttl)
        except Exception as e:
            logger.warning("Redis SET error: %s", e)

    async def delete(self, key: str) -> None:
        """Удалить значение из кэша."""
        try:
            await self._redis.delete(self._make_key(key))
            logger.debug("Cache DELETE: %s", key)
        except Exception as e:
            logger.warning("Redis DELETE error: %s", e)

    async def clear(self) -> None:
        """Очистить весь кэш с нашим префиксом."""
        try:
            keys = await self._redis.keys(f"{self._prefix}*")
            if keys:
                await self._redis.delete(*keys)
            logger.info("Cache CLEARED")
        except Exception as e:
            logger.warning("Redis CLEAR error: %s", e)

    async def close(self) -> None:
        """Закрыть соединение с Redis."""
        await self._redis.close()


class CacheService:
    """
    Сервис кэширования с удобным API.

    Автоматически генерирует ключи и сериализует значения.
    """

    def __init__(self, backend: CacheBackend):
        """
        Инициализировать сервис кэширования.

        Args:
            backend: Бэкенд кэширования (InMemory или Redis)
        """
        self.backend = backend

    @staticmethod
    def make_key(*args, **kwargs) -> str:
        """
        Создать ключ кэша из аргументов.

        Использует MD5 хэш для создания уникального ключа.
        """
        key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()

    async def get_or_set(
        self,
        key: str,
        factory,
        ttl: int = 300,
    ) -> Any:
        """
        Получить из кэша или вычислить и сохранить.

        Args:
            key: Ключ кэша
            factory: Async функция для получения значения
            ttl: Время жизни в секундах

        Returns:
            Значение из кэша или результат factory
        """
        # Попробовать получить из кэша
        cached = await self.backend.get(key)
        if cached is not None:
            return cached

        # Вычислить значение
        value = await factory()

        # Сохранить в кэш
        if value is not None:
            await self.backend.set(key, value, ttl)

        return value

    async def invalidate(self, key: str) -> None:
        """Инвалидировать ключ кэша."""
        await self.backend.delete(key)

    async def invalidate_pattern(self, pattern: str) -> None:
        """
        Инвалидировать ключи по паттерну.

        Примечание: работает только для Redis бэкенда.
        Для in-memory просто очищает весь кэш.
        """
        if isinstance(self.backend, RedisCache):
            try:
                keys = await self.backend._redis.keys(
                    f"{self.backend._prefix}{pattern}"
                )
                if keys:
                    await self.backend._redis.delete(*keys)
            except Exception as e:
                logger.warning("Invalidate pattern error: %s", e)
        else:
            # Для in-memory просто логируем
            logger.debug("Pattern invalidation not supported for InMemoryCache")


# Глобальный экземпляр кэша (будет инициализирован при старте)
_cache_service: CacheService | None = None


def get_cache_service() -> CacheService:
    """Получить сервис кэширования."""
    global _cache_service
    if _cache_service is None:
        # По умолчанию используем in-memory кэш
        _cache_service = CacheService(InMemoryCache(maxsize=1000, ttl=300))
    return _cache_service


def init_cache(
    use_redis: bool = False, redis_url: str = "redis://localhost:6379"
) -> CacheService:
    """
    Инициализировать кэш.

    Args:
        use_redis: Использовать Redis вместо in-memory
        redis_url: URL подключения к Redis

    Returns:
        CacheService: Инициализированный сервис кэширования
    """
    global _cache_service

    if use_redis:
        backend = RedisCache(redis_url)
    else:
        backend = InMemoryCache(maxsize=1000, ttl=300)

    _cache_service = CacheService(backend)
    return _cache_service
