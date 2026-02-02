"""
Pydantic схемы для Open Library API.

Содержит схемы для парсинга ответов от Open Library.
"""

from pydantic import BaseModel, Field


class OpenLibrarySearchDoc(BaseModel):
    """
    Документ из поиска Open Library.

    Содержит данные об одной книге из результатов поиска.
    """

    title: str
    author_name: list[str] | None = Field(None, alias="author_name")
    cover_i: int | None = Field(None, alias="cover_i")
    subject: list[str] | None = None
    publisher: list[str] | None = None
    language: list[str] | None = None
    ratings_average: float | None = Field(None, alias="ratings_average")
    first_publish_year: int | None = Field(None, alias="first_publish_year")
    edition_count: int | None = Field(None, alias="edition_count")
    isbn: list[str] | None = None

    model_config = {
        "populate_by_name": True,
    }


class OpenLibrarySearchResponse(BaseModel):
    """
    Ответ от /search.json

    Содержит результаты поиска и метаданные.
    """

    num_found: int = Field(
        ..., alias="numFound", description="Количество найденных результатов"
    )
    start: int = Field(0, description="Начальный индекс")
    docs: list[OpenLibrarySearchDoc] = Field(
        default_factory=list,
        description="Список найденных книг",
    )

    model_config = {
        "populate_by_name": True,
    }


class OpenLibraryBookData(BaseModel):
    """
    Обогащенные данные книги из Open Library.

    Используется для хранения в поле extra книги.
    """

    cover_url: str | None = Field(None, description="URL обложки")
    subjects: list[str] | None = Field(None, description="Темы/категории")
    publisher: str | None = Field(None, description="Издатель")
    language: str | None = Field(None, description="Язык")
    rating: float | None = Field(None, description="Рейтинг")
    first_publish_year: int | None = Field(None, description="Год первой публикации")
    edition_count: int | None = Field(None, description="Количество изданий")
