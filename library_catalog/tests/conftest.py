"""
Pytest fixtures for testing.

Contains common fixtures used across all tests.
"""

import asyncio
from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.library_catalog.core.database import Base, get_db
from src.library_catalog.main import app

# Test database URL - uses a separate test database
TEST_DATABASE_URL = (
    "postgresql+asyncpg://postgres:postgres@localhost:5432/library_catalog_test"
)


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a test database session.

    Creates all tables before the test and drops them after.
    """
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    Create a test HTTP client.

    Overrides the database dependency to use the test database.
    """

    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def sample_book_data() -> dict:
    """Sample book data for testing."""
    return {
        "title": "Clean Code",
        "author": "Robert Martin",
        "year": 2008,
        "genre": "Programming",
        "pages": 464,
        "isbn": "978-0132350884",
        "description": "A Handbook of Agile Software Craftsmanship",
    }


@pytest.fixture
def sample_book_data_no_isbn() -> dict:
    """Sample book data without ISBN for testing."""
    return {
        "title": "The Pragmatic Programmer",
        "author": "David Thomas, Andrew Hunt",
        "year": 1999,
        "genre": "Programming",
        "pages": 352,
    }
