"""Defensive analytics for CyberSim.

This module turns attack-run telemetry into SOC-friendly material: severity,
detection logic, triage questions, executive metrics, and remediation tasks.
It is intentionally defensive and local-lab oriented.
"""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select

from .database import SessionLocal
from .models import AttackRun, Campaign


PLAYBOOKS: dict[str, dict[str, Any]] = {
    "sql_injection": {
        "severity": "high",
        "business_impact": "Unauthorized data access and authentication bypass.",
        "detections": [
            "HTTP parameters containing quote/comment SQL metacharacters.",
            "Login success after malformed credentials.",
            "Database errors or UNION-like responses in web logs.",
        ],
        "securewatch_query": 'source="CyberSim" attack_type="sql_injection" level IN ("warn","success")',
        "triage": [
            "Identify affected route and parameter.",
            "Review DB account privileges used by the application.",
            "Confirm whether sensitive rows were exposed in the response.",
        ],
        "remediation": [
            "Move all queries to parameterized statements.",
            "Add regression tests with known injection payloads.",
            "Alert on repeated SQL metacharacter patterns in request fields.",
        ],
    },
    "brute_force": {
        "severity": "high",
        "business_impact": "Account takeover risk through weak credentials.",
        "detections": [
            "Many failed logins from the same source in a short window.",
            "Credential stuffing against multiple usernames.",
            "Successful login immediately after repeated failures.",
        ],
        "securewatch_query": 'source="CyberSim" attack_type="brute_force" correlation_id=*',
        "triage": [
            "Check the username targeted and whether a success followed failures.",
            "Review source IP, user agent, and geo anomalies.",
            "Look for the same password attempts across multiple accounts.",
        ],
        "remediation": [
            "Enable MFA for all privileged and remote-access users.",
            "Add rate limiting and account lockout with safe unlock workflows.",
            "Block common passwords and rotate lab/default credentials.",
        ],
    },
    "xss": {
        "severity": "medium",
        "business_impact": "Session theft, content injection, and browser-side compromise.",
        "detections": [
            "Script tags or event handlers in query/body parameters.",
            "Reflected payloads returning in HTML responses.",
            "CSP violation reports from browsers.",
        ],
        "securewatch_query": 'source="CyberSim" attack_type="xss" level="success"',
        "triage": [
            "Find the exact reflected field and output context.",
            "Check whether authentication cookies are protected with HttpOnly.",
            "Review CSP report-only logs before enforcing a stricter policy.",
        ],
        "remediation": [
            "Use framework auto-escaping and context-aware output encoding.",
            "Add a restrictive Content Security Policy.",
            "Sanitize rich-text fields with an allowlist sanitizer.",
        ],
    },
    "port_scan": {
        "severity": "medium",
        "business_impact": "Reconnaissance exposes services that can become attack paths.",
        "detections": [
            "Sequential connection attempts across many ports.",
            "Short-lived TCP connections with no application payload.",
            "Service discovery patterns followed by exploit attempts.",
        ],
        "securewatch_query": 'source="CyberSim" attack_type="port_scan"',
        "triage": [
            "List open ports and confirm each has a business owner.",
            "Check whether management services are exposed unnecessarily.",
            "Correlate scan timing with later exploitation events.",
        ],
        "remediation": [
            "Close unused ports and enforce host firewall policy.",
            "Segment targets behind private networks.",
            "Alert when scans touch sensitive service ranges.",
        ],
    },
    "ddos_sim": {
        "severity": "medium",
        "business_impact": "Service slowdown or outage under request bursts.",
        "detections": [
            "Request-rate spikes and latency increases.",
            "Many concurrent requests from the same source.",
            "Error-rate changes during load bursts.",
        ],
        "securewatch_query": 'source="CyberSim" attack_type="ddos_sim"',
        "triage": [
            "Compare request volume, latency, and error rate during the event.",
            "Identify expensive endpoints and missing cache opportunities.",
            "Confirm rate-limit behavior and upstream protections.",
        ],
        "remediation": [
            "Add endpoint rate limits and request budgets.",
            "Cache expensive responses where safe.",
            "Use load shedding and upstream DDoS protection for public services.",
        ],
    },
    "sqlmap_juice": {
        "severity": "high",
        "business_impact": "Automated SQL injection tooling can quickly confirm and enumerate vulnerable data paths.",
        "detections": [
            "Requests with sqlmap-like user agents or timing patterns.",
            "Repeated encoded payloads against the same query parameter.",
            "Database error patterns after automated parameter testing.",
        ],
        "securewatch_query": 'source="CyberSim" attack_type="sqlmap_juice" tool="sqlmap"',
        "triage": [
            "Identify the parameter sqlmap tested and the endpoint owner.",
            "Review whether the scanner confirmed DBMS or injectable behavior.",
            "Check if the same source touched authentication or admin endpoints.",
        ],
        "remediation": [
            "Parameterize all SQL statements behind the endpoint.",
            "Add WAF signatures for automated injection scanners.",
            "Add request throttling and alert on repeated encoded payloads.",
        ],
    },
    "hydra_bruteforce": {
        "severity": "high",
        "business_impact": "Automated credential guessing can lead to account compromise when weak passwords exist.",
        "detections": [
            "Many login attempts with different credential pairs.",
            "Successful login after repeated failed attempts.",
            "Hydra-like connection cadence against SSH or web login routes.",
        ],
        "securewatch_query": 'source="CyberSim" attack_type="hydra_bruteforce" tool="hydra"',
        "triage": [
            "Confirm which account and protocol were targeted.",
            "Look for success markers after failed login bursts.",
            "Check whether the same credentials are reused elsewhere.",
        ],
        "remediation": [
            "Enable MFA, lockout, and progressive delays.",
            "Disable password SSH where possible and use keys.",
            "Rotate weak/default credentials in lab and production baselines.",
        ],
    },
    "malware_sim": {
        "severity": "critical",
        "business_impact": "Endpoint compromise can disrupt operations, expose credentials, and cause data loss.",
        "detections": [
            "Script interpreter burst from an unusual parent process.",
            "Mass file modification, rename, or encryption-like behavior.",
            "Startup persistence changes, suspicious services, or scheduled task creation.",
            "Outbound connection attempts after credential or file-access signals.",
        ],
        "securewatch_query": 'source="CyberSim" attack_type="malware_sim" level IN ("warn","success")',
        "triage": [
            "Identify affected host, user, process tree, and first-seen timestamp.",
            "Check whether credential stores, browser sessions, or sensitive files were touched.",
            "Preserve evidence before cleanup and scope for lateral movement.",
        ],
        "remediation": [
            "Isolate affected endpoint network access.",
            "Reimage or clean from a trusted baseline after root cause is known.",
            "Rotate exposed credentials and revoke active sessions.",
            "Restore data from clean backups and add detections for observed indicators.",
        ],
    },
    "phishing_sim": {
        "severity": "high",
        "business_impact": "Credential theft or account takeover through social engineering.",
        "detections": [
            "Spoofed or newly registered sender domains.",
            "Urgent language combined with mismatched links or attachments.",
            "Multiple user reports for similar subject lines or URLs.",
            "Login, MFA, or password-reset anomalies after message delivery.",
        ],
        "securewatch_query": 'source="CyberSim" attack_type="phishing_sim"',
        "triage": [
            "Review reported message headers, sender, subject, and target URL.",
            "Search for other recipients and quarantine matching messages.",
            "Check whether any user interacted with the link or had suspicious login activity.",
        ],
        "remediation": [
            "Quarantine messages and block malicious/lookalike domains.",
            "Reset credentials only for users with exposure indicators.",
            "Require phishing-resistant MFA on privileged and sensitive accounts.",
            "Coach users using the exact indicators from the drill.",
        ],
    },
}


