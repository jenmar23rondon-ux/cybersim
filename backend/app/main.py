"""CyberSim FastAPI backend.

Exposes REST endpoints to list modules, launch attacks, browse history, and
download PDF reports, plus a WebSocket for real-time attack logs.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
import httpx
from sqlalchemy import select

from .attacks import REGISTRY
from .campaign import create_campaign, execute_campaign
from .database import SessionLocal, init_db
from .defense import build_metrics, enrich_run, list_playbooks, playbook_for
from .engine import create_run, execute_run
from .models import AttackRun, Campaign
from .report import build_campaign_report, build_report
from .remediation import guide_for, list_guides
from .safety import TargetNotAllowed, assert_target_allowed, describe_target
from .schemas import AttackRequest, CampaignRequest, TargetProbeRequest
from .scenarios import list_scenarios
from .seed import seed_demo_data
from .ws_manager import manager

LOCAL_PORT_TARGETS = {
    3001: "vuln-node-api",
    3002: "juice-shop",
    3003: "mini-vuln-app",
    4280: "dvwa",
    8000: "backend",
    2222: "weak-ssh",
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Retry DB init (Postgres may still be warming up).
    for attempt in range(10):
        try:
            await init_db()
            break
        except Exception:
            await asyncio.sleep(2)
    # Seed a demo run so the dashboard isn't empty on first launch (idempotent).
    try:
        await seed_demo_data()
    except Exception:
        pass
    yield


app = FastAPI(title="CyberSim API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # lab only
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "modules": list(REGISTRY.keys())}


@app.get("/api/modules")
async def list_modules():
    return [m.info() for m in REGISTRY.values()]


@app.get("/api/defense/playbooks")
async def defense_playbooks():
    return await list_playbooks()


@app.get("/api/defense/playbooks/{attack_type}")
async def defense_playbook(attack_type: str):
    if attack_type not in REGISTRY:
        raise HTTPException(404, f"Unknown attack type '{attack_type}'")
    return playbook_for(attack_type)


@app.get("/api/metrics")
async def metrics():
    return await build_metrics()


@app.get("/api/remediation/guides")
async def remediation_guides():
    return list_guides()


@app.get("/api/remediation/guides/{attack_type}")
async def remediation_guide(attack_type: str):
    return guide_for(attack_type)


@app.post("/api/targets/probe")
async def probe_target(req: TargetProbeRequest):
    details = describe_target(req.url)
    try:
        host = assert_target_allowed(req.url)
    except TargetNotAllowed as exc:
        raise HTTPException(403, {
            "message": str(exc),
            "details": details,
        })

    parsed = httpx.URL(req.url if "://" in req.url else f"http://{req.url}")
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    scheme = parsed.scheme or "http"
    path = req.path if req.path.startswith("/") else f"/{req.path}"
    probe_host = _docker_probe_host(host, port)
    attack_host = probe_host
    probe_url = f"{scheme}://{probe_host}:{port}{path}"

    try:
        async with httpx.AsyncClient(timeout=5, follow_redirects=True) as client:
            response = await client.get(probe_url)
    except Exception as exc:
        return {
            "ok": False,
            "host": host,
            "attack_host": attack_host,
            "probe_host": probe_host,
            "port": port,
            "scheme": scheme,
            "probe_url": probe_url,
            "details": details,
            "error": str(exc),
        }

    return {
        "ok": response.status_code < 500,
        "host": host,
        "attack_host": attack_host,
        "probe_host": probe_host,
        "port": port,
        "scheme": scheme,
        "probe_url": probe_url,
        "status_code": response.status_code,
        "content_type": response.headers.get("content-type", ""),
        "details": details,
    }


def _docker_probe_host(host: str, port: int) -> str:
    """Translate browser-local URLs into addresses reachable from containers."""
    if host in {"localhost", "127.0.0.1"}:
        return LOCAL_PORT_TARGETS.get(port, "host.docker.internal")
    return host


@app.post("/api/attacks")
async def launch_attack(req: AttackRequest):
    if req.attack_type not in REGISTRY:
        raise HTTPException(404, f"Unknown attack type '{req.attack_type}'")
    try:
        # Validate + create the run row synchronously so we can return the id
        # and reject bad targets (403) before any background work starts.
        correlation_id, run_id = await create_run(req.attack_type, req.target, req.params)
    except TargetNotAllowed as exc:
        raise HTTPException(403, str(exc))
    except ValueError as exc:
        raise HTTPException(400, str(exc))

    # Stream the actual attack in the background; client subscribes over WS.
    asyncio.create_task(
        execute_run(req.attack_type, req.target, req.params, correlation_id, run_id)
    )
    return {"correlation_id": correlation_id, "status": "started"}


@app.get("/api/attacks")
async def list_runs(limit: int = 50):
    async with SessionLocal() as s:
        rows = (await s.execute(
            select(AttackRun).order_by(AttackRun.id.desc()).limit(limit)
        )).scalars().all()
        return [enrich_run(r.to_dict()) for r in rows]


@app.get("/api/attacks/{correlation_id}")
async def get_run(correlation_id: str):
    async with SessionLocal() as s:
        row = (await s.execute(
            select(AttackRun).where(AttackRun.correlation_id == correlation_id)
        )).scalar_one_or_none()
        if row is None:
            raise HTTPException(404, "Run not found")
        return enrich_run(row.to_dict())


@app.get("/api/attacks/{correlation_id}/report")
async def download_report(correlation_id: str):
    async with SessionLocal() as s:
        row = (await s.execute(
            select(AttackRun).where(AttackRun.correlation_id == correlation_id)
        )).scalar_one_or_none()
        if row is None:
            raise HTTPException(404, "Run not found")
        pdf = build_report(row)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=cybersim-{correlation_id}.pdf"},
    )


# ---------------------------------------------------------------- Scenarios
@app.get("/api/scenarios")
async def get_scenarios():
    return list_scenarios()


@app.post("/api/campaigns")
async def launch_campaign(req: CampaignRequest):
    try:
        campaign_id, row_id = await create_campaign(req.scenario_id)
    except ValueError as exc:
        raise HTTPException(404, str(exc))
    except TargetNotAllowed as exc:
        raise HTTPException(403, str(exc))

    asyncio.create_task(execute_campaign(req.scenario_id, campaign_id, row_id))
    return {"campaign_id": campaign_id, "status": "started"}


@app.get("/api/campaigns")
async def list_campaigns(limit: int = 30):
    async with SessionLocal() as s:
        rows = (await s.execute(
            select(Campaign).order_by(Campaign.id.desc()).limit(limit)
        )).scalars().all()
        return [r.to_dict() for r in rows]


@app.get("/api/campaigns/{campaign_id}")
async def get_campaign(campaign_id: str):
    async with SessionLocal() as s:
        row = (await s.execute(
            select(Campaign).where(Campaign.campaign_id == campaign_id)
        )).scalar_one_or_none()
        if row is None:
            raise HTTPException(404, "Campaign not found")
        return row.to_dict()


@app.get("/api/campaigns/{campaign_id}/report")
async def download_campaign_report(campaign_id: str):
    async with SessionLocal() as s:
        campaign = (await s.execute(
            select(Campaign).where(Campaign.campaign_id == campaign_id)
        )).scalar_one_or_none()
        if campaign is None:
            raise HTTPException(404, "Campaign not found")
        runs = (await s.execute(
            select(AttackRun).where(AttackRun.campaign_id == campaign_id)
        )).scalars().all()
        pdf = build_campaign_report(campaign.to_dict(), [r.to_dict() for r in runs])
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=cybersim-campaign-{campaign_id}.pdf"},
    )


@app.websocket("/ws")
async def ws_global(ws: WebSocket):
    """Global live feed of every attack event (dashboard)."""
    await manager.connect(ws)
    try:
        while True:
            await ws.receive_text()  # keepalive / ignore inbound
    except WebSocketDisconnect:
        await manager.disconnect(ws)


@app.websocket("/ws/{correlation_id}")
async def ws_run(ws: WebSocket, correlation_id: str):
    """Live feed scoped to a single attack run."""
    await manager.connect(ws, correlation_id)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(ws, correlation_id)
