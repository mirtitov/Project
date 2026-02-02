"""
Настройка подключения к базе данных.

Использует async SQLAlchemy 2.0 для работы с PostgreSQL.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from .config import settings


class Base(DeclarativeBase):
    """Базовый класс для всех ORM моделей."""

    pass


# Создать async engine
engine: AsyncEngine = create_async_engine(
    settings.database_url_str,
    pool_size=settings.database_pool_size,
    echo=settings.debug,
    pool_pre_ping=True,
)

# Создать session maker
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency для получения сессии БД.

    Создает новую сессию для каждого запроса.
    Автоматически закрывает сессию после использования.

    Yields:
        AsyncSession: Async сессия SQLAlchemy
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """
    Инициализировать подключение к БД.

    Проверяет, что БД доступна при старте приложения.
    """
    async with engine.begin() as conn:
        # Проверка подключения
        await conn.run_sync(lambda _: None)


async def check_db_connection() -> bool:
    """
    Проверить подключение к БД.

    Returns:
        bool: True если подключение успешно, False иначе
    """
    try:
        async with async_session_maker() as session:
            from sqlalchemy import text

            await session.execute(text("SELECT 1"))
            return True
    except Exception:
        return False


async def dispose_engine() -> None:
    """
    Закрыть все соединения с БД.

    Вызывается при остановке приложения.
    """
    await engine.dispose()