SEVERITY_SCORE = {"low": 25, "medium": 55, "high": 80, "critical": 95}


def playbook_for(attack_type: str) -> dict[str, Any]:
    base = PLAYBOOKS.get(attack_type, {})
    return {
        "attack_type": attack_type,
        "severity": base.get("severity", "low"),
        "business_impact": base.get("business_impact", "Lab finding requires analyst review."),
        "detections": base.get("detections", []),
        "securewatch_query": base.get("securewatch_query", f'source="CyberSim" attack_type="{attack_type}"'),
        "triage": base.get("triage", []),
        "remediation": base.get("remediation", []),
        "risk_score": SEVERITY_SCORE.get(base.get("severity", "low"), 25),
    }


def enrich_run(run: dict[str, Any]) -> dict[str, Any]:
    pb = playbook_for(run["attack_type"])
    log_levels = Counter((event.get("level") or "info") for event in run.get("logs") or [])
    confirmed = run.get("status") == "success"
    score = pb["risk_score"] + (10 if confirmed else 0)
    run["defense"] = {
        **pb,
        "confirmed": confirmed,
        "risk_score": min(score, 100),
        "log_level_counts": dict(log_levels),
        "event_count": len(run.get("logs") or []),
    }
    return run


async def list_playbooks() -> list[dict[str, Any]]:
    return [playbook_for(k) for k in sorted(PLAYBOOKS)]


async def build_metrics() -> dict[str, Any]:
    async with SessionLocal() as s:
        runs = (await s.execute(select(AttackRun))).scalars().all()
        campaigns = (await s.execute(select(Campaign))).scalars().all()

    status_counts = Counter(r.status for r in runs)
    attack_counts = Counter(r.attack_type for r in runs)
    confirmed = [r for r in runs if r.status == "success"]
    scores = [enrich_run(r.to_dict())["defense"]["risk_score"] for r in runs]
    recent = sorted(runs, key=lambda r: r.started_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)[:8]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_runs": len(runs),
        "confirmed_findings": len(confirmed),
        "campaigns": len(campaigns),
        "status_counts": dict(status_counts),
        "attack_counts": dict(attack_counts),
        "average_risk_score": round(sum(scores) / len(scores), 1) if scores else 0,
        "top_findings": [
            {
                "correlation_id": r.correlation_id,
                "attack_type": r.attack_type,
                "target": r.target,
                "status": r.status,
                "risk_score": enrich_run(r.to_dict())["defense"]["risk_score"],
                "started_at": r.started_at.isoformat() if r.started_at else None,
            }
            for r in recent
        ],
    }
