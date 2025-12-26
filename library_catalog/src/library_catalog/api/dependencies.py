"""
Dependency Injection контейнер.

Содержит фабрики для создания сервисов, репозиториев и клиентов.
"""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.cache import CacheService, get_cache_service
from ..core.clients import clients_manager
from ..core.config import settings
from ..core.database import get_db
from ..data.models.user import User
from ..data.repositories.book_repository import BookRepository
from ..data.repositories.user_repository import UserRepository
from ..domain.exceptions import InsufficientPermissionsException
from ..domain.services.auth_service import AuthService
from ..domain.services.book_service import BookService
from ..external.openlibrary.cached_client import CachedOpenLibraryClient
from ..external.openlibrary.client import OpenLibraryClient


# ========== OAUTH2 ==========

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.api_v1_prefix}/auth/login",
    auto_error=False,
)


# ========== CACHE ==========


def get_cache() -> CacheService:
    """
    Получить сервис кэширования.
    
    Returns:
        CacheService: Сервис кэширования
    """
    return get_cache_service()


# ========== EXTERNAL CLIENTS (Managed by ClientsManager) ==========


def get_openlibrary_client() -> OpenLibraryClient:
    """
    Получить OpenLibraryClient из менеджера клиентов.
    
    ClientsManager обеспечивает:
    - Lazy initialization
    - Proper cleanup при shutdown
    - Отсутствие memory leak
    
    Returns:
        OpenLibraryClient: Клиент Open Library API
    """
    return clients_manager.get_openlibrary()


def get_cached_openlibrary_client() -> CachedOpenLibraryClient:
    """
    Получить CachedOpenLibraryClient из менеджера клиентов.
    
    Returns:
        CachedOpenLibraryClient: Кэширующий клиент Open Library
    """
    return clients_manager.get_cached_openlibrary()


# ========== REPOSITORIES ==========


async def get_book_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> BookRepository:
    """
    Создать BookRepository для текущей сессии БД.
    
    Создается новый экземпляр для каждого запроса.
    
    Args:
        db: Async сессия БД
        
    Returns:
        BookRepository: Репозиторий книг
    """
    return BookRepository(db)


async def get_user_repository(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserRepository:
    """
    Создать UserRepository для текущей сессии БД.
    
    Args:
        db: Async сессия БД
        
    Returns:
        UserRepository: Репозиторий пользователей
    """
    return UserRepository(db)


# ========== SERVICES ==========


async def get_book_service(
    book_repo: Annotated[BookRepository, Depends(get_book_repository)],
    ol_client: Annotated[CachedOpenLibraryClient, Depends(get_cached_openlibrary_client)],
) -> BookService:
    """
    Создать BookService с внедренными зависимостями.
    
    FastAPI автоматически разрешит все зависимости:
    1. get_db() создаст AsyncSession
    2. get_book_repository() создаст BookRepository с session
    3. get_cached_openlibrary_client() вернет кэширующий клиент
    4. Все внедрится в BookService
    
    Args:
        book_repo: Репозиторий книг
        ol_client: Кэширующий клиент Open Library
        
    Returns:
        BookService: Сервис для работы с книгами
    """
    return BookService(
        book_repository=book_repo,
        openlibrary_client=ol_client,
    )


async def get_auth_service(
    user_repo: Annotated[UserRepository, Depends(get_user_repository)],
) -> AuthService:
    """
    Создать AuthService.
    
    Args:
        user_repo: Репозиторий пользователей
        
    Returns:
        AuthService: Сервис аутентификации
    """
    return AuthService(user_repository=user_repo)


# ========== AUTHENTICATION ==========


async def get_current_user(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User:
    """
    Получить текущего пользователя из токена.
    
    Args:
        token: JWT токен из заголовка Authorization
        auth_service: Сервис аутентификации
        
    Returns:
        User: Текущий пользователь
        
    Raises:
        HTTPException: Если токен невалиден
    """
    if token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token_data = AuthService.decode_token(token)
    
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if token_data.token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await auth_service.get_user_by_id(token_data.user_id)
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User is deactivated",
        )
    
    return user


async def get_current_user_optional(
    token: Annotated[str | None, Depends(oauth2_scheme)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> User | None:
    """
    Получить текущего пользователя (опционально).
    
    Не выбрасывает исключение если пользователь не авторизован.
    """
    if token is None:
        return None
    
    try:
        return await get_current_user(token, auth_service)
    except HTTPException:
        return None


async def get_admin_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Получить текущего пользователя с правами админа.
    
    Raises:
        InsufficientPermissionsException: Если пользователь не админ
    """
    if not current_user.is_admin:
        raise InsufficientPermissionsException("admin")
    return current_user


# ========== TYPE ALIASES ДЛЯ УДОБСТВА ==========

# Можно использовать в роутерах так:
# async def my_route(service: BookServiceDep):
BookServiceDep = Annotated[BookService, Depends(get_book_service)]
BookRepoDep = Annotated[BookRepository, Depends(get_book_repository)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
DbSessionDep = Annotated[AsyncSession, Depends(get_db)]
CacheDep = Annotated[CacheService, Depends(get_cache)]

# Аутентификация
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentUserOptional = Annotated[User | None, Depends(get_current_user_optional)]
AdminUser = Annotated[User, Depends(get_admin_user)]
