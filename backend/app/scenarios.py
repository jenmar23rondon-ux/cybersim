"""Guided attack scenarios."""

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
                "narrative": "Reconnaissance: discover which services the target exposes.",
            },
            {
                "attack_type": "sql_injection",
                "target": "vuln-node-api",
                "params": {},
                "narrative": "Exploit: bypass authentication and dump data via SQL injection.",
            },
            {
                "attack_type": "xss",
                "target": "vuln-node-api",
                "params": {},
                "narrative": "Exploit: inject scripts through unescaped reflected input.",
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
                "narrative": "Brute force the HTTP login endpoint with no lockout.",
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
        "name": "Full Recon to Exploit",
        "description": (
            "The complete kill-chain demo: scan, inject, script, guess credentials, "
            "and stress the service with every CyberSim module in one run."
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
    "juice_shop_demo": {
        "id": "juice_shop_demo",
        "name": "Juice Shop Two-Face Demo",
        "description": (
            "Show the vulnerable app on one side while CyberSim runs recon, sqlmap, "
            "and a bounded load test against the local Juice Shop container."
        ),
        "steps": [
            {
                "attack_type": "port_scan",
                "target": "juice-shop",
                "params": {"ports": "3000,80,443"},
                "narrative": "Map the exposed service on the OWASP Juice Shop target.",
            },
            {
                "attack_type": "sqlmap_juice",
                "target": "juice-shop",
                "params": {"port": 3000, "search": "apple", "timeout": 90},
                "narrative": "Run sqlmap in a conservative local-lab profile.",
            },
            {
                "attack_type": "ddos_sim",
                "target": "juice-shop",
                "params": {"port": 3000, "path": "/", "requests": 60, "concurrency": 8},
                "narrative": "Demonstrate request pressure with hard safety caps.",
            },
        ],
    },
    "mini_app_takeover": {
        "id": "mini_app_takeover",
        "name": "Mini App Takeover Demo",
        "description": (
            "Attack the visual CyberBank mini app: scan the Docker target, guess "
            "weak credentials, prove SQL injection, and confirm reflected XSS."
        ),
        "steps": [
            {
                "attack_type": "port_scan",
                "target": "mini-vuln-app",
                "params": {"ports": "3003,80,443,3001"},
                "narrative": "Reconnaissance: confirm the mini app exposes its web service.",
            },
            {
                "attack_type": "brute_force",
                "target": "mini-vuln-app",
                "params": {"mode": "http", "port": 3003},
                "narrative": "Credential attack: find the weak admin password with a bounded wordlist.",
            },
            {
                "attack_type": "sql_injection",
                "target": "mini-vuln-app",
                "params": {"port": 3003},
                "narrative": "Exploit: leak rows through the intentionally injectable user lookup.",
            },
            {
                "attack_type": "xss",
                "target": "mini-vuln-app",
                "params": {"port": 3003},
                "narrative": "Exploit: confirm the search page reflects script payloads without escaping.",
            },
        ],
    },
    "soc_malware_phishing_drill": {
        "id": "soc_malware_phishing_drill",
        "name": "SOC Malware + Phishing Drill",
        "description": (
            "A safe incident-response exercise: model phishing indicators, then "
            "simulate malware behavior telemetry so analysts can practice triage, "
            "containment, and remediation."
        ),
        "steps": [
            {
                "attack_type": "phishing_sim",
                "target": "mini-vuln-app",
                "params": {"template": "password_reset", "recipients": 16, "reported": 7},
                "narrative": "Initial access drill: suspicious email indicators and user reports.",
            },
            {
                "attack_type": "malware_sim",
                "target": "mini-vuln-app",
                "params": {"scenario": "info_stealer", "affected_hosts": 2, "simulate_exfil": "yes"},
                "narrative": "Post-click drill: endpoint telemetry suggests credential access and blocked exfiltration.",
            },
        ],
    },
    "advanced_cyberbank_cloud_drill": {
        "id": "advanced_cyberbank_cloud_drill",
        "name": "Advanced CyberBank Cloud Drill",
        "description": (
            "A richer Railway-ready demo against your CyberBank Docker: IDOR, "
            "authorization bypass, SQLi, advanced XSS, and safe RAT/trojan-style SOC telemetry."
        ),
        "steps": [
            {
                "attack_type": "idor_audit",
                "target": "mini-vuln-app",
                "params": {"port": 3003, "requester_id": 2, "account_id": 1001},
                "narrative": "Broken object authorization: one user reads another user's account by changing the ID.",
            },
            {
                "attack_type": "authz_bypass",
                "target": "mini-vuln-app",
                "params": {"port": 3003, "transfer_id": 501},
                "narrative": "Broken function authorization: client-controlled role approves an admin-only transfer.",
            },
            {
                "attack_type": "sql_injection",
                "target": "mini-vuln-app",
                "params": {"port": 3003},
                "narrative": "Injection: SQL-like payloads leak rows from the vulnerable user lookup.",
            },
            {
                "attack_type": "xss_advanced",
                "target": "mini-vuln-app",
                "params": {"port": 3003},
                "narrative": "Browser exploit class: prove reflected and stored XSS sinks with a harmless marker.",
            },
            {
                "attack_type": "rat_trojan_sim",
                "target": "mini-vuln-app",
                "params": {"port": 3003, "family": "rat_simulated", "affected_hosts": 2},
                "narrative": "Post-compromise drill: safe RAT/trojan telemetry opens a SOC incident without malware.",
            },
        ],
    },
    "bug_bounty_defensive_review": {
        "id": "bug_bounty_defensive_review",
        "name": "Bug Bounty Defensive Review",
        "description": (
            "A read-only review pass for demos where you want bug bounty style findings "
            "without changing target state."
        ),
        "steps": [
            {
                "attack_type": "bug_bounty_review",
                "target": "mini-vuln-app",
                "params": {"port": 3003, "requester_id": 2},
                "narrative": "Read-only triage: collect IDOR, SQLi, XSS, and authorization notes without modifying target data.",
            },
        ],
    },
    "expanded_malware_simulation_lab": {
        "id": "expanded_malware_simulation_lab",
        "name": "Expanded Malware Simulation Lab",
        "description": (
            "Safe malware-family telemetry for SOC practice: ransomware-like, worm-like, "
            "spyware, cryptominer, and RAT/trojan indicators without harmful payloads."
        ),
        "steps": [
            {
                "attack_type": "malware_sim",
                "target": "mini-vuln-app",
                "params": {"port": 3003, "scenario": "worm_lateral_movement", "affected_hosts": 2, "simulate_exfil": "no"},
                "narrative": "Simulate worm-like lateral movement indicators without network spread.",
            },
            {
                "attack_type": "malware_sim",
                "target": "mini-vuln-app",
                "params": {"port": 3003, "scenario": "cryptominer_abuse", "affected_hosts": 2, "simulate_exfil": "no"},
                "narrative": "Simulate cryptominer resource-abuse telemetry without mining.",
            },
            {
                "attack_type": "rat_trojan_sim",
                "target": "mini-vuln-app",
                "params": {"port": 3003, "family": "spyware_collection_simulated", "affected_hosts": 2},
                "narrative": "Simulate RAT/trojan collection and C2-style alerts without remote control.",
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
                {
                    "attack_type": st["attack_type"],
                    "target": st["target"],
                    "narrative": st["narrative"],
                }
                for st in s["steps"]
            ],
        }
        for s in SCENARIOS.values()
    ]


def get_scenario(scenario_id: str) -> dict | None:
    return SCENARIOS.get(scenario_id)
