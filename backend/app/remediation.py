"""Remediation guidance for the lab.

These guides are intentionally practical: what to change, where to look, how to
validate the fix, and a compact secure-code pattern. They do not auto-patch the
targets because the learning goal is to let the user practice fixing the issue.
"""

from __future__ import annotations

from typing import Any


GUIDES: dict[str, dict[str, Any]] = {
    "sql_injection": {
        "title": "Fix SQL Injection",
        "goal": "Stop user input from changing query logic.",
        "applies_to": ["targets/vulnerable-node-api/server.js", "OWASP Juice Shop training routes"],
        "difficulty": "medium",
        "steps": [
            "Replace string-built SQL with parameterized queries or ORM query builders.",
            "Never return executed SQL or raw DB errors to the client.",
            "Use least-privilege database users for application traffic.",
            "Add regression tests with classic payloads like ' OR '1'='1 and UNION SELECT.",
        ],
        "secure_pattern": (
            "const row = await db.get('SELECT * FROM users WHERE username = ?', [username]);\n"
            "if (!row) return res.status(404).json({ error: 'Not found' });\n"
            "return res.json({ id: row.id, username: row.username, role: row.role });"
        ),
        "verify": [
            "Run the SQL Injection Demonstrator again.",
            "Expected result after the fix: 0 working payloads and no secret rows leaked.",
            "Confirm response does not include executed_query or raw database details.",
        ],
    },
    "sqlmap_juice": {
        "title": "Fix sqlmap Findings",
        "goal": "Make automated SQL injection tooling fail safely.",
        "applies_to": ["OWASP Juice Shop concept mapping", "backend routes that build SQL queries"],
        "difficulty": "medium",
        "steps": [
            "Identify the parameter sqlmap marked as injectable.",
            "Move that route to parameterized queries and typed validation.",
            "Add request throttling for repeated scanner-like probes.",
            "Log scanner indicators, but do not block only by User-Agent.",
        ],
        "secure_pattern": (
            "const q = z.string().max(80).parse(req.query.q ?? '');\n"
            "const rows = await products.findMany({ where: { name: { contains: q } } });\n"
            "res.json({ data: rows.map(publicProductView) });"
        ),
        "verify": [
            "Run sqlmap vs Juice Shop or the equivalent local route again.",
            "Expected result: no injectable parameter confirmed.",
            "Check SecureWatch/CyberSim logs for detection without data exposure.",
        ],
    },
    "xss": {
        "title": "Fix Reflected XSS",
        "goal": "Prevent browser execution of user-controlled HTML/JavaScript.",
        "applies_to": ["targets/vulnerable-node-api/server.js /api/search"],
        "difficulty": "easy",
        "steps": [
            "Escape output based on the response context.",
            "Prefer JSON responses or templating engines with auto-escaping.",
            "Add a Content-Security-Policy header.",
            "Mark session cookies HttpOnly and SameSite where applicable.",
        ],
        "secure_pattern": (
            "const escapeHtml = (s) => String(s).replace(/[&<>\"']/g, c => ({\n"
            "  '&': '&amp;', '<': '&lt;', '>': '&gt;', '\"': '&quot;', \"'\": '&#39;'\n"
            "}[c]));\n"
            "res.send(`<h1>Results for: ${escapeHtml(q)}</h1>`);"
        ),
        "verify": [
            "Run the XSS Payload Injector again.",
            "Expected result: payloads are escaped or not reflected.",
            "View page source and confirm script tags render as text, not code.",
        ],
    },
    "brute_force": {
        "title": "Fix Weak Authentication",
        "goal": "Make repeated guessing slow, visible, and unlikely to succeed.",
        "applies_to": ["targets/vulnerable-node-api/server.js /api/login"],
        "difficulty": "medium",
        "steps": [
            "Store password hashes, never plaintext passwords.",
            "Add per-account and per-IP rate limiting.",
            "Add account lockout or progressive delays after failed attempts.",
            "Return generic login errors and alert on failure bursts.",
        ],
        "secure_pattern": (
            "const limiter = rateLimit({ windowMs: 60_000, max: 5 });\n"
            "app.post('/api/login', limiter, async (req, res) => {\n"
            "  const user = await users.findByUsername(req.body.username);\n"
            "  const ok = user && await bcrypt.compare(req.body.password, user.passwordHash);\n"
            "  if (!ok) return res.status(401).json({ success: false, error: 'Invalid login' });\n"
            "  return res.json({ success: true });\n"
            "});"
        ),
        "verify": [
            "Run Brute Force Simulator again with the same wordlist.",
            "Expected result: rate limits or lockout stop repeated attempts.",
            "Confirm logs show failed-login burst detection.",
        ],
    },
    "hydra_bruteforce": {
        "title": "Fix Hydra Credential Exposure",
        "goal": "Prevent standard credential tools from finding valid accounts.",
        "applies_to": ["weak-ssh", "web login routes", "identity provider policy"],
        "difficulty": "medium",
        "steps": [
            "Disable password SSH and require key-based authentication.",
            "Remove default lab credentials like labuser/password123.",
            "Add MFA for web and administrative access.",
            "Add fail2ban or equivalent lockout for repeated failures.",
        ],
        "secure_pattern": (
            "# SSH hardening example\n"
            "PasswordAuthentication no\n"
            "PermitRootLogin no\n"
            "MaxAuthTries 3\n"
            "AllowUsers named-admin-user"
        ),
        "verify": [
            "Run Hydra Credential Audit again.",
            "Expected result: no valid credential finding.",
            "Confirm failed attempts are throttled and visible in logs.",
        ],
    },
    "port_scan": {
        "title": "Reduce Port Scan Exposure",
        "goal": "Expose only the services the application actually needs.",
        "applies_to": ["docker-compose.yml", "firewall/security group rules"],
        "difficulty": "easy",
        "steps": [
            "Remove unused published ports from docker-compose.yml.",
            "Keep internal-only services on the Docker network without host ports.",
            "Document the owner and purpose of every exposed port.",
            "Alert when scanning touches sensitive ranges.",
        ],
        "secure_pattern": (
            "services:\n"
            "  db:\n"
            "    ports: []   # internal only\n"
            "    networks: [cybersim-net]"
        ),
        "verify": [
            "Run Port Scanner again.",
            "Expected result: only intentionally exposed lab ports appear open.",
            "Confirm unexpected admin/database ports are not published to localhost.",
        ],
    },
    "ddos_sim": {
        "title": "Add Load Protection",
        "goal": "Keep the service usable during request bursts.",
        "applies_to": ["Express routes", "reverse proxy/CDN", "autoscaling policy"],
        "difficulty": "medium",
        "steps": [
            "Add request rate limits per client and endpoint.",
            "Cache safe responses and make expensive routes cheaper.",
            "Add timeouts, queue limits, and graceful load shedding.",
            "Monitor p95 latency and error rate during bursts.",
        ],
        "secure_pattern": (
            "const limiter = rateLimit({ windowMs: 60_000, max: 120 });\n"
            "app.use('/api', limiter);\n"
            "server.headersTimeout = 15_000;\n"
            "server.requestTimeout = 20_000;"
        ),
        "verify": [
            "Run the DDoS Simulation again with the same bounded settings.",
            "Expected result: lower p95 latency or clear 429 rate-limit responses.",
            "Confirm dashboards show rate-limit events instead of service crashes.",
        ],
    },
    "malware_sim": {
        "title": "Respond to Malware Indicators",
        "goal": "Contain affected endpoints, preserve evidence, and remove the root cause.",
        "applies_to": ["endpoint fleet", "EDR policy", "backup and incident response procedure"],
        "difficulty": "hard",
        "steps": [
            "Isolate affected host(s) from the network without powering them off.",
            "Collect EDR timeline, process tree, hashes, user context, and relevant logs.",
            "Scope lateral movement by checking authentication, SMB, RDP, and admin activity.",
            "Rotate exposed credentials and revoke sessions when credential access is suspected.",
            "Restore from known-clean backups only after persistence and initial access are removed.",
        ],
        "secure_pattern": (
            "Incident checklist:\n"
            "1. Isolate endpoint.\n"
            "2. Preserve evidence.\n"
            "3. Scope users, hosts, and credentials.\n"
            "4. Remove persistence.\n"
            "5. Restore and monitor for recurrence."
        ),
        "verify": [
            "Run Malware Behavior Simulation again.",
            "Expected result: SOC detects the same indicators faster and containment actions are documented.",
            "Confirm no real files or payloads are created because this is a safe drill.",
        ],
    },
    "phishing_sim": {
        "title": "Reduce Phishing Risk",
        "goal": "Make phishing easier to report, faster to contain, and harder to convert into account takeover.",
        "applies_to": ["email security gateway", "identity provider", "user awareness program"],
        "difficulty": "medium",
        "steps": [
            "Enable SPF, DKIM, and DMARC enforcement for owned domains.",
            "Deploy a visible phishing report button and SOC triage queue.",
            "Block or monitor lookalike domains and suspicious sender patterns.",
            "Use phishing-resistant MFA for privileged and sensitive users.",
            "Run awareness drills and coach users on the indicators they missed.",
        ],
        "secure_pattern": (
            "Email response flow:\n"
            "reported_message -> header review -> recipient search -> quarantine -> "
            "identity check -> user coaching -> detection update"
        ),
        "verify": [
            "Run Phishing Awareness Simulation again.",
            "Expected result: higher report rate and faster triage steps.",
            "Confirm the drill sends 0 emails and collects 0 credentials.",
        ],
    },
}


def list_guides() -> list[dict[str, Any]]:
    return [{"attack_type": key, **value} for key, value in sorted(GUIDES.items())]


def guide_for(attack_type: str) -> dict[str, Any]:
    guide = GUIDES.get(attack_type)
    if guide is None:
        return {
            "attack_type": attack_type,
            "title": "General Remediation",
            "goal": "Review the finding, identify root cause, apply a control, and rerun validation.",
            "applies_to": [],
            "difficulty": "medium",
            "steps": [
                "Identify the vulnerable endpoint or service.",
                "Apply the smallest control that removes the root cause.",
                "Add a regression test or monitoring rule.",
                "Rerun the CyberSim attack to validate the fix.",
            ],
            "secure_pattern": "",
            "verify": ["Rerun the original attack and confirm it no longer succeeds."],
        }
    return {"attack_type": attack_type, **guide}
