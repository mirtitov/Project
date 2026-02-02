"""
Доменные исключения.

Содержит специфичные исключения для бизнес-логики книг.
"""

from uuid import UUID

from ..core.exceptions import AppException, ConflictException, NotFoundException


class BookNotFoundException(NotFoundException):
    """
    Исключение: Книга не найдена.

    Выбрасывается когда книга с указанным ID не существует.
    """

    def __init__(self, book_id: UUID):
        super().__init__(resource="Book", identifier=book_id)


class BookAlreadyExistsException(ConflictException):
    """
    Исключение: Книга с таким ISBN уже существует.

    Выбрасывается при попытке создать книгу с дублирующимся ISBN.
    """

    def __init__(self, isbn: str):
        super().__init__(
            message=f"Book with ISBN '{isbn}' already exists",
            details={"isbn": isbn},
        )


class InvalidYearException(AppException):
    """
    Исключение: Невалидный год издания.

    Выбрасывается когда год издания вне допустимого диапазона.
    """

    def __init__(self, year: int):
        from datetime import datetime

        current_year = datetime.now().year
        super().__init__(
            message=f"Year {year} is invalid (must be 1000-{current_year})",
            status_code=400,
            details={"year": year, "max_year": current_year},
        )


class InvalidPagesException(AppException):
    """
    Исключение: Невалидное количество страниц.

    Выбрасывается когда количество страниц <= 0.
    """

    def __init__(self, pages: int):
        super().__init__(
            message=f"Pages count must be positive, got {pages}",
            status_code=400,
            details={"pages": pages},
        )


class OpenLibraryException(AppException):
    """
    Исключение: Ошибка Open Library API.

    Выбрасывается при общих ошибках обращения к Open Library.
    """

    def __init__(self, message: str):
        super().__init__(
            message=f"Open Library API error: {message}",
            status_code=503,
            details={"service": "OpenLibrary"},
        )


class OpenLibraryTimeoutException(AppException):
    """
    Исключение: Таймаут при обращении к Open Library API.

    Выбрасывается когда запрос к Open Library превышает таймаут.
    """

    def __init__(self, timeout: float):
        super().__init__(
            message=f"Open Library API timeout after {timeout}s",
            status_code=504,
            details={"service": "OpenLibrary", "timeout": timeout},
        )


# ========== AUTH EXCEPTIONS ==========


class UserNotFoundException(NotFoundException):
    """
    Исключение: Пользователь не найден.
    """

    def __init__(self, user_id: UUID):
        super().__init__(resource="User", identifier=user_id)


class UserAlreadyExistsException(ConflictException):
    """
    Исключение: Пользователь уже существует.
    """

    def __init__(self, field: str, value: str):
        super().__init__(
            message=f"User with {field} '{value}' already exists",
            details={field: value},
        )


class InvalidCredentialsException(AppException):
    """
    Исключение: Неверные учётные данные.
    """

    def __init__(self, message: str = "Invalid username or password"):
        super().__init__(
            message=message,
            status_code=401,
        )


class TokenExpiredException(AppException):
    """
    Исключение: Токен истёк.
    """

    def __init__(self):
        super().__init__(
            message="Token has expired",
            status_code=401,
        )


class InvalidTokenException(AppException):
    """
    Исключение: Невалидный токен.
    """

    def __init__(self):
        super().__init__(
            message="Invalid token",
            status_code=401,
        )


class InsufficientPermissionsException(AppException):
    """
    Исключение: Недостаточно прав.
    """

    def __init__(self, required_role: str = "admin"):
        super().__init__(
            message=f"Insufficient permissions. Required role: {required_role}",
            status_code=403,
            details={"required_role": required_role},
        )
