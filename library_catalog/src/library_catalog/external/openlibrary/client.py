"""
Клиент для Open Library API.

Обеспечивает поиск и обогащение данных о книгах из Open Library.
"""

from typing import Any

import httpx

from ...domain.exceptions import OpenLibraryException, OpenLibraryTimeoutException
from ..base.base_client import BaseApiClient


class OpenLibraryClient(BaseApiClient):
    """
    Клиент для Open Library API.
    
    Позволяет:
    - Искать книги по ISBN
    - Искать книги по названию и автору
    - Получать обложки и дополнительную информацию
    """
    
    def __init__(
        self,
        base_url: str = "https://openlibrary.org",
        timeout: float = 10.0,
    ):
        """
        Инициализировать клиент Open Library.
        
        Args:
            base_url: Базовый URL API
            timeout: Таймаут запроса
        """
        super().__init__(base_url, timeout=timeout)
    
    def client_name(self) -> str:
        """Имя клиента для логирования."""
        return "openlibrary"
    
    async def search_by_isbn(self, isbn: str) -> dict[str, Any]:
        """
        Поиск книги по ISBN.
        
        Args:
            isbn: ISBN-10 или ISBN-13
            
        Returns:
            dict: Данные книги (cover_url, subjects, etc.)
            
        Raises:
            OpenLibraryTimeoutException: При таймауте
            OpenLibraryException: При ошибке API
        """
        try:
            # Очистить ISBN от дефисов
            clean_isbn = isbn.replace("-", "").replace(" ", "")
            
            data = await self._get(
                "/search.json",
                params={"isbn": clean_isbn, "limit": 1},
            )
            
            docs = data.get("docs", [])
            if not docs:
                self.logger.debug("No results for ISBN: %s", isbn)
                return {}
            
            return self._extract_book_data(docs[0])
        
        except httpx.TimeoutException:
            raise OpenLibraryTimeoutException(self.timeout)
        except httpx.HTTPError as e:
            raise OpenLibraryException(str(e))
    
    async def search_by_title_author(
        self,
        title: str,
        author: str,
    ) -> dict[str, Any]:
        """
        Поиск по названию и автору.
        
        Args:
            title: Название книги
            author: Автор книги
            
        Returns:
            dict: Данные книги
            
        Raises:
            OpenLibraryTimeoutException: При таймауте
            OpenLibraryException: При ошибке API
        """
        try:
            data = await self._get(
                "/search.json",
                params={
                    "title": title,
                    "author": author,
                    "limit": 1,
                },
            )
            
            docs = data.get("docs", [])
            if not docs:
                self.logger.debug(
                    "No results for title='%s', author='%s'",
                    title,
                    author,
                )
                return {}
            
            return self._extract_book_data(docs[0])
        
        except httpx.TimeoutException:
            raise OpenLibraryTimeoutException(self.timeout)
        except httpx.HTTPError as e:
            raise OpenLibraryException(str(e))
    
    async def enrich(
        self,
        title: str,
        author: str,
        isbn: str | None = None,
    ) -> dict[str, Any]:
        """
        Обогатить данные книги.
        
        Сначала пытается найти по ISBN, затем по title+author.
        
        Args:
            title: Название книги
            author: Автор книги
            isbn: ISBN книги (опционально)
            
        Returns:
            dict: Обогащенные данные или пустой словарь
        """
        # Попытка 1: По ISBN
        if isbn:
            try:
                data = await self.search_by_isbn(isbn)
                if data:
                    self.logger.info("Enriched by ISBN: %s", isbn)
                    return data
            except (OpenLibraryException, OpenLibraryTimeoutException) as e:
                self.logger.warning("ISBN search failed: %s", e)
        
        # Попытка 2: По title + author
        try:
            data = await self.search_by_title_author(title, author)
            if data:
                self.logger.info(
                    "Enriched by title/author: %s/%s",
                    title,
                    author,
                )
            return data
        except (OpenLibraryException, OpenLibraryTimeoutException) as e:
            self.logger.warning("Title/author search failed: %s", e)
            return {}
    
    def _extract_book_data(self, doc: dict[str, Any]) -> dict[str, Any]:
        """
        Извлечь нужные поля из ответа Open Library.
        
        Args:
            doc: Документ из массива docs
            
        Returns:
            dict: Обработанные данные
        """
        result: dict[str, Any] = {}
        
        # Cover URL
        if cover_id := doc.get("cover_i"):
            result["cover_url"] = self._get_cover_url(cover_id)
        
        # Subjects (темы) - первые 10
        if subjects := doc.get("subject"):
            result["subjects"] = subjects[:10]
        
        # Publisher
        if publishers := doc.get("publisher"):
            result["publisher"] = publishers[0] if publishers else None
        
        # Language
        if languages := doc.get("language"):
            result["language"] = languages[0] if languages else None
        
        # Ratings
        if ratings := doc.get("ratings_average"):
            result["rating"] = round(ratings, 2)
        
        # First publish year
        if first_year := doc.get("first_publish_year"):
            result["first_publish_year"] = first_year
        
        # Number of editions
        if editions := doc.get("edition_count"):
            result["edition_count"] = editions
        
        return result
    
    def _get_cover_url(self, cover_id: int | None, size: str = "L") -> str | None:
        """
        Получить URL обложки.
        
        Args:
            cover_id: ID обложки в Open Library
            size: Размер (S, M, L)
            
        Returns:
            str | None: URL обложки или None
        """
        if not cover_id:
            return None
        return f"https://covers.openlibrary.org/b/id/{cover_id}-{size}.jpg"

