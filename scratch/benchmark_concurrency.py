"""
NutriGuide AI - Concurrency & Performance Benchmark Harness
Measures RPS, Median (p50), and p95 latency under concurrency levels: 1, 5, 10, 25 users.
"""
import asyncio
import time
import os
import statistics
import httpx

BASE_URL = "http://127.0.0.1:8000"

# Load valid validation pizza image for confident classification benchmarking
PIZZA_PATH = "backend/datasets/food20/val/pizza/pizza_00000.jpg"
with open(PIZZA_PATH, "rb") as f:
    SAMPLE_IMAGE = f.read()


async def run_benchmark(endpoint_type: str, concurrency: int, total_requests: int):
    latencies = []
    errors = 0
    start_time = time.time()

    async with httpx.AsyncClient(base_url=BASE_URL, timeout=30.0) as client:
        sem = asyncio.Semaphore(concurrency)

        async def worker():
            nonlocal errors
            async with sem:
                t0 = time.time()
                try:
                    if endpoint_type == "read_health":
                        r = await client.get("/api/health")
                    elif endpoint_type == "categories_api":
                        r = await client.get("/api/categories")
                    elif endpoint_type == "analyze_confident":
                        files = {"file": ("pizza.jpg", SAMPLE_IMAGE, "image/jpeg")}
                        r = await client.post("/api/analyze", files=files)
                    else:
                        raise ValueError(f"Unknown: {endpoint_type}")

                    t1 = time.time()
                    if r.status_code == 200:
                        latencies.append((t1 - t0) * 1000)
                    else:
                        errors += 1
                except Exception:
                    errors += 1

        tasks = [worker() for _ in range(total_requests)]
        await asyncio.gather(*tasks)

    duration = time.time() - start_time
    rps = total_requests / duration if duration > 0 else 0
    p50 = statistics.median(latencies) if latencies else 0
    p95 = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else (max(latencies) if latencies else 0)
    error_rate = (errors / total_requests) * 100

    return {
        "endpoint": endpoint_type,
        "concurrency": concurrency,
        "total_requests": total_requests,
        "duration_sec": round(duration, 2),
        "rps": round(rps, 2),
        "median_ms": round(p50, 2),
        "p95_ms": round(p95, 2),
        "error_rate_pct": round(error_rate, 2),
        "successful": len(latencies),
        "errors": errors,
    }


async def main():
    endpoints = ["read_health", "categories_api", "analyze_confident"]
    concurrency_levels = [1, 5, 10, 25]

    print("=" * 80)
    print("NUTRIGUIDE AI CONCURRENCY & STRESS BENCHMARK RESULTS")
    print("=" * 80)
    print(f"{'Endpoint':<18} | {'Conc':<4} | {'Total':<5} | {'RPS':<7} | {'Median(ms)':<10} | {'p95(ms)':<9} | {'Err%':<5}")
    print("-" * 80)

    for ep in endpoints:
        for c in concurrency_levels:
            total = 10 if c <= 5 else 20
            res = await run_benchmark(ep, c, total)
            print(f"{res['endpoint']:<18} | {res['concurrency']:<4} | {res['total_requests']:<5} | {res['rps']:<7} | {res['median_ms']:<10} | {res['p95_ms']:<9} | {res['error_rate_pct']:<5}", flush=True)
        print("-" * 80, flush=True)


if __name__ == "__main__":
    asyncio.run(main())
