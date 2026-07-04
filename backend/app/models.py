from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class AttackRun(Base):
    __tablename__ = "attack_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    correlation_id: Mapped[str] = mapped_column(String(64), index=True)
    # When part of a guided scenario / auto-campaign, links back to the campaign.
    campaign_id: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    attack_type: Mapped[str] = mapped_column(String(64), index=True)
    target: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="running")  # running|success|failed
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    logs: Mapped[list] = mapped_column(JSON, default=list)
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    ai_explanation: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "correlation_id": self.correlation_id,
            "campaign_id": self.campaign_id,
            "attack_type": self.attack_type,
            "target": self.target,
            "status": self.status,
            "params": self.params,
            "logs": self.logs,
            "result": self.result,
            "ai_explanation": self.ai_explanation,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }


class Campaign(Base):
    """A guided scenario run — an ordered sequence of attacks executed together."""

    __tablename__ = "campaigns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    campaign_id: Mapped[str] = mapped_column(String(64), index=True)
    scenario_id: Mapped[str] = mapped_column(String(64), index=True)
    name: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(32), default="running")  # running|success|failed
    # Per-step metadata: [{attack_type, target, correlation_id, status, narrative}]
    steps: Mapped[list] = mapped_column(JSON, default=list)
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "campaign_id": self.campaign_id,
            "scenario_id": self.scenario_id,
            "name": self.name,
            "status": self.status,
            "steps": self.steps,
            "summary": self.summary,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }
