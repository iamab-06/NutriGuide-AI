"""
NutriGuide AI - Red Team Vulnerability & Failure Probe Suite
"""
import io
import json
import httpx
from PIL import Image

BASE_URL = "http://127.0.0.1:8000"

def test_file_upload_security():
    print("\n--- [TEST SUITE 1] File Upload Security Probes ---")
    client = httpx.Client(base_url=BASE_URL, timeout=15.0)

    # 1.1: HTML payload disguised as JPEG
    html_content = b"<html><body><script>alert('XSS')</script></body></html>"
    files = {"file": ("malicious.jpg", html_content, "image/jpeg")}
    r = client.post("/api/analyze", files=files)
    print(f"Probe 1.1 (HTML with image/jpeg): Status {r.status_code}, Detail: {r.text[:120]}")

    # 1.2: Executable bytes disguised as PNG
    exe_content = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00This is a fake PE executable"
    files = {"file": ("malware.png", exe_content, "image/png")}
    r = client.post("/api/analyze", files=files)
    print(f"Probe 1.2 (EXE with image/png): Status {r.status_code}, Detail: {r.text[:120]}")

    # 1.3: Zero-byte file
    files = {"file": ("empty.jpg", b"", "image/jpeg")}
    r = client.post("/api/analyze", files=files)
    print(f"Probe 1.3 (Zero-byte file): Status {r.status_code}, Detail: {r.text[:120]}")

    # 1.4: Oversized file (>10MB)
    huge_bytes = b"0" * (11 * 1024 * 1024)
    files = {"file": ("huge.jpg", huge_bytes, "image/jpeg")}
    r = client.post("/api/analyze", files=files)
    print(f"Probe 1.4 (11MB file): Status {r.status_code}, Detail: {r.text[:120]}")

    # 1.5: Giant dimensions image (pixel flood / potential DOS)
    # Generate 5000x5000 image
    try:
        img = Image.new("RGB", (5000, 5000), color="red")
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=50)
        giant_jpeg = buf.getvalue()
        files = {"file": ("giant.jpg", giant_jpeg, "image/jpeg")}
        r = client.post("/api/analyze", files=files)
        print(f"Probe 1.5 (5000x5000 px image): Status {r.status_code}, Length: {len(giant_jpeg)} bytes, Detail: {r.text[:120]}")
    except Exception as e:
        print(f"Probe 1.5 error generating: {e}")

    # 1.6: Truncated corrupted JPEG
    corrupted = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb"
    files = {"file": ("corrupted.jpg", corrupted, "image/jpeg")}
    r = client.post("/api/analyze", files=files)
    print(f"Probe 1.6 (Corrupted JPEG): Status {r.status_code}, Detail: {r.text[:120]}")


def test_input_validation():
    print("\n--- [TEST SUITE 2] Input Validation & Bounds Probes ---")
    client = httpx.Client(base_url=BASE_URL, timeout=15.0)

    # 2.1: Giant query in nutrition search
    giant_q = "A" * 5000
    r = client.get("/api/nutrition/search", params={"q": giant_q})
    print(f"Probe 2.1 (5000-char search query): Status {r.status_code}, Detail: {r.text[:120]}")

    # 2.2: Giant barcode
    giant_barcode = "9" * 5000
    r = client.get(f"/api/products/barcode/{giant_barcode}")
    print(f"Probe 2.2 (5000-digit barcode): Status {r.status_code}, Detail: {r.text[:120]}")

    # 2.3: SQL-injection string in barcode
    sqli_barcode = "12345' OR '1'='1"
    r = client.get(f"/api/products/barcode/{sqli_barcode}")
    print(f"Probe 2.3 (SQLi in barcode): Status {r.status_code}, Detail: {r.text[:120]}")

    # 2.4: Path traversal in nutrition food_name
    r = client.get("/api/nutrition/..%2F..%2Fetc%2Fpasswd")
    print(f"Probe 2.4 (Path traversal in nutrition): Status {r.status_code}, Detail: {r.text[:120]}")

    # 2.5: Compare endpoint with 5000-char food names
    r = client.post("/api/compare", json={"food1": "A" * 5000, "food2": "B" * 5000})
    print(f"Probe 2.5 (5000-char compare): Status {r.status_code}, Detail: {r.text[:120]}")

    # 2.6: Compare identical food
    r = client.post("/api/compare", json={"food1": "pizza", "food2": "pizza"})
    print(f"Probe 2.6 (Compare identical food): Status {r.status_code}, Detail: {r.text[:120]}")

    # 2.7: Chat with 50,000 char message
    r = client.post("/api/chat", json={"message": "X" * 50000})
    print(f"Probe 2.7 (50,000-char chat message): Status {r.status_code}, Detail: {r.text[:120]}")


def test_cors_and_headers():
    print("\n--- [TEST SUITE 3] CORS & Method Security Probes ---")
    client = httpx.Client(base_url=BASE_URL, timeout=15.0)

    # 3.1: Untrusted origin
    headers = {"Origin": "https://malicious-attacker-site.com"}
    r = client.get("/api/health", headers=headers)
    cors_header = r.headers.get("access-control-allow-origin")
    print(f"Probe 3.1 (Untrusted Origin CORS): Status {r.status_code}, Allow-Origin: {cors_header}")

    # 3.2: Allowed local origin
    headers = {"Origin": "http://localhost:5173"}
    r = client.get("/api/health", headers=headers)
    cors_header = r.headers.get("access-control-allow-origin")
    print(f"Probe 3.2 (Trusted Origin CORS): Status {r.status_code}, Allow-Origin: {cors_header}")


if __name__ == "__main__":
    test_file_upload_security()
    test_input_validation()
    test_cors_and_headers()
