"""
Unit of Work паттерн.

Обеспечивает атомарность транзакций при работе с несколькими репозиториями.
Единственное место где делается commit/rollback.
"""

from typing import Protocol

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .repositories.book_repository import BookRepository
from .repositories.user_repository import UserRepository


class UnitOfWorkProtocol(Protocol):
    """
    Протокол Unit of Work.

    Определяет интерфейс для работы с транзакциями.
    Можно использовать для мокирования в тестах.
    """

    books: BookRepository
    users: UserRepository

    async def commit(self) -> None:
        """Зафиксировать транзакцию."""
        ...

    async def rollback(self) -> None:
        """Откатить транзакцию."""
        ...

    async def __aenter__(self) -> "UnitOfWorkProtocol":
        """Войти в контекст."""
        ...

    async def __aexit__(self, *args) -> None:
        """Выйти из контекста."""
        ...


class UnitOfWork:
    """
    SQLAlchemy реализация Unit of Work.

    Использование:
    ```python
    async with uow:
        book = await uow.books.create(title="...", ...)
        await uow.commit()
    ```

    Преимущества:
    - Атомарность: все операции в одной транзакции
    - Единый commit: репозитории не делают commit
    - Автоматический rollback при исключении
    - Все репозитории используют одну сессию
    """

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        """
        Инициализировать UnitOfWork.

        Args:
            session_factory: Фабрика для создания async сессий
        """
        self._session_factory = session_factory
        self._session: AsyncSession | None = None

    async def __aenter__(self) -> "UnitOfWork":
        """
        Войти в контекст - создать сессию и репозитории.

        Returns:
            UnitOfWork: Экземпляр с инициализированными репозиториями
        """
        self._session = self._session_factory()

        # Все репозитории используют ОДНУ сессию
        self.books = BookRepository(self._session)
        self.users = UserRepository(self._session)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """
        Выйти из контекста.

        При исключении - автоматический rollback.
        В любом случае - закрыть сессию.
        """
        if exc_type is not None:
            await self.rollback()

        if self._session is not None:
            await self._session.close()
            self._session = None

    async def commit(self) -> None:
        """
        Зафиксировать транзакцию.

        ЕДИНСТВЕННОЕ место где делается commit.
        """
        if self._session is not None:
            await self._session.commit()

    async def rollback(self) -> None:
        """
        Откатить транзакцию.

        Вызывается автоматически при исключении в контексте.
        """
        if self._session is not None:
            await self._session.rollback()

    @property
    def session(self) -> AsyncSession:
        """
        Получить текущую сессию.

        Returns:
            AsyncSession: Текущая сессия

        Raises:
            RuntimeError: Если UoW не в контексте
        """
        if self._session is None:
            raise RuntimeError("UnitOfWork must be used as context manager")
        return self._session
