"""
Integration tests for Books API.

Tests the complete API flow including database operations.
"""

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


class TestBooksAPI:
    """Tests for /api/v1/books endpoints."""
    
    async def test_health_check(self, client: AsyncClient):
        """Test health check endpoint."""
        response = await client.get("/api/v1/health/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    async def test_create_book(self, client: AsyncClient, sample_book_data: dict):
        """Test creating a new book."""
        response = await client.post(
            "/api/v1/books/",
            json=sample_book_data,
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_book_data["title"]
        assert data["author"] == sample_book_data["author"]
        assert "book_id" in data
    
    async def test_get_book(self, client: AsyncClient, sample_book_data: dict):
        """Test getting a book by ID."""
        # Create a book first
        create_response = await client.post(
            "/api/v1/books/",
            json=sample_book_data,
        )
        book_id = create_response.json()["book_id"]
        
        # Get the book
        response = await client.get(f"/api/v1/books/{book_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["book_id"] == book_id
        assert data["title"] == sample_book_data["title"]
    
    async def test_get_book_not_found(self, client: AsyncClient):
        """Test getting a non-existent book."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/api/v1/books/{fake_id}")
        
        assert response.status_code == 404
    
    async def test_update_book(self, client: AsyncClient, sample_book_data: dict):
        """Test updating a book."""
        # Create a book first
        create_response = await client.post(
            "/api/v1/books/",
            json=sample_book_data,
        )
        book_id = create_response.json()["book_id"]
        
        # Update the book
        update_data = {"available": False}
        response = await client.patch(
            f"/api/v1/books/{book_id}",
            json=update_data,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False
    
    async def test_delete_book(self, client: AsyncClient, sample_book_data: dict):
        """Test deleting a book."""
        # Create a book first
        create_response = await client.post(
            "/api/v1/books/",
            json=sample_book_data,
        )
        book_id = create_response.json()["book_id"]
        
        # Delete the book
        response = await client.delete(f"/api/v1/books/{book_id}")
        
        assert response.status_code == 204
        
        # Verify it's deleted
        get_response = await client.get(f"/api/v1/books/{book_id}")
        assert get_response.status_code == 404
    
    async def test_list_books(self, client: AsyncClient, sample_book_data: dict):
        """Test listing books."""
        # Create a book first
        await client.post("/api/v1/books/", json=sample_book_data)
        
        # List books
        response = await client.get("/api/v1/books/")
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) >= 1
    
    async def test_search_books_by_title(
        self,
        client: AsyncClient,
        sample_book_data: dict,
    ):
        """Test searching books by title."""
        await client.post("/api/v1/books/", json=sample_book_data)
        
        response = await client.get(
            "/api/v1/books/",
            params={"title": "Clean"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) >= 1
        assert "Clean" in data["items"][0]["title"]
    
    async def test_create_book_invalid_year(self, client: AsyncClient):
        """Test creating a book with invalid year."""
        invalid_data = {
            "title": "Future Book",
            "author": "Unknown",
            "year": 3000,  # Invalid future year
            "genre": "Sci-Fi",
            "pages": 100,
        }
        
        response = await client.post(
            "/api/v1/books/",
            json=invalid_data,
        )
        
        # Pydantic validation should catch this
        assert response.status_code == 422

