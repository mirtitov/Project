"""
Репозиторий для работы с книгами.

Содержит специфичные методы для книг (поиск, фильтрация).
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.book import Book
from .base_repository import BaseRepository


class BookRepository(BaseRepository[Book]):
    """
    Репозиторий для работы с книгами.
    
    Наследуется от BaseRepository и добавляет
    специфичные методы для работы с книгами.
    """
    
    def __init__(self, session: AsyncSession):
        """
        Инициализировать репозиторий книг.
        
        Args:
            session: Async сессия БД
        """
        super().__init__(session, Book)
    
    async def find_by_filters(
        self,
        title: str | None = None,
        author: str | None = None,
        genre: str | None = None,
        year: int | None = None,
        available: bool | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Book]:
        """
        Поиск книг с фильтрацией.
        
        Args:
            title: Поиск по названию (частичное совпадение)
            author: Поиск по автору (частичное совпадение)
            genre: Точное совпадение жанра
            year: Точное совпадение года
            available: Фильтр по доступности
            limit: Максимальное количество результатов
            offset: Смещение от начала
            
        Returns:
            list[Book]: Список найденных книг
        """
        stmt = select(Book)
        
        # Применить фильтры
        if title:
            stmt = stmt.where(Book.title.ilike(f"%{title}%"))
        if author:
            stmt = stmt.where(Book.author.ilike(f"%{author}%"))
        if genre:
            stmt = stmt.where(Book.genre == genre)
        if year:
            stmt = stmt.where(Book.year == year)
        if available is not None:
            stmt = stmt.where(Book.available == available)
        
        # Сортировка и пагинация
        stmt = stmt.order_by(Book.created_at.desc())
        stmt = stmt.limit(limit).offset(offset)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def find_by_isbn(self, isbn: str) -> Book | None:
        """
        Найти книгу по ISBN.
        
        Args:
            isbn: ISBN книги
            
        Returns:
            Book | None: Найденная книга или None
        """
        stmt = select(Book).where(Book.isbn == isbn)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def count_by_filters(
        self,
        title: str | None = None,
        author: str | None = None,
        genre: str | None = None,
        year: int | None = None,
        available: bool | None = None,
    ) -> int:
        """
        Подсчитать количество книг по фильтрам.
        
        Args:
            title: Поиск по названию (частичное совпадение)
            author: Поиск по автору (частичное совпадение)
            genre: Точное совпадение жанра
            year: Точное совпадение года
            available: Фильтр по доступности
            
        Returns:
            int: Количество книг, соответствующих фильтрам
        """
        stmt = select(func.count()).select_from(Book)
        
        # Применить те же фильтры
        if title:
            stmt = stmt.where(Book.title.ilike(f"%{title}%"))
        if author:
            stmt = stmt.where(Book.author.ilike(f"%{author}%"))
        if genre:
            stmt = stmt.where(Book.genre == genre)
        if year:
            stmt = stmt.where(Book.year == year)
        if available is not None:
            stmt = stmt.where(Book.available == available)
        
        result = await self.session.execute(stmt)
        return result.scalar() or 0
    
    async def get_genres(self) -> list[str]:
        """
        Получить список всех уникальных жанров.
        
        Returns:
            list[str]: Список жанров
        """
        stmt = select(Book.genre).distinct().order_by(Book.genre)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def get_authors(self) -> list[str]:
        """
        Получить список всех уникальных авторов.
        
        Returns:
            list[str]: Список авторов
        """
        stmt = select(Book.author).distinct().order_by(Book.author)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

