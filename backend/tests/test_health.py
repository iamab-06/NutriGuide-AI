"""
Tests for NutriGuide AI Health and Categories API
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.categories import SUPPORTED_CATEGORIES, CATEGORY_DISPLAY_NAMES


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "NutriGuide AI"
    assert "version" in data


@pytest.mark.asyncio
async def test_categories_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/categories")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 20
    assert len(data["categories"]) == 20
    assert "pizza" in data["categories"]
    assert "hamburger" in data["categories"]
    assert data["display_names"]["pizza"] == "Pizza"
    assert data["total_food101_count"] == 101
    assert "apple_pie" in data["all_categories"]


@pytest.mark.asyncio
async def test_cache_stats_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/cache/stats")
    assert response.status_code == 200
    data = response.json()
    assert "nutrition_cache" in data
    assert "search_cache" in data
    assert "product_cache" in data
    assert "hit_rate_pct" in data["nutrition_cache"]
