"""
Library Catalog API - Точка входа приложения.

FastAPI приложение для управления библиотечным каталогом.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .api.v1.routers import auth, books, health
from .core.cache import init_cache
from .core.clients import clients_manager
from .core.config import settings
from .core.database import dispose_engine
from .core.exceptions import register_exception_handlers
from .core.logging_config import setup_logging
from .core.rate_limit import limiter

# ========== LIFECYCLE EVENTS ==========


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager для FastAPI.

    Выполняется при:
    - startup: настройка логирования, инициализация кэша
    - shutdown: закрытие подключений к БД
    """
    # Startup
    setup_logging()

    # Инициализация кэша
    use_redis = settings.cache_backend == "redis"
    init_cache(use_redis=use_redis, redis_url=settings.redis_url)
    cache_type = "Redis" if use_redis else "In-Memory"

    print("🚀 Application started")
    print(f"📚 {settings.app_name} v1.0.0")
    print(f"📖 Docs: http://localhost:8000{settings.docs_url}")
    print(f"💾 Cache: {cache_type}")

    yield

    # Shutdown
    print("👋 Shutting down...")

    # Закрыть внешние клиенты (избегаем memory leak)
    await clients_manager.close_all()

    # Закрыть соединения с БД
    await dispose_engine()

    print("✅ Application stopped")


# ========== CREATE APP ==========


app = FastAPI(
    title=settings.app_name,
    description="""
# Library Catalog API

REST API для управления библиотечным каталогом.

## Возможности

- 📚 **CRUD операции** с книгами
- 🔍 **Поиск и фильтрация** по названию, автору, жанру, году
- 🌐 **Автоматическое обогащение** данных из Open Library
- 📄 **Пагинация** результатов
- ✅ **Валидация** данных

## Технологии

- FastAPI + Uvicorn
- PostgreSQL + SQLAlchemy 2.0
- Pydantic 2.0
- httpx для HTTP запросов
""",
    version="1.0.0",
    docs_url=settings.docs_url,
    redoc_url=settings.redoc_url,
    lifespan=lifespan,
)


# ========== MIDDLEWARE ==========


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========== RATE LIMITING ==========


# Добавляем limiter в state для доступа из роутеров
app.state.limiter = limiter

# Обработчик для превышения лимита
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ========== EXCEPTION HANDLERS ==========


register_exception_handlers(app)


# ========== ROUTERS ==========


# Версия 1 API
app.include_router(
    auth.router,
    prefix=settings.api_v1_prefix,
)
app.include_router(
    books.router,
    prefix=settings.api_v1_prefix,
)
app.include_router(
    health.router,
    prefix=settings.api_v1_prefix,
)


# ========== ROOT ENDPOINT ==========


@app.get("/", tags=["Root"])
async def root():
    """
    Корневой эндпоинт.

    Возвращает приветственное сообщение и ссылки на документацию.
    """
    return {
        "message": f"Welcome to {settings.app_name}",
        "docs": settings.docs_url,
        "redoc": settings.redoc_url,
        "version": "1.0.0",
    }


# ========== RUN ==========


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.library_catalog.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
