"""Attack engine — orchestrates a single attack run.

Split into two phases so the API can validate + return a correlation id
synchronously, then stream results in the background:

  * :func:`create_run`  — runs the safety guard, creates the DB row, returns the
    correlation id. Raises ``TargetNotAllowed`` / ``ValueError`` for the caller
    to surface as HTTP errors.
  * :func:`execute_run` — the background coroutine that actually runs the module,
    streaming/persisting/forwarding every event and finishing with the AI
    explanation.

Both accept an optional ``campaign_id`` so guided-scenario campaigns can group
runs and mirror their events into a shared campaign room.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import update

from .ai_explainer import explain_attack
from .attacks import REGISTRY
from .database import SessionLocal
from .models import AttackRun
from .safety import TargetNotAllowed, assert_target_allowed
from .securewatch import forward_event
from .ws_manager import manager


async def create_run(attack_type: str, target: str, params: dict,
                     campaign_id: str | None = None) -> tuple[str, int]:
    module = REGISTRY.get(attack_type)
    if module is None:
        raise ValueError(f"Unknown attack type: {attack_type}")

    # SAFETY: reject any non-local target before a row is even created.
    safe_target = assert_target_allowed(target)
    correlation_id = uuid.uuid4().hex[:16]

    async with SessionLocal() as s:
        run = AttackRun(
            correlation_id=correlation_id,
            campaign_id=campaign_id,
            attack_type=attack_type,
            target=safe_target,
            status="running",
            params=params,
            logs=[],
            result={},
        )
        s.add(run)
        await s.commit()
        return correlation_id, run.id


def _make_emitter(correlation_id: str, attack_type: str, run_id: int,
                  extra_rooms: list[str] | None = None):
    rooms = [correlation_id, *(extra_rooms or [])]

    async def emit(level: str, message: str, progress: int = 0, data: dict | None = None):
        event = {
            "correlation_id": correlation_id,
            "attack_type": attack_type,
            "level": level,
            "message": message,
            "progress": progress,
            "data": data or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        # Stream to the run room + any campaign room (+ global via manager).
        for room in rooms:
            await manager.broadcast(room, event)
        await forward_event(event)
        async with SessionLocal() as s:
            obj = await s.get(AttackRun, run_id)
            if obj is not None:
                obj.logs = (obj.logs or []) + [event]
                await s.commit()

    return emit


async def execute_run(attack_type: str, target: str, params: dict,
                      correlation_id: str, run_id: int,
                      extra_rooms: list[str] | None = None) -> dict:
    """Run a module to completion. Returns ``{status, result, explanation}``."""
    module = REGISTRY[attack_type]
    emit = _make_emitter(correlation_id, attack_type, run_id, extra_rooms)

    await emit("info", f"Launching {module.name} against {target}", 0,
               {"mitre": module.mitre})

    try:
        result = await module.run(target, params, emit)
        status = "success" if result.get("success") else "failed"
    except TargetNotAllowed as exc:
        await emit("error", f"Blocked by safety guard: {exc}", 100)
        result, status = {"success": False, "error": str(exc)}, "failed"
    except Exception as exc:
        await emit("error", f"Attack crashed: {exc}", 100)
        result, status = {"success": False, "error": str(exc)}, "failed"

    await emit("info", "Generating AI explanation ...", 100)
    explanation = await explain_attack(attack_type, target, result)

    async with SessionLocal() as s:
        await s.execute(
            update(AttackRun).where(AttackRun.id == run_id).values(
                status=status, result=result, ai_explanation=explanation,
                finished_at=datetime.now(timezone.utc),
            )
        )
        await s.commit()

    await emit("success" if status == "success" else "warn",
               f"Run finished: {status.upper()}", 100,
               {"final": True, "status": status, "explanation": explanation})
    return {"status": status, "result": result, "explanation": explanation,
            "correlation_id": correlation_id}
