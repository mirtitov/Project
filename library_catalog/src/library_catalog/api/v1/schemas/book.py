"""
Pydantic схемы для книг.

Содержит схемы для создания, обновления и отображения книг.
"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class BookBase(BaseModel):
    """
    Базовая схема с общими полями.

    Используется как основа для других схем.
    """

    title: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Название книги",
        examples=["Clean Code"],
    )
    author: str = Field(
        ...,
        min_length=1,
        max_length=300,
        description="Автор книги",
        examples=["Robert Martin"],
    )
    year: int = Field(
        ...,
        ge=1000,
        le=2100,
        description="Год издания",
        examples=[2008],
    )
    genre: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Жанр книги",
        examples=["Programming"],
    )
    pages: int = Field(
        ...,
        gt=0,
        description="Количество страниц",
        examples=[464],
    )


class BookCreate(BookBase):
    """
    Схема для создания книги.

    Добавляет опциональные поля ISBN и описание.
    """

    isbn: str | None = Field(
        None,
        min_length=10,
        max_length=20,
        description="ISBN книги (10 или 13 цифр)",
        examples=["978-0132350884"],
    )
    description: str | None = Field(
        None,
        max_length=5000,
        description="Описание книги",
        examples=["A Handbook of Agile Software Craftsmanship"],
    )

    @field_validator("isbn")
    @classmethod
    def validate_isbn(cls, v: str | None) -> str | None:
        """
        Валидация формата ISBN.

        Проверяет что ISBN содержит только цифры и имеет правильную длину.
        """
        if v is None:
            return v

        # Удалить дефисы и пробелы
        clean = v.replace("-", "").replace(" ", "")

        # Проверить что только цифры (и X для ISBN-10)
        if not clean.replace("X", "").replace("x", "").isdigit():
            raise ValueError("ISBN must contain only digits and dashes")

        # Проверить длину
        if len(clean) not in (10, 13):
            raise ValueError("ISBN must be 10 or 13 digits")

        return v

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Clean Code",
                    "author": "Robert Martin",
                    "year": 2008,
                    "genre": "Programming",
                    "pages": 464,
                    "isbn": "978-0132350884",
                    "description": "A Handbook of Agile Software Craftsmanship",
                }
            ]
        }
    }


class BookUpdate(BaseModel):
    """
    Схема для обновления книги.

    Все поля опциональны - передаются только изменяемые.
    """

    title: str | None = Field(
        None,
        min_length=1,
        max_length=500,
        description="Название книги",
    )
    author: str | None = Field(
        None,
        min_length=1,
        max_length=300,
        description="Автор книги",
    )
    year: int | None = Field(
        None,
        ge=1000,
        le=2100,
        description="Год издания",
    )
    genre: str | None = Field(
        None,
        min_length=1,
        max_length=100,
        description="Жанр книги",
    )
    pages: int | None = Field(
        None,
        gt=0,
        description="Количество страниц",
    )
    available: bool | None = Field(
        None,
        description="Доступность книги",
    )
    isbn: str | None = Field(
        None,
        description="ISBN книги",
    )
    description: str | None = Field(
        None,
        description="Описание книги",
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "available": False,
                }
            ]
        }
    }


class ShowBook(BookBase):
    """
    Схема для отображения книги (response).

    Включает все поля, включая автогенерируемые.
    """

    book_id: UUID = Field(
        ...,
        description="Уникальный идентификатор книги",
    )
    available: bool = Field(
        ...,
        description="Доступность книги",
    )
    isbn: str | None = Field(
        None,
        description="ISBN книги",
    )
    description: str | None = Field(
        None,
        description="Описание книги",
    )
    extra: dict[str, Any] | None = Field(
        None,
        description="Дополнительные данные из Open Library",
    )
    created_at: datetime = Field(
        ...,
        description="Дата создания записи",
    )
    updated_at: datetime = Field(
        ...,
        description="Дата последнего обновления",
    )

    model_config = {
        "from_attributes": True,  # Для работы с ORM моделями
        "json_schema_extra": {
            "examples": [
                {
                    "book_id": "123e4567-e89b-12d3-a456-426614174000",
                    "title": "Clean Code",
                    "author": "Robert Martin",
                    "year": 2008,
                    "genre": "Programming",
                    "pages": 464,
                    "available": True,
                    "isbn": "978-0132350884",
                    "description": "A Handbook of Agile Software Craftsmanship",
                    "extra": {
                        "cover_url": "https://covers.openlibrary.org/b/id/123-L.jpg",
                        "subjects": ["Computer Science", "Software Engineering"],
                    },
                    "created_at": "2024-01-01T12:00:00",
                    "updated_at": "2024-01-01T12:00:00",
                }
            ]
        },
    }


class BookFilters(BaseModel):
    """
    Схема для фильтров поиска книг.

    Используется как Query параметры.
    """

    title: str | None = Field(
        None,
        description="Поиск по названию (частичное совпадение)",
    )
    author: str | None = Field(
        None,
        description="Поиск по автору (частичное совпадение)",
    )
    genre: str | None = Field(
        None,
        description="Точное совпадение жанра",
    )
    year: int | None = Field(
        None,
        description="Точное совпадение года",
    )
    available: bool | None = Field(
        None,
        description="Фильтр по доступности",
    )
