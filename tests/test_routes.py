"""Tests for API routes."""

import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

import storage


@pytest.fixture(autouse=True)
def clean_db():
    """Clean database before and after each test."""
    if os.path.exists("urls.json"):
        with open("urls.json", "w") as f:
            f.write("{}")
    yield
    if os.path.exists("urls.json"):
        with open("urls.json", "w") as f:
            f.write("{}")


@ pytest_asyncio.fixture
async def client():
    from main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestEncurtarRoute:
    @pytest.mark.asyncio
    async def test_create_short_url_success(self, client):
        response = await client.post("/encurtar", json={"url": "https://example.com/very/long/path"})
        assert response.status_code == 201
        data = response.json()
        assert "codigo" in data
        assert "url_curta" in data
        assert len(data["codigo"]) == 6
        assert data["url_curta"].startswith("http://localhost:8000/")

    @pytest.mark.asyncio
    async def test_invalid_url_returns_422(self, client):
        response = await client.post("/encurtar", json={"url": "not-a-url"})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_url_returns_422(self, client):
        response = await client.post("/encurtar", json={})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_ftp_url_returns_422(self, client):
        response = await client.post("/encurtar", json={"url": "ftp://example.com"})
        assert response.status_code == 422


class TestRedirecionarRoute:
    @pytest.mark.asyncio
    async def test_redirect_existing_code(self, client):
        storage.save_url("abc123", "https://example.com")
        response = await client.get("/abc123", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "https://example.com"

    @pytest.mark.asyncio
    async def test_404_for_nonexistent_code(self, client):
        response = await client.get("/nonexistent")
        assert response.status_code == 404
        assert "Código não encontrado" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_redirect_preserves_query_params(self, client):
        storage.save_url("xyz789", "https://example.com?foo=bar")
        response = await client.get("/xyz789", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "https://example.com?foo=bar"


class TestHealthRoute:
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}