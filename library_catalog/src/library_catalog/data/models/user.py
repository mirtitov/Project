"""
ORM модель пользователя.

Содержит данные пользователя для аутентификации и авторизации.
"""

import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from ...core.database import Base


class UserRole(str, Enum):
    """Роли пользователей."""
    
    USER = "user"
    ADMIN = "admin"


class User(Base):
    """
    ORM модель пользователя.
    
    Attributes:
        user_id: Уникальный идентификатор
        email: Email пользователя (уникальный)
        username: Имя пользователя (уникальное)
        hashed_password: Хэш пароля
        role: Роль пользователя (user/admin)
        is_active: Активен ли пользователь
        created_at: Дата регистрации
        updated_at: Дата последнего обновления
    """
    
    __tablename__ = "users"
    
    # Primary Key
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    
    # Аутентификация
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )
    
    username: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
    )
    
    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    # Авторизация
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=UserRole.USER.value,
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
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
        return f"<User(id={self.user_id}, username='{self.username}', role='{self.role}')>"
    
    @property
    def is_admin(self) -> bool:
        """Проверить, является ли пользователь администратором."""
        return self.role == UserRole.ADMIN.value

