"""
ORM модель книги.

Использует SQLAlchemy 2.0 синтаксис с Mapped и mapped_column.
"""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON, UUID
from sqlalchemy.orm import Mapped, mapped_column

from ...core.database import Base


class Book(Base):
    """
    ORM модель книги в библиотечном каталоге.

    Attributes:
        book_id: Уникальный идентификатор книги (UUID)
        title: Название книги
        author: Автор книги
        year: Год издания
        genre: Жанр книги
        pages: Количество страниц
        available: Доступность книги
        isbn: ISBN книги (опционально)
        description: Описание книги (опционально)
        extra: Дополнительные данные из Open Library (JSON)
        created_at: Дата создания записи
        updated_at: Дата последнего обновления
    """

    __tablename__ = "books"

    # Primary Key
    book_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )

    # Обязательные поля
    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        index=True,
    )

    author: Mapped[str] = mapped_column(
        String(300),
        nullable=False,
        index=True,
    )

    year: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    genre: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    pages: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    available: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    # Опциональные поля
    isbn: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
        unique=True,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    extra: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    def __repr__(self) -> str:
        """Строковое представление модели."""
        return (
            f"<Book(id={self.book_id}, title='{self.title}', author='{self.author}')>"
        )
