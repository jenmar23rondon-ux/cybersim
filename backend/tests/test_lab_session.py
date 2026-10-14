import unittest
from unittest.mock import patch

from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.database import Base
from app.main import app
from app.models import AttackRun, Campaign


class LabSessionTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        self.patches = [patch("app.main.SessionLocal", self.sessions), patch("app.defense.SessionLocal", self.sessions)]
        for item in self.patches:
            item.start()
        self.client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")

    async def asyncTearDown(self):
        await self.client.aclose()
        for item in self.patches:
            item.stop()
        await self.engine.dispose()

    async def add_run(self, cid, campaign_id=None, **kwargs):
        async with self.sessions() as session:
            session.add(AttackRun(correlation_id=cid, campaign_id=campaign_id, attack_type="idor_audit",
                                  target="lab", status="failed", result={"success": False}, **kwargs))
            await session.commit()

    async def test_reset_boundary_empties_view_preserves_reports_and_excludes_old_campaign_steps(self):
        async with self.sessions() as session:
            session.add(Campaign(campaign_id="old", scenario_id="test", name="Existing campaign"))
            await session.commit()
        await self.add_run("old-run", "old")
        self.assertEqual((await self.client.get("/api/metrics")).json()["total_runs"], 1)
        boundary = (await self.client.get("/api/lab/baseline")).json()
        for _ in range(2):
            self.assertEqual((await self.client.get("/api/attacks", params=boundary)).json(), [])
            metrics = (await self.client.get("/api/metrics", params=boundary)).json()
            self.assertEqual(metrics["total_runs"], 0)
            self.assertEqual(metrics["campaigns"], 0)
            self.assertEqual(metrics["average_risk_score"], 0)
        await self.add_run("late-old-step", "old")
        self.assertEqual((await self.client.get("/api/attacks", params=boundary)).json(), [])
        await self.add_run("new-run")
        visible = (await self.client.get("/api/attacks", params=boundary)).json()
        self.assertEqual([run["correlation_id"] for run in visible], ["new-run"])
        self.assertEqual((await self.client.get("/api/metrics", params=boundary)).json()["total_runs"], 1)
        self.assertEqual((await self.client.get("/api/attacks/old-run/report")).status_code, 200)
        self.assertEqual(len((await self.client.get("/api/attacks")).json()), 3)

    async def test_empty_database_and_invalid_boundary(self):
        self.assertEqual((await self.client.get("/api/lab/baseline")).json(), {"after_run_id": 0, "after_campaign_id": 0})
        for route in ["/api/metrics", "/api/attacks"]:
            self.assertEqual((await self.client.get(route, params={"after_run_id": -1})).status_code, 422)


if __name__ == "__main__":
    unittest.main()
