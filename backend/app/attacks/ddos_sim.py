"""DDoS simulation (low rate, bounded).

Sends a small, capped number of concurrent requests to a lab target and measures
how response latency changes under load. This is a CONCEPT DEMONSTRATION — the
request count and concurrency are hard-capped so it never becomes an actual flood.
"""

from __future__ import annotations

import asyncio
import statistics
import time

import httpx

from .base import AttackModuleBase, Emit, register

# Hard safety caps — cannot be exceeded regardless of params.
MAX_REQUESTS = 200
MAX_CONCURRENCY = 20


@register
class DdosSim(AttackModuleBase):
    id = "ddos_sim"
    name = "DDoS Simulation (low rate)"
    description = "Bounded concurrent load test to show latency degradation. Capped, not a flood."
    default_target = "vuln-node-api"
    mitre = "T1498"
    params_schema = {
        "port": {"type": "int", "default": 3001},
        "path": {"type": "string", "default": "/health"},
        "requests": {"type": "int", "default": 100, "max": MAX_REQUESTS},
        "concurrency": {"type": "int", "default": 10, "max": MAX_CONCURRENCY},
    }

    async def run(self, target: str, params: dict, emit: Emit) -> dict:
        port = int(params.get("port", 3001))
        path = str(params.get("path", "/health"))
        n = min(int(params.get("requests", 100)), MAX_REQUESTS)
        concurrency = min(int(params.get("concurrency", 10)), MAX_CONCURRENCY)
        url = f"http://{target}:{port}{path}"

        await emit("info", f"Baseline latency probe on {url}", 5)
        latencies: list[float] = []
        errors = 0
        done = 0

        async with httpx.AsyncClient(timeout=10) as client:
            # single baseline
            try:
                t0 = time.perf_counter()
                await client.get(url)
                baseline = (time.perf_counter() - t0) * 1000
                await emit("info", f"Baseline: {baseline:.1f} ms", 10)
            except Exception as exc:
                await emit("error", f"Baseline failed: {exc}", 10)
                baseline = None

            sem = asyncio.Semaphore(concurrency)
            lock = asyncio.Lock()

            async def one(idx: int):
                nonlocal errors, done
                async with sem:
                    try:
                        t0 = time.perf_counter()
                        await client.get(url)
                        dt = (time.perf_counter() - t0) * 1000
                        latencies.append(dt)
                    except Exception:
                        errors += 1
                    finally:
                        async with lock:
                            done += 1
                            if done % max(1, n // 10) == 0:
                                prog = int(10 + (done / n) * 85)
                                avg = statistics.mean(latencies) if latencies else 0
                                await emit("info",
                                           f"{done}/{n} sent — avg {avg:.1f} ms, {errors} errors",
                                           prog, {"sent": done, "avg_ms": round(avg, 1)})

            await emit("warn", f"Sending {n} requests @ concurrency {concurrency} (capped).", 12)
            await asyncio.gather(*(one(i) for i in range(n)))

        avg = statistics.mean(latencies) if latencies else 0
        p95 = (statistics.quantiles(latencies, n=20)[-1] if len(latencies) >= 20 else avg)
        degraded = baseline is not None and avg > baseline * 2
        await emit("success",
                   f"Complete: {len(latencies)} ok, {errors} errors, avg {avg:.1f} ms, p95 {p95:.1f} ms.",
                   100, {"avg_ms": round(avg, 1), "p95_ms": round(p95, 1), "errors": errors})
        return {
            "success": len(latencies) > 0,
            "requests_sent": n,
            "concurrency": concurrency,
            "baseline_ms": round(baseline, 1) if baseline else None,
            "avg_ms": round(avg, 1),
            "p95_ms": round(p95, 1),
            "errors": errors,
            "latency_degraded": degraded,
        }
