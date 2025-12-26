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
    "BookUpdate",
    "ShowBook",
    "BookFilters",
    "PaginationParams",
    "PaginatedResponse",
    "HealthCheckResponse",
    "MessageResponse",
    "ErrorResponse",
]

