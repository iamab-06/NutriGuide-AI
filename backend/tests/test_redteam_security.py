"""
NutriGuide AI - Red Team Security & Robustness Automated Test Suite
Permanently verifies fixes for input validation, file upload security,
dimension guards, memory leak prevention, RAG boundaries, and error sanitization.
"""
import io
import pytest
from PIL import Image
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.rag.rag_service import get_rag_service
from app.services.nutrition import _extract_nutrients
from app.services.openfoodfacts import get_product_by_barcode


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
async def test_file_upload_html_disguised_rejected():
    """Verify that HTML disguised with image/jpeg Content-Type is rejected with 400 and clean error."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        html_payload = b"<html><body><script>alert('XSS')</script></body></html>"
        files = {"file": ("exploit.jpg", html_payload, "image/jpeg")}
        resp = await ac.post("/api/analyze", files=files)
        assert resp.status_code == 400
        detail = resp.json()["detail"]
        assert "Invalid image file or unsupported image format." in detail
        # Verify no internal Python memory address leaks
        assert "<_io.BytesIO" not in detail
        assert "0x" not in detail


@pytest.mark.asyncio
async def test_file_upload_exe_disguised_rejected():
    """Verify executable binary disguised as PNG is rejected."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        exe_payload = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00"
        files = {"file": ("payload.png", exe_payload, "image/png")}
        resp = await ac.post("/api/analyze", files=files)
        assert resp.status_code == 400
        assert "Invalid image file or unsupported image format." in resp.json()["detail"]


@pytest.mark.asyncio
async def test_file_upload_zero_byte_rejected():
    """Verify empty file is rejected with clean 400."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        files = {"file": ("empty.jpg", b"", "image/jpeg")}
        resp = await ac.post("/api/analyze", files=files)
        assert resp.status_code == 400
        assert "Empty file uploaded." in resp.json()["detail"]


@pytest.mark.asyncio
async def test_file_upload_deceptive_extension_rejected():
    """Verify non-image file extension is rejected."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        files = {"file": ("malicious.php", b"\xff\xd8\xff\xe0test", "image/jpeg")}
        resp = await ac.post("/api/analyze", files=files)
        assert resp.status_code == 400
        assert "Unsupported file extension: .php" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_file_upload_oversized_dimensions_rejected():
    """Verify 5000x5000 dimension pixel bomb is rejected with 400."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        img = Image.new("RGB", (5000, 5000), color="blue")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=40)
        files = {"file": ("giant.jpg", buf.getvalue(), "image/jpeg")}
        resp = await ac.post("/api/analyze", files=files)
        assert resp.status_code == 400
        assert "exceed maximum allowed limit" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_file_upload_corrupted_jpeg_rejected():
    """Verify truncated corrupted JPEG is rejected with clean error."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        corrupted = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01"
        files = {"file": ("corrupt.jpg", corrupted, "image/jpeg")}
        resp = await ac.post("/api/analyze", files=files)
        assert resp.status_code == 400
        detail = resp.json()["detail"]
        assert "Invalid image file or unsupported image format." in detail
        assert "<_io.BytesIO" not in detail


@pytest.mark.asyncio
async def test_search_nutrition_query_length_boundary():
    """Verify nutrition search rejects queries longer than 100 characters."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/nutrition/search", params={"q": "A" * 101})
        assert resp.status_code == 422


@pytest.mark.asyncio
async def test_nutrition_food_name_length_boundary():
    """Verify nutrition food_name rejects oversized inputs."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/api/nutrition/{'A' * 150}")
        assert resp.status_code == 400
        assert "Food name must be between 1 and 100 characters." in resp.json()["detail"]


@pytest.mark.asyncio
async def test_barcode_length_and_type_boundary():
    """Verify barcode rejects non-numeric, too short, or excessive length values."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # SQL injection attempt
        r1 = await ac.get("/api/products/barcode/12345' OR '1'='1")
        assert r1.status_code == 400

        # Too short (< 6 digits)
        r2 = await ac.get("/api/products/barcode/123")
        assert r2.status_code == 400

        # Excessive digits (> 32)
        r3 = await ac.get(f"/api/products/barcode/{'9' * 50}")
        assert r3.status_code == 400


@pytest.mark.asyncio
async def test_products_search_length_boundary():
    """Verify product search rejects queries longer than 100 characters."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/api/products/search", params={"q": "A" * 150})
        assert resp.status_code == 422


@pytest.mark.asyncio
async def test_compare_endpoint_bounds():
    """Verify compare endpoint rejects food names longer than 100 chars."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/compare", json={"food1": "A" * 150, "food2": "pizza"})
        assert resp.status_code == 422


@pytest.mark.asyncio
async def test_compare_endpoint_identical_food():
    """Verify comparing identical food returns immediate equality without duplicate lookup."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/compare", json={"food1": "pizza", "food2": "pizza"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["food1"]["food_name"] == data["food2"]["food_name"]
        assert "identical" in data["comparison_notes"].lower()


@pytest.mark.asyncio
async def test_chat_message_length_boundary():
    """Verify chat message length > 2000 chars is rejected."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/api/chat", json={"message": "X" * 2001})
        assert resp.status_code == 422


@pytest.mark.asyncio
async def test_chat_history_length_boundary():
    """Verify chat history > 20 items is rejected."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        history = [{"role": "user", "content": f"msg {i}"} for i in range(25)]
        resp = await ac.post("/api/chat", json={"message": "hello", "history": history})
        assert resp.status_code == 422


def test_rag_retrieve_boundary_conditions():
    """Verify RAG handles empty strings, zero/negative k, and excessive k safely."""
    rag = get_rag_service()

    # Empty query
    assert rag.retrieve("", k=3) == []
    assert rag.retrieve("   ", k=3) == []

    # k=0 or negative k clamped safely to >= 1
    res = rag.retrieve("protein", k=0)
    assert len(res) >= 1

    res_neg = rag.retrieve("protein", k=-5)
    assert len(res_neg) >= 1

    # k > total documents clamped safely
    res_large = rag.retrieve("calories", k=999)
    assert len(res_large) <= len(rag.documents)


def test_nutrition_nan_and_negative_sanitization():
    """Verify that _extract_nutrients clamps negative values and filters NaN/Inf."""
    mock_food = {
        "foodNutrients": [
            {"nutrientId": 1008, "amount": -50.0},        # Negative calories
            {"nutrientId": 1003, "amount": float("nan")}, # NaN protein
            {"nutrientId": 1005, "amount": float("inf")}, # Inf carbs
            {"nutrientId": 1004, "amount": 12.5},         # Valid fat
        ]
    }
    nutrients = _extract_nutrients(mock_food)
    assert nutrients["calories"] == 0.0  # Clamped to 0.0
    assert nutrients["protein"] is None  # Filtered out
    assert nutrients["carbohydrates"] is None  # Filtered out
    assert nutrients["fat"] == 12.5      # Preserved
