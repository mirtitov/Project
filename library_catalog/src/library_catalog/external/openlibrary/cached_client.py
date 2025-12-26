"""
Кэширующий клиент для Open Library API.

Оборачивает OpenLibraryClient и добавляет кэширование.
"""

from typing import Any

from ...core.cache import CacheService, get_cache_service
from .client import OpenLibraryClient


class CachedOpenLibraryClient:
    """
    Кэширующая обёртка для OpenLibraryClient.
    
    Кэширует результаты запросов к Open Library
    для уменьшения нагрузки и ускорения ответов.
    """
    
    def __init__(
        self,
        client: OpenLibraryClient,
        cache: CacheService | None = None,
        ttl: int = 3600,  # 1 час
    ):
        """
        Инициализировать кэширующий клиент.
        
        Args:
            client: Базовый клиент Open Library
            cache: Сервис кэширования (по умолчанию глобальный)
            ttl: Время жизни кэша в секундах
        """
        self._client = client
        self._cache = cache or get_cache_service()
        self._ttl = ttl
    
    async def search_by_isbn(self, isbn: str) -> dict[str, Any]:
        """
        Поиск книги по ISBN с кэшированием.
        
        Args:
            isbn: ISBN книги
            
        Returns:
            dict: Данные книги
        """
        # Очистить ISBN для создания ключа
        clean_isbn = isbn.replace("-", "").replace(" ", "")
        cache_key = f"ol:isbn:{clean_isbn}"
        
        return await self._cache.get_or_set(
            key=cache_key,
            factory=lambda: self._client.search_by_isbn(isbn),
            ttl=self._ttl,
        )
    
    async def search_by_title_author(
        self,
        title: str,
        author: str,
    ) -> dict[str, Any]:
        """
        Поиск по названию и автору с кэшированием.
        
        Args:
            title: Название книги
            author: Автор книги
            
        Returns:
            dict: Данные книги
        """
        # Создать ключ из title и author
        cache_key = f"ol:title_author:{CacheService.make_key(title, author)}"
        
        return await self._cache.get_or_set(
            key=cache_key,
            factory=lambda: self._client.search_by_title_author(title, author),
            ttl=self._ttl,
        )
    
    async def enrich(
        self,
        title: str,
        author: str,
        isbn: str | None = None,
    ) -> dict[str, Any]:
        """
        Обогатить данные книги с кэшированием.
        
        Args:
            title: Название книги
            author: Автор книги
            isbn: ISBN книги (опционально)
            
        Returns:
            dict: Обогащенные данные
        """
        # Создать уникальный ключ
        cache_key = f"ol:enrich:{CacheService.make_key(title, author, isbn)}"
        
        return await self._cache.get_or_set(
            key=cache_key,
            factory=lambda: self._client.enrich(title, author, isbn),
            ttl=self._ttl,
        )
    
    async def close(self) -> None:
        """Закрыть клиент."""
        await self._client.close()

