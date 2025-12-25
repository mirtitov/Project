"""
API роутер для аутентификации.

Содержит эндпоинты для регистрации, логина и управления токенами.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from ...dependencies import AuthServiceDep, CurrentUser
from ..schemas.auth import Token, UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Регистрация",
    description="Зарегистрировать нового пользователя",
    responses={
        201: {"description": "Пользователь создан"},
        409: {"description": "Email или username уже заняты"},
    },
)
async def register(
    user_data: UserCreate,
    service: AuthServiceDep,
) -> UserResponse:
    """
    Зарегистрировать нового пользователя.
    
    - Email должен быть уникальным
    - Username должен быть уникальным
    - Пароль минимум 8 символов
    """
    return await service.register(user_data)


@router.post(
    "/login",
    response_model=Token,
    summary="Логин",
    description="Получить токены аутентификации",
    responses={
        200: {"description": "Успешный логин"},
        401: {"description": "Неверные учётные данные"},
    },
)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: AuthServiceDep,
) -> Token:
    """
    Выполнить логин.
    
    Принимает username (или email) и password.
    Возвращает access_token и refresh_token.
    """
    tokens = await service.login(
        username_or_email=form_data.username,
        password=form_data.password,
    )
    return Token(**tokens)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Текущий пользователь",
    description="Получить информацию о текущем пользователе",
    responses={
        200: {"description": "Информация о пользователе"},
        401: {"description": "Не авторизован"},
    },
)
async def get_current_user(
    current_user: CurrentUser,
) -> UserResponse:
    """
    Получить информацию о текущем авторизованном пользователе.
    
    Требует валидный access token в заголовке Authorization.
    """
    return UserResponse(
        user_id=current_user.user_id,
        email=current_user.email,
        username=current_user.username,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )

