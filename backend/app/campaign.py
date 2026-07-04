"""Campaign engine — runs a guided scenario as a chained sequence of attacks.

A campaign gets its own ``campaign_id`` which doubles as a WebSocket room and a
SIEM correlation trail. Every step is a normal attack run (so it shows up in
history and has its own AI explanation and per-run report), but its events are
also mirrored into the campaign room and its result is aggregated into a
consolidated campaign summary + PDF report.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import update

from .database import SessionLocal
from .engine import create_run, execute_run
from .models import Campaign
from .safety import TargetNotAllowed, assert_target_allowed
from .scenarios import get_scenario
from .securewatch import forward_event
from .ws_manager import manager


async def create_campaign(scenario_id: str) -> tuple[str, int]:
    scenario = get_scenario(scenario_id)
    if scenario is None:
        raise ValueError(f"Unknown scenario: {scenario_id}")

    # SAFETY: validate every step's target up front so a bad scenario can't
    # start and only fail halfway through.
    for step in scenario["steps"]:
        assert_target_allowed(step["target"])

    campaign_id = uuid.uuid4().hex[:16]
    steps_meta = [
        {
            "attack_type": st["attack_type"],
            "target": st["target"],
            "narrative": st["narrative"],
            "correlation_id": None,
            "status": "pending",
        }
        for st in scenario["steps"]
    ]

    async with SessionLocal() as s:
        campaign = Campaign(
            campaign_id=campaign_id,
            scenario_id=scenario_id,
            name=scenario["name"],
            status="running",
            steps=steps_meta,
            summary={},
        )
        s.add(campaign)
        await s.commit()
        return campaign_id, campaign.id


async def _emit_campaign(campaign_id: str, level: str, message: str,
                         progress: int, data: dict | None = None) -> None:
    event = {
        "correlation_id": campaign_id,
        "attack_type": "campaign",
        "level": level,
        "message": message,
        "progress": progress,
        "data": data or {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await manager.broadcast(campaign_id, event)
    await forward_event(event)


async def execute_campaign(scenario_id: str, campaign_id: str, row_id: int) -> None:
    scenario = get_scenario(scenario_id)
    assert scenario is not None
    steps = scenario["steps"]
    total = len(steps)
    results: list[dict] = []

    await _emit_campaign(campaign_id, "info",
                         f"Starting campaign '{scenario['name']}' ({total} steps)", 0,
                         {"scenario_id": scenario_id})

    async with SessionLocal() as s:
        campaign = await s.get(Campaign, row_id)
        steps_meta = list(campaign.steps or [])

    for i, step in enumerate(steps):
        base = int((i / total) * 100)
        await _emit_campaign(campaign_id, "info",
                             f"Step {i + 1}/{total}: {step['narrative']}", base,
                             {"step": i + 1, "attack_type": step["attack_type"],
                              "target": step["target"]})
        try:
            correlation_id, run_id = await create_run(
                step["attack_type"], step["target"], step.get("params", {}),
                campaign_id=campaign_id,
            )
        except (TargetNotAllowed, ValueError) as exc:
            await _emit_campaign(campaign_id, "error",
                                 f"Step {i + 1} blocked: {exc}", base)
            steps_meta[i].update(status="failed", correlation_id=None)
            results.append({"attack_type": step["attack_type"], "status": "failed",
                            "error": str(exc)})
            continue

        steps_meta[i].update(status="running", correlation_id=correlation_id)
        await _persist_steps(row_id, steps_meta)

        outcome = await execute_run(
            step["attack_type"], step["target"], step.get("params", {}),
            correlation_id, run_id, extra_rooms=[campaign_id],
        )
        steps_meta[i].update(status=outcome["status"])
        await _persist_steps(row_id, steps_meta)
        results.append({
            "attack_type": step["attack_type"],
            "target": step["target"],
            "status": outcome["status"],
            "correlation_id": correlation_id,
            "result": outcome["result"],
        })

    succeeded = sum(1 for r in results if r["status"] == "success")
    overall = "success" if succeeded > 0 else "failed"
    summary = {
        "scenario": scenario["name"],
        "total_steps": total,
        "succeeded": succeeded,
        "failed": total - succeeded,
        "steps": results,
    }

    async with SessionLocal() as s:
        await s.execute(
            update(Campaign).where(Campaign.id == row_id).values(
                status=overall, summary=summary, steps=steps_meta,
                finished_at=datetime.now(timezone.utc),
            )
        )
        await s.commit()

    await _emit_campaign(campaign_id, "success" if overall == "success" else "warn",
                         f"Campaign finished: {succeeded}/{total} step(s) exploited.", 100,
                         {"final": True, "status": overall, "summary": summary})


async def _persist_steps(row_id: int, steps_meta: list) -> None:
    async with SessionLocal() as s:
        await s.execute(update(Campaign).where(Campaign.id == row_id).values(steps=steps_meta))
        await s.commit()
