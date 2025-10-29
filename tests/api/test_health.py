import pytest
import httpx


@pytest.mark.asyncio
async def test_health_check():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get("/healthz")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_db_health():
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        response = await client.get("/health/db")
        assert response.status_code == 200
        data = response.json()
        assert "oracle" in data
        assert "postgres" in data
        assert "mongo" in data

