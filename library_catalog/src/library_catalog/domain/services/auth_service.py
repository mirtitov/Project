"""
Сервис аутентификации.

Содержит логику регистрации, логина и работы с JWT токенами.
"""

import logging
from datetime import UTC, datetime, timedelta
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

from ...api.v1.schemas.auth import TokenData, UserCreate, UserResponse
from ...core.config import settings
from ...data.models.user import User, UserRole
from ...data.repositories.user_repository import UserRepository
from ..exceptions import (
    InvalidCredentialsException,
    UserAlreadyExistsException,
    UserNotFoundException,
)

# Контекст для хэширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """
    Сервис аутентификации.

    Отвечает за:
    - Регистрацию пользователей
    - Аутентификацию (логин)
    - Создание и валидацию JWT токенов
    - Хэширование паролей
    """

    def __init__(self, user_repository: UserRepository):
        """
        Инициализировать сервис.

        Args:
            user_repository: Репозиторий пользователей
        """
        self.user_repo = user_repository
        self.logger = logging.getLogger(__name__)

    # ========== ПАРОЛИ ==========

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Хэшировать пароль.

        Args:
            password: Пароль в открытом виде

        Returns:
            str: Хэш пароля
        """
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Проверить пароль.

        Args:
            plain_password: Пароль в открытом виде
            hashed_password: Хэш пароля

        Returns:
            bool: True если пароль верный
        """
        return pwd_context.verify(plain_password, hashed_password)

    # ========== JWT ТОКЕНЫ ==========

    @staticmethod
    def create_access_token(
        data: dict,
        expires_delta: timedelta | None = None,
    ) -> str:
        """
        Создать access token.

        Args:
            data: Данные для токена
            expires_delta: Время жизни токена

        Returns:
            str: JWT токен
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(
                minutes=settings.jwt_access_token_expire_minutes
            )

        to_encode.update({"exp": expire, "type": "access"})

        return jwt.encode(
            to_encode,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

    @staticmethod
    def create_refresh_token(
        data: dict,
        expires_delta: timedelta | None = None,
    ) -> str:
        """
        Создать refresh token.

        Args:
            data: Данные для токена
            expires_delta: Время жизни токена

        Returns:
            str: JWT токен
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.now(UTC) + expires_delta
        else:
            expire = datetime.now(UTC) + timedelta(
                days=settings.jwt_refresh_token_expire_days
            )

        to_encode.update({"exp": expire, "type": "refresh"})

        return jwt.encode(
            to_encode,
            settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
        )

    @staticmethod
    def decode_token(token: str) -> TokenData | None:
        """
        Декодировать JWT токен.

        Args:
            token: JWT токен

        Returns:
            TokenData | None: Данные токена или None если невалидный
        """
        try:
            payload = jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
            )

            user_id: str = payload.get("sub")
            username: str = payload.get("username")
            role: str = payload.get("role")
            token_type: str = payload.get("type")

            if user_id is None:
                return None

            return TokenData(
                user_id=UUID(user_id),
                username=username,
                role=role,
                token_type=token_type,
            )
        except JWTError:
            return None

    # ========== РЕГИСТРАЦИЯ И ЛОГИН ==========

    async def register(self, user_data: UserCreate) -> UserResponse:
        """
        Зарегистрировать нового пользователя.

        Args:
            user_data: Данные для регистрации

        Returns:
            UserResponse: Созданный пользователь

        Raises:
            UserAlreadyExistsException: Если email или username уже заняты
        """
        # Проверить уникальность
        existing = await self.user_repo.find_by_email_or_username(
            email=user_data.email,
            username=user_data.username,
        )
        if existing:
            if existing.email == user_data.email:
                raise UserAlreadyExistsException(
                    field="email",
                    value=user_data.email,
                )
            else:
                raise UserAlreadyExistsException(
                    field="username",
                    value=user_data.username,
                )

        # Создать пользователя
        hashed_password = self.hash_password(user_data.password)

        user = await self.user_repo.create(
            email=user_data.email,
            username=user_data.username,
            hashed_password=hashed_password,
            role=UserRole.USER.value,
        )

        # Commit транзакции (сервис отвечает за commit)
        await self.user_repo.session.commit()

        self.logger.info("User registered: %s", user.username)

        return UserResponse(
            user_id=user.user_id,
            email=user.email,
            username=user.username,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
        )

    async def authenticate(
        self,
        username_or_email: str,
        password: str,
    ) -> User:
        """
        Аутентифицировать пользователя.

        Args:
            username_or_email: Username или email
            password: Пароль

        Returns:
            User: Аутентифицированный пользователь

        Raises:
            InvalidCredentialsException: Если логин/пароль неверны
        """
        # Найти пользователя
        user = await self.user_repo.find_by_email(username_or_email)
        if not user:
            user = await self.user_repo.find_by_username(username_or_email)

        if not user:
            raise InvalidCredentialsException()

        # Проверить пароль
        if not self.verify_password(password, user.hashed_password):
            raise InvalidCredentialsException()

        # Проверить что пользователь активен
        if not user.is_active:
            raise InvalidCredentialsException("User is deactivated")

        self.logger.info("User authenticated: %s", user.username)

        return user

    async def login(
        self,
        username_or_email: str,
        password: str,
    ) -> dict[str, str]:
        """
        Выполнить логин и получить токены.

        Args:
            username_or_email: Username или email
            password: Пароль

        Returns:
            dict: access_token и refresh_token

        Raises:
            InvalidCredentialsException: Если логин/пароль неверны
        """
        user = await self.authenticate(username_or_email, password)

        # Создать токены
        token_data = {
            "sub": str(user.user_id),
            "username": user.username,
            "role": user.role,
        }

        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token(token_data)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }

    async def get_user_by_id(self, user_id: UUID) -> User:
        """
        Получить пользователя по ID.

        Args:
            user_id: UUID пользователя

        Returns:
            User: Найденный пользователь

        Raises:
            UserNotFoundException: Если пользователь не найден
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise UserNotFoundException(user_id)
        return user
