"""
Репозиторий для работы с пользователями.

Содержит методы для CRUD операций с пользователями.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.user import User
from .base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Репозиторий для работы с пользователями.

    Наследуется от BaseRepository и добавляет
    специфичные методы для работы с пользователями.
    """

    def __init__(self, session: AsyncSession):
        """
        Инициализировать репозиторий пользователей.

        Args:
            session: Async сессия БД
        """
        super().__init__(session, User)

    async def find_by_email(self, email: str) -> User | None:
        """
        Найти пользователя по email.

        Args:
            email: Email пользователя

        Returns:
            User | None: Найденный пользователь или None
        """
        stmt = select(User).where(User.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_username(self, username: str) -> User | None:
        """
        Найти пользователя по username.

        Args:
            username: Имя пользователя

        Returns:
            User | None: Найденный пользователь или None
        """
        stmt = select(User).where(User.username == username)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_email_or_username(
        self,
        email: str,
        username: str,
    ) -> User | None:
        """
        Найти пользователя по email или username.

        Используется для проверки уникальности при регистрации.

        Args:
            email: Email пользователя
            username: Имя пользователя

        Returns:
            User | None: Найденный пользователь или None
        """
        stmt = select(User).where((User.email == email) | (User.username == username))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
