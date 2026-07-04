"""Guided attack scenarios.

Each scenario is a named, ordered sequence of attack steps with a short
narrative. Running a scenario launches an auto-campaign that chains the steps,
correlating everything under one campaign id (and one SIEM correlation trail).
"""

from __future__ import annotations

SCENARIOS: dict[str, dict] = {
    "web_app_pentest": {
        "id": "web_app_pentest",
        "name": "Web Application Pentest",
        "description": (
            "Full black-box pass against the vulnerable web API: map the surface, "
            "then exploit injection and cross-site scripting flaws."
        ),
        "steps": [
            {
                "attack_type": "port_scan",
                "target": "vuln-node-api",
                "params": {"ports": "3001,8000,80,443"},
                "narrative": "Reconnaissance — discover which services the target exposes.",
            },
            {
                "attack_type": "sql_injection",
                "target": "vuln-node-api",
                "params": {},
                "narrative": "Exploit — bypass authentication and dump data via SQL injection.",
            },
            {
                "attack_type": "xss",
                "target": "vuln-node-api",
                "params": {},
                "narrative": "Exploit — inject scripts through unescaped reflected input.",
            },
        ],
    },
    "credential_attack": {
        "id": "credential_attack",
        "name": "Credential Attack",
        "description": (
            "Guess weak credentials against both the web login and the SSH server "
            "that lack rate limiting or lockout."
        ),
        "steps": [
            {
                "attack_type": "brute_force",
                "target": "vuln-node-api",
                "params": {"mode": "http", "port": 3001},
                "narrative": "Brute force the HTTP login endpoint (no lockout).",
            },
            {
                "attack_type": "brute_force",
                "target": "weak-ssh",
                "params": {"mode": "ssh", "port": 22},
                "narrative": "Brute force the SSH service with common credentials.",
            },
        ],
    },
    "full_recon_exploit": {
        "id": "full_recon_exploit",
        "name": "Full Recon → Exploit (all modules)",
        "description": (
            "The complete kill-chain demo: scan, inject, script, guess credentials, "
            "and stress the service — every CyberSim module in one run."
        ),
        "steps": [
            {
                "attack_type": "port_scan",
                "target": "vuln-node-api",
                "params": {"ports": "21-25,80,443,3001,3306,5432,8000"},
                "narrative": "Enumerate the attack surface.",
            },
            {
                "attack_type": "sql_injection",
                "target": "vuln-node-api",
                "params": {},
                "narrative": "Exploit an injectable query.",
            },
            {
                "attack_type": "xss",
                "target": "vuln-node-api",
                "params": {},
                "narrative": "Prove reflected XSS.",
            },
            {
                "attack_type": "brute_force",
                "target": "vuln-node-api",
                "params": {"mode": "http"},
                "narrative": "Guess weak application credentials.",
            },
            {
                "attack_type": "ddos_sim",
                "target": "vuln-node-api",
                "params": {"requests": 80, "concurrency": 10},
                "narrative": "Show latency degradation under bounded load.",
            },
        ],
    },
    "incident_response_drill": {
        "id": "incident_response_drill",
        "name": "Incident Response Drill",
        "description": (
            "A SOC-style exercise: recon first, then credential pressure, then "
            "web exploitation so analysts can correlate events across phases."
        ),
        "steps": [
            {
                "attack_type": "port_scan",
                "target": "vuln-node-api",
                "params": {"ports": "22,80,443,3001,8000"},
                "narrative": "Detect initial service discovery and confirm exposed services.",
            },
            {
                "attack_type": "brute_force",
                "target": "vuln-node-api",
                "params": {"mode": "http", "port": 3001},
                "narrative": "Alert on repeated authentication failures and possible success.",
            },
            {
                "attack_type": "sql_injection",
                "target": "vuln-node-api",
                "params": {},
                "narrative": "Correlate exploit attempt after reconnaissance and credential activity.",
            },
        ],
    },
}


def list_scenarios() -> list[dict]:
    return [
        {
            "id": s["id"],
            "name": s["name"],
            "description": s["description"],
            "steps": [
                {"attack_type": st["attack_type"], "target": st["target"],
                 "narrative": st["narrative"]}
                for st in s["steps"]
            ],
        }
        for s in SCENARIOS.values()
    ]


def get_scenario(scenario_id: str) -> dict | None:
    return SCENARIOS.get(scenario_id)
