"""SecureWatch SIEM forwarder.

CyberSim ships every attack event to SecureWatch so the SIEM can raise its own
detection and we can visualize the correlation (same ``correlation_id`` on both
sides). If no webhook is configured this is a no-op, so the lab still runs
standalone.
"""

from __future__ import annotations

import httpx

from .config import get_settings


async def forward_event(event: dict) -> None:
    settings = get_settings()
    url = settings.securewatch_webhook_url
    if not url:
        return
    headers = {"Content-Type": "application/json"}
    if settings.securewatch_api_key:
        headers["Authorization"] = f"Bearer {settings.securewatch_api_key}"
    payload = {
        "source": "CyberSim",
        "event_type": "simulated_attack",
        **event,
    }
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(url, json=payload, headers=headers)
    except Exception:
        # SIEM forwarding must never break the simulation.
        pass
