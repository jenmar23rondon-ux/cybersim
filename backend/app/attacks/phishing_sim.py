"""Safe phishing-awareness simulation.

The module does not send email, collect credentials, or generate deceptive live
pages. It models a campaign so analysts can practice detection, triage, and
user-awareness response.
"""

from __future__ import annotations

import asyncio

import httpx

from .base import AttackModuleBase, Emit, register


@register
class PhishingSimulation(AttackModuleBase):
    id = "phishing_sim"
    name = "Phishing Awareness Simulation"
    description = "Models phishing indicators and user-report workflow without sending emails."
    default_target = "mini-vuln-app"
    mitre = "T1566"
    params_schema = {
        "template": {
            "type": "select",
            "label": "Training template",
            "default": "password_reset",
            "options": ["password_reset", "invoice", "mfa_prompt"],
        },
        "recipients": {"type": "int", "label": "Simulated recipients", "default": 12, "max": 50},
        "reported": {"type": "int", "label": "Users who report it", "default": 5, "max": 50},
        "scheme": {
            "type": "select",
            "label": "Target scheme",
            "default": "http",
            "options": ["http", "https"],
        },
        "port": {"type": "int", "label": "Target port", "default": 3003},
    }

    async def run(self, target: str, params: dict, emit: Emit) -> dict:
        template = str(params.get("template", "password_reset"))
        recipients = max(1, min(int(params.get("recipients", 12)), 50))
        reported = max(0, min(int(params.get("reported", 5)), recipients))
        report_rate = round((reported / recipients) * 100, 1)
        origin = _target_origin(target, params)

        await emit(
            "info",
            f"Starting phishing-awareness drill for {recipients} simulated user(s). No email is sent.",
            5,
            {"safe_simulation": True, "template": template},
        )
        await asyncio.sleep(0.2)

        await emit(
            "warn",
            "Email signal: spoofed sender, urgent language, and mismatched link indicators modeled.",
            28,
            {"indicator": "suspicious_email_pattern", "mitre": "T1566"},
        )
        await asyncio.sleep(0.2)

        target_event = None
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.post(
                    f"{origin}/api/security/phishing-drill",
                    json={"template": template, "recipients": recipients, "reported": reported},
                )
                response.raise_for_status()
                target_event = response.json()
            await emit(
                "info",
                "Target API updated: CyberBank SOC received the simulated phishing incident.",
                40,
                {"target_api": f"{origin}/api/security/phishing-drill", "incident_id": target_event.get("incident", {}).get("id")},
            )
        except Exception as exc:
            await emit(
                "warn",
                f"Target API event could not be recorded, continuing tabletop drill: {exc}",
                40,
                {"target_api": f"{origin}/api/security/phishing-drill"},
            )

        await emit(
            "info",
            "User behavior signal: simulated users submit phishing reports to the SOC queue.",
            52,
            {"recipients": recipients, "reported": reported, "report_rate": report_rate},
        )
        await asyncio.sleep(0.2)

        await emit(
            "warn" if report_rate < 60 else "success",
            f"Awareness metric: {report_rate}% report rate. Target coaching recommended below 60%.",
            78,
            {"report_rate": report_rate, "needs_coaching": report_rate < 60},
        )

        result = {
            "success": True,
            "safe_simulation": True,
            "template": template,
            "recipients": recipients,
            "reported": reported,
            "report_rate": report_rate,
            "emails_sent": 0,
            "credentials_collected": 0,
            "target_api_event": target_event,
            "recommended_actions": [
                "Block or quarantine lookalike domains and suspicious sender patterns.",
                "Create a user-facing report button and SOC triage queue.",
                "Coach users on urgency, mismatched URLs, and MFA prompt fatigue.",
                "Require phishing-resistant MFA for sensitive accounts.",
            ],
        }
        await emit(
            "success",
            "Phishing drill complete: awareness and detection telemetry generated safely.",
            100,
            result,
        )
        return result


def _target_origin(target: str, params: dict) -> str:
    scheme = str(params.get("scheme", "http")).lower()
    port = int(params.get("port", 443 if scheme == "https" else 3003))
    default_port = 443 if scheme == "https" else 80
    suffix = "" if port == default_port else f":{port}"
    return f"{scheme}://{target}{suffix}"
