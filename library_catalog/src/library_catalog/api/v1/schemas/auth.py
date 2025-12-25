"""
Pydantic схемы для аутентификации.

Содержит схемы для регистрации, логина и токенов.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """
    Схема для регистрации пользователя.
    """
    
    email: EmailStr = Field(
        ...,
        description="Email пользователя",
        examples=["user@example.com"],
    )
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern=r"^[a-zA-Z0-9_]+$",
        description="Имя пользователя (только буквы, цифры, _)",
        examples=["john_doe"],
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Пароль (минимум 8 символов)",
        examples=["SecurePass123"],
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "email": "user@example.com",
                    "username": "john_doe",
                    "password": "SecurePass123",
                }
            ]
        }
    }


class UserLogin(BaseModel):
    """
    Схема для логина.
    """
    
    username: str = Field(
        ...,
        description="Username или email",
        examples=["john_doe"],
    )
    password: str = Field(
        ...,
        description="Пароль",
        examples=["SecurePass123"],
    )


class UserResponse(BaseModel):
    """
    Схема для отображения пользователя.
    """
    
    user_id: UUID = Field(..., description="ID пользователя")
    email: str = Field(..., description="Email")
    username: str = Field(..., description="Username")
    role: str = Field(..., description="Роль (user/admin)")
    is_active: bool = Field(..., description="Активен ли пользователь")
    created_at: datetime = Field(..., description="Дата регистрации")
    
    model_config = {
        "from_attributes": True,
    }


class Token(BaseModel):
    """
    Схема для токенов.
    """
    
    access_token: str = Field(..., description="Access token")
    refresh_token: str = Field(..., description="Refresh token")
    token_type: str = Field("bearer", description="Тип токена")


class TokenData(BaseModel):
    """
    Данные из токена.
    """
    
    user_id: UUID | None = None
    username: str | None = None
    role: str | None = None
    token_type: str | None = None


class RefreshTokenRequest(BaseModel):
    """
    Запрос на обновление токена.
    """
    
    refresh_token: str = Field(..., description="Refresh token")

