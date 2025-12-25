# 📚 Library Catalog API

REST API для управления библиотечным каталогом, построенный на FastAPI с использованием современных практик разработки.

## 🚀 Возможности

- ✅ CRUD операции с книгами
- ✅ Поиск и фильтрация
- ✅ Автоматическое обогащение данных из Open Library API
- ✅ Хранение в PostgreSQL
- ✅ Пагинация результатов
- ✅ **Кэширование (Redis / In-Memory)**
- ✅ **JWT аутентификация**
- ✅ **Роли пользователей (user/admin)**
- ✅ **Docker контейнеризация**
- ✅ Swagger/ReDoc документация

## 🛠️ Технологии

| Компонент | Технология |
|-----------|------------|
| Web Framework | FastAPI 0.109+ |
| ASGI Server | Uvicorn 0.27+ |
| Database | PostgreSQL 16+ |
| ORM | SQLAlchemy 2.0+ |
| Migrations | Alembic 1.13+ |
| Validation | Pydantic 2.5+ |
| HTTP Client | httpx 0.26+ |
| Cache | Redis 7+ / cachetools |
| Auth | JWT (python-jose) |
| Container | Docker |

## 📁 Структура проекта

```
library_catalog/
├── src/library_catalog/
│   ├── api/           # API Layer (endpoints, schemas, DI)
│   ├── core/          # Core (config, database, cache, exceptions)
│   ├── data/          # Data Layer (models, repositories)
│   ├── domain/        # Domain Layer (services, mappers)
│   ├── external/      # External Layer (API clients)
│   └── utils/         # Utilities
├── alembic/           # Database migrations
├── tests/             # Tests
├── Dockerfile         # Multi-stage Docker build
└── docker-compose.yml # Full stack configuration
```

## 🚀 Быстрый старт

### Вариант 1: Docker (рекомендуется)

```bash
# Запустить весь стек
docker compose up -d

# Применить миграции
docker compose --profile migrations up migrations

# Открыть документацию
open http://localhost:8000/docs
```

### Вариант 2: Локально

```bash
# 1. Запустить PostgreSQL и Redis
docker compose up -d postgres redis

# 2. Создать виртуальное окружение
python -m venv .venv
source .venv/bin/activate

# 3. Установить зависимости
pip install -r requirements.txt
# или
pip install fastapi uvicorn sqlalchemy alembic asyncpg pydantic pydantic-settings httpx python-dotenv redis cachetools python-jose passlib bcrypt greenlet

# 4. Применить миграции
python -m alembic upgrade head

# 5. Запустить приложение
python -m uvicorn src.library_catalog.main:app --reload
```

## 📚 API Endpoints

### 📖 Books

| Метод | URL | Описание | Auth |
|-------|-----|----------|------|
| `GET` | `/api/v1/books` | Список книг | - |
| `POST` | `/api/v1/books` | Создать книгу | - |
| `GET` | `/api/v1/books/{id}` | Получить книгу | - |
| `PATCH` | `/api/v1/books/{id}` | Обновить книгу | - |
| `DELETE` | `/api/v1/books/{id}` | Удалить книгу | - |

### 🔐 Authentication

| Метод | URL | Описание |
|-------|-----|----------|
| `POST` | `/api/v1/auth/register` | Регистрация |
| `POST` | `/api/v1/auth/login` | Логин (получить токен) |
| `GET` | `/api/v1/auth/me` | Текущий пользователь |

### ❤️ Health

| Метод | URL | Описание |
|-------|-----|----------|
| `GET` | `/api/v1/health` | Health check |

## 🔐 Аутентификация

### Регистрация
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "username": "john", "password": "SecurePass123"}'
```

### Логин
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=john&password=SecurePass123"
```

### Использование токена
```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <access_token>"
```

## 💾 Кэширование

Поддерживается два бэкенда:

- **In-Memory** (по умолчанию) — для разработки
- **Redis** — для production

```bash
# Использовать Redis
CACHE_BACKEND=redis
REDIS_URL=redis://localhost:6379
```

## 🐳 Docker

### Полный стек (production)
```bash
docker compose up -d
```

### Только для разработки
```bash
docker compose --profile dev up -d api-dev
```

### Сборка образа
```bash
docker build -t library-catalog:latest .
```

## 🧪 Тестирование

```bash
# Запустить тесты
python -m pytest

# С покрытием
python -m pytest --cov=src
```

## 📝 Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `DATABASE_URL` | URL PostgreSQL | postgresql+asyncpg://... |
| `REDIS_URL` | URL Redis | redis://localhost:6379 |
| `CACHE_BACKEND` | memory / redis | memory |
| `JWT_SECRET_KEY` | Секрет для JWT | change-me |
| `DEBUG` | Режим отладки | true |

## 📖 Документация

После запуска доступна:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📝 Лицензия

MIT License
