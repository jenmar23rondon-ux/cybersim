"""Read-only boundaries for restarting a browser's lab dashboard."""

from sqlalchemy import or_, select

from .models import AttackRun, Campaign


def session_queries(after_run_id: int = 0, after_campaign_id: int = 0):
    campaigns = select(Campaign).where(Campaign.id > after_campaign_id)
    runs = select(AttackRun).where(AttackRun.id > after_run_id)
    # An older running campaign can create steps after the reset boundary.
    if after_campaign_id:
        runs = runs.where(or_(
            AttackRun.campaign_id.is_(None),
            AttackRun.campaign_id.in_(select(Campaign.campaign_id).where(Campaign.id > after_campaign_id)),
        ))
    return runs, campaigns
