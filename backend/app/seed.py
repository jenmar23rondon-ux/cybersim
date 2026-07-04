"""Idempotent demo-data seeding.

On first startup (empty DB) this inserts one finished sample attack run so the
dashboard's history isn't empty during a demo. It's a no-op if any run already
exists, so restarts never duplicate it.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from .ai_explainer import KNOWLEDGE_BASE
from .database import SessionLocal
from .models import AttackRun


async def seed_demo_data() -> None:
    async with SessionLocal() as s:
        count = (await s.execute(select(func.count(AttackRun.id)))).scalar_one()
        if count and count > 0:
            return  # already has data — do nothing

        kb = KNOWLEDGE_BASE["sql_injection"]
        now = datetime.now(timezone.utc)
        demo = AttackRun(
            correlation_id=uuid.uuid4().hex[:16],
            campaign_id=None,
            attack_type="sql_injection",
            target="vuln-node-api",
            status="success",
            params={"port": 3001},
            logs=[
                {"level": "info", "message": "[DEMO] Sample historical run", "progress": 0},
                {"level": "success", "message": "[DEMO] Injection succeeded", "progress": 100},
            ],
            result={"success": True, "working_payloads": [
                {"label": "auth bypass", "payload": "admin' OR '1'='1", "rows": 3}]},
            ai_explanation={
                "generated_by": "seed",
                "title": kb["title"],
                "what_it_does": kb["what"],
                "vulnerability_exploited": kb["vulnerability"],
                "remediation": kb["fix"],
                "mitre": kb["mitre"],
            },
            started_at=now - timedelta(minutes=5),
            finished_at=now - timedelta(minutes=5, seconds=-8),
        )
        s.add(demo)
        await s.commit()
