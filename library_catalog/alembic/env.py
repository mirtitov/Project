"""
Alembic Environment Configuration.

Настраивает Alembic для работы с PostgreSQL.
Использует синхронный psycopg2 для миграций.
"""

from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context

# Импортировать config и Base
from src.library_catalog.core.config import settings
from src.library_catalog.core.database import Base

# Импортировать все модели (ОБЯЗАТЕЛЬНО!)
# Это нужно чтобы Alembic видел все таблицы
from src.library_catalog.data.models import book, user  # noqa

# this is the Alembic Config object
config = context.config

# Установить database_url из settings
# ВАЖНО: Заменяем asyncpg на psycopg2 для синхронных миграций
database_url = str(settings.database_url).replace("+asyncpg", "")
config.set_main_option("sqlalchemy.url", database_url)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Установить target_metadata из Base
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    Uses synchronous psycopg2 driver for migrations.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
