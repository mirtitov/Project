# ============================================
# LIBRARY CATALOG API - DOCKERFILE
# Multi-stage build for optimized production image
# ============================================

# ============================================
# STAGE 1: Builder
# ============================================
FROM python:3.13-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
COPY pyproject.toml ./
RUN pip install --upgrade pip && \
    pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --only main --no-interaction --no-ansi || \
    pip install fastapi uvicorn[standard] sqlalchemy alembic asyncpg \
        pydantic pydantic-settings httpx python-dotenv \
        redis cachetools python-jose[cryptography] passlib[bcrypt] bcrypt greenlet

# ============================================
# STAGE 2: Production
# ============================================
FROM python:3.13-slim as production

# Labels
LABEL maintainer="developer@example.com" \
      version="1.0.0" \
      description="Library Catalog API"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Create non-root user for security
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home appuser

# Copy application code
COPY --chown=appuser:appuser . .

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health/ || exit 1

# Run application
CMD ["uvicorn", "src.library_catalog.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ============================================
# STAGE 3: Development (optional)
# ============================================
FROM production as development

USER root

# Install dev dependencies
RUN pip install pytest pytest-asyncio black ruff mypy

USER appuser

# Run with reload for development
CMD ["uvicorn", "src.library_catalog.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

