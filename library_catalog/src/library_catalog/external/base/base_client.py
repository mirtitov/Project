"""
Базовый HTTP клиент для внешних API.

Содержит общую логику для HTTP запросов с retry и обработкой ошибок.
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any

import httpx


class BaseApiClient(ABC):
    """
    Базовый класс для HTTP клиентов внешних API.
    
    Включает:
    - Retry логику с exponential backoff
    - Обработку ошибок
    - Логирование
    - Timeout management
    
    Attributes:
        base_url: Базовый URL API
        timeout: Таймаут запроса в секундах
        retries: Количество попыток
        backoff: Базовое время ожидания между попытками
    """
    
    def __init__(
        self,
        base_url: str,
        timeout: float = 10.0,
        retries: int = 3,
        backoff: float = 0.5,
    ):
        """
        Инициализировать клиент.
        
        Args:
            base_url: Базовый URL API
            timeout: Таймаут запроса в секундах
            retries: Количество попыток
            backoff: Базовое время ожидания между попытками
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.retries = retries
        self.backoff = backoff
        self._client: httpx.AsyncClient | None = None
        self.logger = logging.getLogger(self.client_name())
    
    @abstractmethod
    def client_name(self) -> str:
        """
        Имя клиента для логирования.
        
        Returns:
            str: Имя клиента
        """
        pass
    
    @property
    def client(self) -> httpx.AsyncClient:
        """
        Получить HTTP клиент (lazy initialization).
        
        Returns:
            httpx.AsyncClient: HTTP клиент
        """
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
            )
        return self._client
    
    def _build_url(self, path: str) -> str:
        """
        Построить полный URL.
        
        Args:
            path: Путь API
            
        Returns:
            str: Полный URL
        """
        if not path.startswith("/"):
            path = "/" + path
        return self.base_url + path
    
    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Выполнить HTTP запрос с retry логикой.
        
        Args:
            method: HTTP метод
            path: Путь API
            params: Query параметры
            json: JSON тело запроса
            headers: HTTP заголовки
            
        Returns:
            dict: JSON ответ
            
        Raises:
            httpx.TimeoutException: При таймауте
            httpx.HTTPError: При HTTP ошибке
        """
        url = self._build_url(path)
        
        for attempt in range(self.retries):
            try:
                self.logger.debug(
                    "%s %s params=%s attempt=%d",
                    method,
                    url,
                    params,
                    attempt + 1,
                )
                
                response = await self.client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json,
                    headers=headers,
                )
                
                response.raise_for_status()
                return response.json()
            
            except httpx.TimeoutException:
                if attempt == self.retries - 1:
                    self.logger.error(
                        "Timeout after %d attempts: %s",
                        self.retries,
                        url,
                    )
                    raise
                
                wait_time = self.backoff * (2 ** attempt)
                self.logger.warning(
                    "Timeout, retrying in %.1fs (attempt %d/%d)",
                    wait_time,
                    attempt + 1,
                    self.retries,
                )
                await asyncio.sleep(wait_time)
            
            except httpx.HTTPStatusError as e:
                # 5xx ошибки - retry
                if e.response.status_code >= 500 and attempt < self.retries - 1:
                    wait_time = self.backoff * (2 ** attempt)
                    self.logger.warning(
                        "Server error %d, retrying in %.1fs",
                        e.response.status_code,
                        wait_time,
                    )
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error("HTTP error: %s", e)
                    raise
        
        # Если все попытки исчерпаны
        raise httpx.HTTPError(f"All {self.retries} attempts failed")
    
    async def _get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        GET запрос.
        
        Args:
            path: Путь API
            params: Query параметры
            headers: HTTP заголовки
            
        Returns:
            dict: JSON ответ
        """
        return await self._request("GET", path, params=params, headers=headers)
    
    async def _post(
        self,
        path: str,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        POST запрос.
        
        Args:
            path: Путь API
            json: JSON тело
            params: Query параметры
            headers: HTTP заголовки
            
        Returns:
            dict: JSON ответ
        """
        return await self._request("POST", path, params=params, json=json, headers=headers)
    
    async def close(self) -> None:
        """Закрыть HTTP клиент."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

