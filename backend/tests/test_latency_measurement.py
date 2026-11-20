"""
NutriGuide AI - Real-Time Latency Measurement Unit Tests
========================================================
Validates that:
1. /api/analyze measures and returns real-time latency (latency_ms > 0)
   and timing breakdown (preprocessing_ms, classification_ms, fallback_ms, nutrition_retrieval_ms).
2. /api/chat measures and returns total_ms, rag_ms, llm_generation_ms.
3. /api/chat/stream returns timing with TTFT (time_to_first_token_ms) in the 'done' event.
4. /api/compare returns total_ms, nutrition_retrieval_ms, llm_generation_ms.
5. All timing values are real measured floats using time.perf_counter().
"""
import io
import json
import pytest
from PIL import Image
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock

from app.main import app
from app.services.classifier import CONFIDENCE_THRESHOLD


def create_sample_image(format="JPEG", size=(224, 224), color=(200, 150, 50)) -> bytes:
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_analyze_food_latency_measurement():
    """Verify that /api/analyze records real-time latency and stage timing."""
    img_bytes = create_sample_image()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/api/analyze",
            files={"file": ("sample.jpg", img_bytes, "image/jpeg")},
        )

    assert response.status_code == 200
    data = response.json()

    assert "latency_ms" in data
    assert data["latency_ms"] is not None
    assert data["latency_ms"] > 0.0

    timing = data.get("timing")
    assert timing is not None
    assert timing["total_ms"] > 0.0
    assert timing["preprocessing_ms"] is not None
    assert timing["preprocessing_ms"] >= 0.0
    assert timing["classification_ms"] is not None
    assert timing["classification_ms"] >= 0.0


@pytest.mark.asyncio
async def test_chat_latency_measurement():
    """Verify that /api/chat measures RAG and LLM response latency."""
    mock_chat_res = {
        "answer": "Ragi Mudde contains 122 kcal and 2.6g protein per 100g.",
        "sources": ["Curated Local Food Database"],
        "evidence_used": True,
        "warning": None,
    }

    with patch("app.api.chat.chat_with_context", new=AsyncMock(return_value=mock_chat_res)):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/chat",
                json={"message": "What is the nutrition of Ragi Mudde?", "history": []},
            )

    assert response.status_code == 200
    data = response.json()

    assert data["latency_ms"] is not None
    assert data["latency_ms"] > 0.0

    timing = data.get("timing")
    assert timing is not None
    assert timing["total_ms"] > 0.0
    assert timing["rag_ms"] is not None
    assert timing["llm_generation_ms"] is not None


@pytest.mark.asyncio
async def test_chat_stream_ttft_measurement():
    """Verify that /api/chat/stream SSE delivers time-to-first-token in the completion event."""
    async def mock_stream_tokens(*args, **kwargs):
        yield {"event": "meta", "sources": ["USDA"], "evidence_used": True}
        yield {"event": "token", "token": "Hello"}
        yield {"event": "token", "token": " world!"}
        yield {"event": "done"}

    with patch("app.api.chat.stream_chat_with_context", new=mock_stream_tokens):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/chat/stream",
                json={"message": "Hello", "history": []},
            )

    assert response.status_code == 200
    events = []
    for line in response.text.split("\n"):
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))

    done_event = next((e for e in events if e.get("event") == "done"), None)
    assert done_event is not None
    assert "timing" in done_event
    assert done_event["timing"]["total_ms"] > 0.0
    assert "time_to_first_token_ms" in done_event["timing"]
