"""API v1 schemas."""

from .book import BookCreate, BookFilters, BookUpdate, ShowBook
from .common import (
    ErrorResponse,
    HealthCheckResponse,
    MessageResponse,
    PaginatedResponse,
    PaginationParams,
)

__all__ = [
    "BookCreate",
    "BookFilters",
    "BookUpdate",
    "ErrorResponse",
    "HealthCheckResponse",
    "MessageResponse",
    "PaginatedResponse",
    "PaginationParams",
    "ShowBook",
]
