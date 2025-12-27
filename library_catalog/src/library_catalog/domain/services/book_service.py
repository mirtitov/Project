"""
Сервис для работы с книгами.

Содержит всю бизнес-логику приложения.
"""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from typing import Protocol

from ...api.v1.schemas.book import BookCreate, BookUpdate, ShowBook
from ...data.repositories.book_repository import BookRepository
from ..exceptions import (
    BookAlreadyExistsException,
    BookNotFoundException,
    InvalidPagesException,
    InvalidYearException,
    OpenLibraryException,
    OpenLibraryTimeoutException,
)
from ..mappers.book_mapper import BookMapper


class OpenLibraryClientProtocol(Protocol):
    """Протокол для Open Library клиента (обычного или кэширующего)."""
    
    async def enrich(
        self,
        title: str,
        author: str,
        isbn: str | None = None,
    ) -> dict[str, Any]:
        """Обогатить данные книги."""
        ...


class BookService:
    """
    Сервис для работы с книгами.
    
    Содержит всю бизнес-логику приложения.
    Использует репозитории для работы с БД
    и внешние клиенты для обогащения данных.
    
    Attributes:
        book_repo: Репозиторий книг
        ol_client: Клиент Open Library API
        logger: Логгер сервиса
    """
    
    def __init__(
        self,
        book_repository: BookRepository,
        openlibrary_client: OpenLibraryClientProtocol,
    ):
        """
        Инициализировать сервис.
        
        Args:
            book_repository: Репозиторий для работы с книгами
            openlibrary_client: Клиент Open Library для обогащения (обычный или кэширующий)
        """
        self.book_repo = book_repository
        self.ol_client = openlibrary_client
        self.logger = logging.getLogger(__name__)
    
    async def create_book(self, book_data: BookCreate) -> ShowBook:
        """
        Создать новую книгу с обогащением из Open Library.
        
        Бизнес-правила:
        - Год не в будущем
        - Страницы > 0
        - ISBN уникален (если указан)
        
        Args:
            book_data: Данные для создания
            
        Returns:
            ShowBook: Созданная книга
            
        Raises:
            InvalidYearException: Если год невалиден
            InvalidPagesException: Если страницы <= 0
            BookAlreadyExistsException: Если ISBN уже существует
        """
        # 1. Валидация бизнес-правил
        self._validate_book_data(book_data)
        
        # 2. Проверка уникальности ISBN
        if book_data.isbn:
            existing = await self.book_repo.find_by_isbn(book_data.isbn)
            if existing:
                raise BookAlreadyExistsException(book_data.isbn)
        
        # 3. Обогащение данных из Open Library
        extra = await self._enrich_book_data(book_data)
        
        # 4. Создание в БД
        book = await self.book_repo.create(
            title=book_data.title,
            author=book_data.author,
            year=book_data.year,
            genre=book_data.genre,
            pages=book_data.pages,
            isbn=book_data.isbn,
            description=book_data.description,
            extra=extra,
        )
        
        # 5. Commit транзакции (сервис отвечает за commit)
        await self.book_repo.session.commit()
        
        self.logger.info("Created book: %s (id=%s)", book.title, book.book_id)
        
        # 5. Маппинг в DTO
        return BookMapper.to_show_book(book)
    
    async def get_book(self, book_id: UUID) -> ShowBook:
        """
        Получить книгу по ID.
        
        Args:
            book_id: UUID книги
            
        Returns:
            ShowBook: Найденная книга
            
        Raises:
            BookNotFoundException: Если книга не найдена
        """
        book = await self.book_repo.get_by_id(book_id)
        if book is None:
            raise BookNotFoundException(book_id)
        
        return BookMapper.to_show_book(book)
    
    async def update_book(
        self,
        book_id: UUID,
        book_data: BookUpdate,
    ) -> ShowBook:
        """
        Обновить книгу.
        
        Обновляются только переданные поля.
        
        Args:
            book_id: UUID книги
            book_data: Данные для обновления
            
        Returns:
            ShowBook: Обновленная книга
            
        Raises:
            BookNotFoundException: Если книга не найдена
            InvalidYearException: Если год невалиден
            InvalidPagesException: Если страницы <= 0
        """
        # Проверить существование
        existing = await self.book_repo.get_by_id(book_id)
        if existing is None:
            raise BookNotFoundException(book_id)
        
        # Валидация если обновляется год/страницы
        if book_data.year is not None:
            self._validate_year(book_data.year)
        if book_data.pages is not None:
            self._validate_pages(book_data.pages)
        
        # Получить только заполненные поля
        update_data = book_data.model_dump(exclude_unset=True)
        
        if not update_data:
            # Если нечего обновлять - вернуть текущую книгу
            return BookMapper.to_show_book(existing)
        
        # Обновить
        updated = await self.book_repo.update(book_id, **update_data)
        
        # Commit транзакции
        await self.book_repo.session.commit()
        
        self.logger.info("Updated book: %s (id=%s)", updated.title, updated.book_id)
        
        return BookMapper.to_show_book(updated)
    
    async def delete_book(self, book_id: UUID) -> None:
        """
        Удалить книгу.
        
        Args:
            book_id: UUID книги
            
        Raises:
            BookNotFoundException: Если книга не найдена
        """
        deleted = await self.book_repo.delete(book_id)
        if not deleted:
            raise BookNotFoundException(book_id)
        
        # Commit транзакции
        await self.book_repo.session.commit()
        
        self.logger.info("Deleted book: id=%s", book_id)
    
    async def search_books(
        self,
        title: str | None = None,
        author: str | None = None,
        genre: str | None = None,
        year: int | None = None,
        available: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[ShowBook], int]:
        """
        Поиск книг с фильтрацией и пагинацией.
        
        Args:
            title: Поиск по названию (частичное совпадение)
            author: Поиск по автору (частичное совпадение)
            genre: Точное совпадение жанра
            year: Точное совпадение года
            available: Фильтр по доступности
            limit: Максимальное количество результатов
            offset: Смещение от начала
            
        Returns:
            tuple: (список книг, общее количество)
        """
        # Получить книги
        books = await self.book_repo.find_by_filters(
            title=title,
            author=author,
            genre=genre,
            year=year,
            available=available,
            limit=limit,
            offset=offset,
        )
        
        # Подсчитать общее количество
        total = await self.book_repo.count_by_filters(
            title=title,
            author=author,
            genre=genre,
            year=year,
            available=available,
        )
        
        return BookMapper.to_show_books(books), total
    
    # ========== ПРИВАТНЫЕ МЕТОДЫ ==========
    
    def _validate_book_data(self, data: BookCreate) -> None:
        """
        Валидация бизнес-правил для новой книги.
        
        Args:
            data: Данные книги
            
        Raises:
            InvalidYearException: Если год невалиден
            InvalidPagesException: Если страницы <= 0
        """
        self._validate_year(data.year)
        self._validate_pages(data.pages)
    
    def _validate_year(self, year: int) -> None:
        """
        Проверить что год валиден.
        
        Args:
            year: Год издания
            
        Raises:
            InvalidYearException: Если год вне диапазона 1000-текущий
        """
        current_year = datetime.now().year
        if year < 1000 or year > current_year:
            raise InvalidYearException(year)
    
    def _validate_pages(self, pages: int) -> None:
        """
        Проверить что количество страниц валидно.
        
        Args:
            pages: Количество страниц
            
        Raises:
            InvalidPagesException: Если pages <= 0
        """
        if pages <= 0:
            raise InvalidPagesException(pages)
    
    async def _enrich_book_data(
        self,
        book_data: BookCreate,
    ) -> dict[str, Any] | None:
        """
        Обогатить данные книги из Open Library.
        
        Не выбрасывает исключение если API недоступен -
        книга будет создана без дополнительных данных.
        
        Args:
            book_data: Данные книги
            
        Returns:
            dict | None: Обогащенные данные или None
        """
        try:
            extra = await self.ol_client.enrich(
                title=book_data.title,
                author=book_data.author,
                isbn=book_data.isbn,
            )
            return extra if extra else None
        except (OpenLibraryException, OpenLibraryTimeoutException) as e:
            # Логируем но не прерываем создание книги
            self.logger.warning(
                "Failed to enrich book data from Open Library: %s "
                "(title=%s, author=%s)",
                e,
                book_data.title,
                book_data.author,
            )
            return None

