"""
Базовый репозиторий.

Реализует паттерн Repository для CRUD операций с базой данных.
"""

from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """
    Базовый репозиторий для CRUD операций.
    
    Использует Generic для типизации модели.
    
    Attributes:
        session: Async сессия SQLAlchemy
        model: Класс ORM модели
    """
    
    def __init__(self, session: AsyncSession, model: type[T]):
        """
        Инициализировать репозиторий.
        
        Args:
            session: Async сессия БД
            model: Класс ORM модели
        """
        self.session = session
        self.model = model
    
    async def create(self, **kwargs) -> T:
        """
        Создать новую запись.
        
        Args:
            **kwargs: Поля для создания записи
            
        Returns:
            T: Созданная модель
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        await self.session.commit()
        await self.session.refresh(instance)
        return instance
    
    async def get_by_id(self, id: UUID) -> T | None:
        """
        Получить запись по ID.
        
        Примечание: session.get() автоматически работает с primary key модели,
        независимо от его названия (id, book_id, user_id и т.д.)
        
        Args:
            id: UUID записи
            
        Returns:
            T | None: Найденная модель или None
        """
        return await self.session.get(self.model, id)
    
    async def update(self, id: UUID, **kwargs) -> T | None:
        """
        Обновить запись.
        
        Args:
            id: UUID записи
            **kwargs: Поля для обновления
            
        Returns:
            T | None: Обновленная модель или None если не найдена
        """
        instance = await self.get_by_id(id)
        if instance is None:
            return None
        
        for key, value in kwargs.items():
            if hasattr(instance, key):
                setattr(instance, key, value)
        
        await self.session.commit()
        await self.session.refresh(instance)
        return instance
    
    async def delete(self, id: UUID) -> bool:
        """
        Удалить запись.
        
        Args:
            id: UUID записи
            
        Returns:
            bool: True если удалено, False если не найдено
        """
        instance = await self.get_by_id(id)
        if instance is None:
            return False
        
        await self.session.delete(instance)
        await self.session.commit()
        return True
    
    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
    ) -> list[T]:
        """
        Получить все записи с пагинацией.
        
        Args:
            limit: Максимальное количество записей
            offset: Смещение от начала
            
        Returns:
            list[T]: Список моделей
        """
        stmt = select(self.model).limit(limit).offset(offset)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def count(self) -> int:
        """
        Подсчитать общее количество записей.
        
        Returns:
            int: Количество записей
        """
        stmt = select(func.count()).select_from(self.model)
        result = await self.session.execute(stmt)
        return result.scalar() or 0

