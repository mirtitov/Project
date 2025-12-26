"""
API роутер для книг.

Содержит все CRUD эндпоинты для работы с книгами.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status

from ....core.rate_limit import limiter
from ...dependencies import BookServiceDep
from ..schemas.book import BookCreate, BookUpdate, ShowBook
from ..schemas.common import PaginatedResponse, PaginationParams

router = APIRouter(prefix="/books", tags=["Books"])


@router.post(
    "/",
    response_model=ShowBook,
    status_code=status.HTTP_201_CREATED,
    summary="Создать книгу",
    description="Создать новую книгу в каталоге с автоматическим обогащением из Open Library",
    responses={
        201: {"description": "Книга успешно создана"},
        400: {"description": "Невалидные данные"},
        409: {"description": "Книга с таким ISBN уже существует"},
        429: {"description": "Превышен лимит запросов"},
    },
)
@limiter.limit("30/minute")
async def create_book(
    request: Request,
    book_data: BookCreate,
    service: BookServiceDep,
) -> ShowBook:
    """
    Создать новую книгу.
    
    Автоматически обогащает данные из Open Library API:
    - Обложка книги
    - Темы/subjects
    - Издатель
    - Рейтинг
    
    Если Open Library недоступен, книга все равно будет создана.
    """
    return await service.create_book(book_data)


@router.get(
    "/",
    response_model=PaginatedResponse[ShowBook],
    summary="Получить список книг",
    description="Получить список книг с фильтрацией и пагинацией",
    responses={429: {"description": "Превышен лимит запросов"}},
)
@limiter.limit("100/minute")
async def get_books(
    request: Request,
    service: BookServiceDep,
    pagination: Annotated[PaginationParams, Depends()],
    title: str | None = Query(None, description="Поиск по названию (частичное совпадение)"),
    author: str | None = Query(None, description="Поиск по автору (частичное совпадение)"),
    genre: str | None = Query(None, description="Фильтр по жанру (точное совпадение)"),
    year: int | None = Query(None, description="Фильтр по году (точное совпадение)"),
    available: bool | None = Query(None, description="Фильтр по доступности"),
) -> PaginatedResponse[ShowBook]:
    """
    Получить список книг с фильтрацией.
    
    Поддерживаемые фильтры:
    - title: частичное совпадение (регистронезависимо)
    - author: частичное совпадение (регистронезависимо)
    - genre: точное совпадение
    - year: точное совпадение
    - available: True/False
    
    Пагинация:
    - page: номер страницы (начиная с 1)
    - page_size: размер страницы (1-100, по умолчанию 20)
    """
    books, total = await service.search_books(
        title=title,
        author=author,
        genre=genre,
        year=year,
        available=available,
        limit=pagination.limit,
        offset=pagination.offset,
    )
    
    return PaginatedResponse.create(books, total, pagination)


@router.get(
    "/{book_id}",
    response_model=ShowBook,
    summary="Получить книгу",
    description="Получить информацию о конкретной книге по ID",
    responses={
        200: {"description": "Книга найдена"},
        404: {"description": "Книга не найдена"},
        429: {"description": "Превышен лимит запросов"},
    },
)
@limiter.limit("100/minute")
async def get_book(
    request: Request,
    book_id: UUID,
    service: BookServiceDep,
) -> ShowBook:
    """
    Получить книгу по ID.
    
    Returns:
        ShowBook: Полная информация о книге
        
    Raises:
        404: Книга не найдена
    """
    return await service.get_book(book_id)


@router.patch(
    "/{book_id}",
    response_model=ShowBook,
    summary="Обновить книгу",
    description="Частичное обновление книги (передаются только изменяемые поля)",
    responses={
        200: {"description": "Книга обновлена"},
        400: {"description": "Невалидные данные"},
        404: {"description": "Книга не найдена"},
        429: {"description": "Превышен лимит запросов"},
    },
)
@limiter.limit("30/minute")
async def update_book(
    request: Request,
    book_id: UUID,
    book_data: BookUpdate,
    service: BookServiceDep,
) -> ShowBook:
    """
    Обновить книгу.
    
    Передаются только те поля, которые нужно изменить.
    Остальные поля остаются без изменений.
    
    Returns:
        ShowBook: Обновленная книга
        
    Raises:
        404: Книга не найдена
        400: Невалидные данные
    """
    return await service.update_book(book_id, book_data)


@router.delete(
    "/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить книгу",
    description="Удалить книгу из каталога",
    responses={
        204: {"description": "Книга удалена"},
        404: {"description": "Книга не найдена"},
        429: {"description": "Превышен лимит запросов"},
    },
)
@limiter.limit("10/minute")
async def delete_book(
    request: Request,
    book_id: UUID,
    service: BookServiceDep,
) -> None:
    """
    Удалить книгу.
    
    Raises:
        404: Книга не найдена
    """
    await service.delete_book(book_id)

