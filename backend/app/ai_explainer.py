"""AI Explainer.

Produces a structured explanation of an attack: what it does, the vulnerability
exploited, remediation, and MITRE ATT&CK mapping. Uses the OpenAI API when a key
is configured; otherwise falls back to solid built-in explanations so the lab is
fully functional offline.
"""

from __future__ import annotations

import json

from .config import get_settings

# Offline knowledge base - also used as the prompt scaffold for the LLM.
KNOWLEDGE_BASE: dict[str, dict] = {
    "sql_injection": {
        "title": "SQL Injection",
        "what": (
            "The attacker sends crafted input (e.g. ' OR '1'='1) into a parameter "
            "that the application concatenates directly into a SQL query, altering "
            "the query's logic to bypass authentication or dump data."
        ),
        "vulnerability": "Unparameterized SQL built from untrusted input (CWE-89).",
        "fix": [
            "Use parameterized queries / prepared statements.",
            "Apply least-privilege DB accounts.",
            "Validate and allowlist input; use an ORM.",
            "Deploy a WAF to catch common payloads.",
        ],
        "mitre": {"id": "T1190", "name": "Exploit Public-Facing Application"},
    },
    "brute_force": {
        "title": "Brute Force / Credential Guessing",
        "what": (
            "The attacker repeatedly submits username/password combinations from a "
            "wordlist against a login service that lacks rate limiting or lockout."
        ),
        "vulnerability": "Weak credentials + no throttling/lockout (CWE-307).",
        "fix": [
            "Enforce strong password policy and MFA.",
            "Rate-limit and lock accounts after failed attempts.",
            "Use fail2ban / progressive delays.",
            "Alert on abnormal auth failure rates.",
        ],
        "mitre": {"id": "T1110", "name": "Brute Force"},
    },
    "xss": {
        "title": "Cross-Site Scripting (XSS)",
        "what": (
            "The attacker injects a script payload into a parameter that the app "
            "reflects into HTML without encoding, so it executes in a victim's browser."
        ),
        "vulnerability": "Unescaped output of untrusted input into HTML (CWE-79).",
        "fix": [
            "Context-aware output encoding.",
            "Content-Security-Policy header.",
            "Sanitize input; use framework auto-escaping.",
            "Set HttpOnly on session cookies.",
        ],
        "mitre": {"id": "T1059.007", "name": "Command and Scripting Interpreter: JavaScript"},
    },
    "port_scan": {
        "title": "Port Scanning / Service Discovery",
        "what": (
            "The attacker probes a host's TCP ports to enumerate open services and "
            "their versions, mapping the attack surface."
        ),
        "vulnerability": "Unnecessary exposed services / weak network segmentation.",
        "fix": [
            "Close unused ports; minimize exposed services.",
            "Network segmentation and firewalls.",
            "IDS/IPS to detect scan patterns.",
            "Port knocking / zero-trust access.",
        ],
        "mitre": {"id": "T1046", "name": "Network Service Discovery"},
    },
    "ddos_sim": {
        "title": "Denial of Service (low-rate simulation)",
        "what": (
            "The attacker sends a controlled burst of concurrent requests to measure "
            "how service latency degrades under load. CyberSim keeps the rate low and "
            "bounded - this demonstrates the concept, it does not flood."
        ),
        "vulnerability": "No rate limiting / insufficient capacity & autoscaling.",
        "fix": [
            "Rate limiting and connection throttling.",
            "CDN / DDoS protection (e.g. upstream scrubbing).",
            "Autoscaling and load shedding.",
            "Anomaly detection on request volume.",
        ],
        "mitre": {"id": "T1498", "name": "Network Denial of Service"},
    },
    "sqlmap_juice": {
        "title": "sqlmap against OWASP Juice Shop",
        "what": (
            "CyberSim launches sqlmap with a conservative profile against the local "
            "OWASP Juice Shop search endpoint to demonstrate how industry tools "
            "automate SQL injection testing."
        ),
        "vulnerability": "Potential injectable web parameter in a local vulnerable training app.",
        "fix": [
            "Use parameterized queries and ORM-safe query builders.",
            "Add regression tests for injection payloads.",
            "Monitor unusual query strings and automated scanner user agents.",
            "Keep vulnerable training apps isolated from production networks.",
        ],
        "mitre": {"id": "T1190", "name": "Exploit Public-Facing Application"},
    },
    "hydra_bruteforce": {
        "title": "Hydra Credential Audit",
        "what": (
            "CyberSim launches hydra against a local lab login profile to demonstrate "
            "credential guessing with a standard pentest toolkit."
        ),
        "vulnerability": "Weak credentials and missing throttling or lockout controls.",
        "fix": [
            "Enable MFA and rate limiting.",
            "Block common passwords and default lab credentials.",
            "Alert on failed-login bursts and success-after-failure patterns.",
            "Segment administrative services away from public routes.",
        ],
        "mitre": {"id": "T1110", "name": "Brute Force"},
    },
}


def _offline_explanation(attack_type: str, result: dict) -> dict:
    kb = KNOWLEDGE_BASE.get(attack_type, {})
    return {
        "generated_by": "offline-knowledge-base",
        "title": kb.get("title", attack_type),
        "what_it_does": kb.get("what", ""),
        "vulnerability_exploited": kb.get("vulnerability", ""),
        "remediation": kb.get("fix", []),
        "mitre": kb.get("mitre", {}),
    }


async def explain_attack(attack_type: str, target: str, result: dict) -> dict:
    settings = get_settings()
    if not settings.openai_api_key:
        return _offline_explanation(attack_type, result)

    kb = KNOWLEDGE_BASE.get(attack_type, {})
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.openai_api_key)
        prompt = (
            "You are a defensive security instructor. Explain this ETHICAL, lab-only "
            "attack simulation for a security demo. Return STRICT JSON with keys: "
            "what_it_does, vulnerability_exploited, remediation (array of strings), "
            "mitre (object with id and name).\n\n"
            f"Attack type: {attack_type}\n"
            f"Target (local lab container): {target}\n"
            f"Reference knowledge: {json.dumps(kb)}\n"
            f"Observed result: {json.dumps(result)[:2000]}\n"
        )
        resp = await client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        content = resp.choices[0].message.content or "{}"
        parsed = json.loads(content)
        parsed["generated_by"] = f"openai:{settings.openai_model}"
        parsed.setdefault("title", kb.get("title", attack_type))
        return parsed
    except Exception as exc:
        fallback = _offline_explanation(attack_type, result)
        fallback["note"] = f"OpenAI call failed, used offline KB ({exc})."
        return fallback
