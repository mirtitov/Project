"""
Общие Pydantic схемы.

Содержит схемы для пагинации, health check и других общих элементов.
"""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationParams(BaseModel):
    """
    Параметры пагинации.

    Используется как Query параметры в эндпоинтах списков.
    """

    page: int = Field(
        1,
        ge=1,
        description="Номер страницы (начиная с 1)",
    )
    page_size: int = Field(
        20,
        ge=1,
        le=100,
        description="Размер страницы (1-100)",
    )

    @property
    def offset(self) -> int:
        """Вычислить offset для SQL запроса."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Limit для SQL запроса."""
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Generic схема для пагинированных ответов.

    Содержит список элементов и метаданные пагинации.
    """

    items: list[T] = Field(
        ...,
        description="Список элементов текущей страницы",
    )
    total: int = Field(
        ...,
        description="Общее количество элементов",
    )
    page: int = Field(
        ...,
        description="Текущая страница",
    )
    page_size: int = Field(
        ...,
        description="Размер страницы",
    )
    pages: int = Field(
        ...,
        description="Общее количество страниц",
    )

    @classmethod
    def create(
        cls,
        items: list[T],
        total: int,
        pagination: PaginationParams,
    ) -> "PaginatedResponse[T]":
        """
        Создать пагинированный ответ.

        Args:
            items: Список элементов текущей страницы
            total: Общее количество элементов
            pagination: Параметры пагинации

        Returns:
            PaginatedResponse: Готовый ответ с метаданными
        """
        # Вычислить количество страниц (ceiling division)
        pages = (
            (total + pagination.page_size - 1) // pagination.page_size
            if total > 0
            else 0
        )

        return cls(
            items=items,
            total=total,
            page=pagination.page,
            page_size=pagination.page_size,
            pages=pages,
        )


class HealthCheckResponse(BaseModel):
    """
    Схема для health check ответа.

    Содержит статус сервиса и его компонентов.
    """

    status: str = Field(
        "healthy",
        description="Общий статус сервиса",
    )
    database: str = Field(
        "connected",
        description="Статус подключения к БД",
    )


class MessageResponse(BaseModel):
    """
    Простой ответ с сообщением.

    Используется для информационных ответов.
    """

    message: str = Field(
        ...,
        description="Сообщение",
    )


class ErrorResponse(BaseModel):
    """
    Схема для ошибок.

    Используется для документации API.
    """

    detail: str = Field(
        ...,
        description="Описание ошибки",
    )
    type: str | None = Field(
        None,
        description="Тип ошибки",
    )
