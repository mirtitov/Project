"""
Менеджер для управления lifecycle внешних клиентов.

Решает проблему memory leak при использовании lru_cache для HTTP клиентов.
"""

import logging

from ..core.cache import get_cache_service
from ..core.config import settings
from ..external.openlibrary.cached_client import CachedOpenLibraryClient
from ..external.openlibrary.client import OpenLibraryClient

logger = logging.getLogger(__name__)


class ClientsManager:
    """
    Менеджер для управления lifecycle внешних клиентов.

    Преимущества:
    - Lazy initialization (клиенты создаются при первом обращении)
    - Proper cleanup при shutdown
    - Можно мокировать в тестах
    - Избегает memory leak от lru_cache с httpx.AsyncClient
    """

    def __init__(self):
        """Инициализировать менеджер с пустыми клиентами."""
        self._openlibrary: OpenLibraryClient | None = None
        self._cached_openlibrary: CachedOpenLibraryClient | None = None

    def get_openlibrary(self) -> OpenLibraryClient:
        """
        Получить OpenLibrary клиент (lazy initialization).

        Returns:
            OpenLibraryClient: Клиент для Open Library API
        """
        if self._openlibrary is None:
            logger.info("Initializing OpenLibrary client")
            self._openlibrary = OpenLibraryClient(
                base_url=settings.openlibrary_base_url,
                timeout=settings.openlibrary_timeout,
            )
        return self._openlibrary

    def get_cached_openlibrary(self) -> CachedOpenLibraryClient:
        """
        Получить кэширующий OpenLibrary клиент.

        Returns:
            CachedOpenLibraryClient: Кэширующая обёртка для Open Library
        """
        if self._cached_openlibrary is None:
            logger.info("Initializing CachedOpenLibrary client")
            self._cached_openlibrary = CachedOpenLibraryClient(
                client=self.get_openlibrary(),
                cache=get_cache_service(),
                ttl=settings.cache_ttl,
            )
        return self._cached_openlibrary

    async def close_all(self) -> None:
        """
        Закрыть все клиенты.

        Вызывается при shutdown приложения для освобождения ресурсов.
        """
        if self._cached_openlibrary is not None:
            logger.info("Closing CachedOpenLibrary client")
            await self._cached_openlibrary.close()
            self._cached_openlibrary = None

        if self._openlibrary is not None:
            logger.info("Closing OpenLibrary client")
            await self._openlibrary.close()
            self._openlibrary = None

        logger.info("All clients closed successfully")


# Глобальный экземпляр менеджера клиентов
clients_manager = ClientsManager()
