import os
import sys
import asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from httpx import AsyncClient, ASGITransport
from app.main import app

async def main():
    img_path = r"C:\Users\abhij\.gemini\antigravity\brain\bd348a6d-253f-4d7d-a9c4-c0e81c72a89f\.user_uploaded\media_1794032194304_6ba6b98c.jpg"
    with open(img_path, "rb") as f:
        img_bytes = f.read()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.post("/api/analyze", files={"file": ("tiramisu.jpg", img_bytes, "image/jpeg")})
        print("Status code:", r.status_code)
        data = r.json()
        print("Requires confirmation:", data.get("requires_confirmation"))
        print("Classification:")
        print("  Predicted:", data["classification"]["predicted_class"])
        print("  Confidence:", data["classification"]["confidence"])
        print("  Is Confident:", data["classification"]["is_confident"])
        print("Top predictions:")
        for tp in data["classification"]["top_predictions"][:5]:
            print(f"  - {tp['display_name']}: {tp['confidence_pct']}")
        if data.get("gemini_fallback"):
            print("Vision fallback:")
            print("  Suggested:", data["gemini_fallback"].get("suggested_food"))
            print("  Confidence:", data["gemini_fallback"].get("confidence"))
            print("  Explanation:", data["gemini_fallback"].get("explanation"))

if __name__ == "__main__":
    asyncio.run(main())
