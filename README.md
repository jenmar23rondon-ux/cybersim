# CyberSim

CyberSim is an interactive ethical attack simulator for cybersecurity demos,
training, and interview presentations. It runs a complete local lab with
intentionally vulnerable Docker targets, a FastAPI attack engine, real-time
WebSocket logs, SOC-style detection panels, remediation guidance, optional AI
explanations, and PDF reporting.

CyberSim is designed to show both sides of the story:

- The vulnerable application or service being attacked.
- The defender view that explains impact, detection, affected components, and
  how to fix the issue.

> Authorized lab use only. CyberSim is built to attack only local, allowlisted
> Docker containers. Do not deploy the vulnerable targets to the public internet.

## Highlights

- Local Docker lab with vulnerable targets and attack tooling.
- React + TypeScript dashboard with live logs, progress, impact map, and history.
- FastAPI backend with WebSocket streaming and PostgreSQL persistence.
- Guided campaigns that chain multiple attack modules under one correlation ID.
- AI Explainer with OpenAI support, plus offline fallback explanations.
- Remediation Lab with fix steps, validation checks, and secure code patterns.
- Impact Map that shows which areas were affected: API, auth, database, browser,
  network, availability, endpoint, and email/identity.
- Safe malware and phishing drills that generate defensive telemetry without
  payloads, email delivery, or credential collection.
- PDF reports for individual attacks and campaigns.
- Optional SecureWatch SIEM webhook integration.
- Installable dashboard PWA for mobile demos.

## Architecture

| Layer | Technology | Purpose |
| --- | --- | --- |
| Dashboard | React, TypeScript, Vite | Launch attacks, view logs, inspect impact, download reports |
| Backend | FastAPI, SQLAlchemy, WebSocket | Orchestrates attacks and streams events |
| Database | PostgreSQL | Stores runs, logs, history, and campaigns |
| Attack engine | Python, Nmap, sqlmap, Hydra | Executes bounded local-lab simulations |
| Vulnerable targets | Docker | CyberBank, OWASP Juice Shop, DVWA, Node API, weak SSH |
| Reporting | fpdf2 | Executive and technical PDF reports |
| AI | OpenAI optional | Explains findings, MITRE mapping, detection, and remediation |

## Lab Targets

| Target | URL / Address | Purpose |
| --- | --- | --- |
| Dashboard | http://localhost:5173 | Main CyberSim interface |
| Backend API docs | http://localhost:8000/docs | FastAPI documentation |
| CyberBank Mini App | http://localhost:3003 | Visual vulnerable app for SQLi, XSS, brute force, scans |
| CyberBank Portal | http://localhost:3003/portal | Normal-looking business API view |
| CyberBank SOC | http://localhost:3003/security | Target-side security events and incident view |
| OWASP Juice Shop | http://localhost:3002 | Industry-standard vulnerable web app |
| Vulnerable Node API | http://localhost:3001 | Small API used by built-in attack modules |
| DVWA | http://localhost:4280 | Classic web security practice target |
| Weak SSH | `ssh labuser@localhost -p 2222` | Weak SSH credential demo, password `password123` |

Inside Docker, use service names:

```text
mini-vuln-app:3003
juice-shop:3000
vuln-node-api:3001
weak-ssh:22
dvwa:80
```

## Quick Start

### Windows

Start Docker Desktop, then run:

```powershell
.\start.bat
```

To stop everything:

```powershell
.\stop.bat
```

### Any OS

```bash
cp .env.example .env
docker compose up --build
```

Then open:

```text
http://localhost:5173
```

The stack uses health checks so services start in order: database, backend,
dashboard, then targets and tooling.

## Demo Flow

Use this flow for interviews or presentations:

1. Open CyberSim at `http://localhost:5173`.
2. Open CyberBank at `http://localhost:3003` in another tab or side-by-side.
3. In CyberSim, choose **Guided Scenario**.
4. Launch **Mini App Takeover Demo**.
5. Watch the live attack logs and campaign progress.
6. Use **Impact Map** to explain what was affected and what was not.
7. Open **AI Explainer** and **Detection Lab** for the defensive view.
8. Use **Remediation Lab** to show how the vulnerability should be fixed.
9. Download the PDF report.

## Attack Modules

| Module | Default target | MITRE | What it demonstrates |
| --- | --- | --- | --- |
| `port_scan` | `vuln-node-api` | T1046 | Service discovery with Nmap or TCP fallback |
| `sql_injection` | `vuln-node-api` | T1190 | Auth bypass and data exposure through injectable input |
| `xss` | `vuln-node-api` | T1059.007 | Reflected XSS through unescaped output |
| `brute_force` | `vuln-node-api` | T1110 | HTTP or SSH credential guessing with bounded wordlists |
| `ddos_sim` | `vuln-node-api` | T1498 | Low-rate capped load test for availability impact |
| `sqlmap_juice` | `juice-shop` | T1190 | Conservative sqlmap profile against Juice Shop |
| `hydra_bruteforce` | `weak-ssh` | T1110 | Hydra-based local credential audit |
| `malware_sim` | `mini-vuln-app` | T1059 | Safe endpoint malware-behavior telemetry drill |
| `phishing_sim` | `mini-vuln-app` | T1566 | Safe phishing-awareness and user-reporting drill |

`malware_sim` and `phishing_sim` are simulations only. They do not create
malware, encrypt files, send emails, host phishing pages, or collect
credentials. They are included so you can demonstrate SOC detection,
containment, and remediation workflows safely.

When these drills target `mini-vuln-app`, they also call the CyberBank API:

```text
POST /api/security/phishing-drill
POST /api/security/endpoint-telemetry
GET  /api/security/events
GET  /api/incidents
```

That makes the Docker target look more like a normal company API: CyberSim
shows the attacker/analyst view, while `http://localhost:3003/security` shows
how the same incident appears inside the target application's SOC panel.

The built-in modules can target CyberBank by using:

```text
Target: mini-vuln-app
Port: 3003
```

## Guided Scenarios

| Scenario | Steps |
| --- | --- |
| Web Application Pentest | Port scan -> SQL injection -> XSS |
| Credential Attack | HTTP brute force -> SSH brute force |
| Full Recon to Exploit | Scan -> SQLi -> XSS -> brute force -> load simulation |
| Incident Response Drill | Recon -> credential pressure -> SQLi correlation |
| Juice Shop Two-Face Demo | Scan -> sqlmap -> bounded load test |
| Mini App Takeover Demo | Scan -> brute force -> SQLi -> XSS |
| SOC Malware + Phishing Drill | Phishing simulation -> malware behavior simulation |

Scenarios are defined in:

```text
backend/app/scenarios.py
```

## Dashboard Features

- **Metrics Strip**: total runs, confirmed findings, campaigns, average risk.
- **Target Showcase**: opens vulnerable targets directly.
- **Target Connector**: connect and reuse additional authorized local apps.
- **Impact Map**: visual affected/not-affected component map.
- **Live Attack**: real-time logs over WebSocket with progress and status.
- **AI Explainer**: explains what happened and how to fix it.
- **Detection Lab**: SOC playbook, severity, triage questions, SecureWatch query.
- **Remediation Lab**: fix checklist and secure code patterns.
- **History**: re-open previous runs and reports.

## Connecting Your Own Apps

CyberSim can connect to other apps you own or are explicitly authorized to test,
as long as they are local, private-network, or explicitly allowlisted lab
targets.

Use the **Target Connector** panel in the dashboard:

1. Enter a profile name.
2. Enter the app URL or Docker service, for example `http://mini-vuln-app:3003`.
3. Set a health path, for example `/health`.
4. Click **Test connection**.
5. If the backend approves and reaches the app, click **Save & apply**.
6. Launch the selected CyberSim module against the connected target.

The connector stores target profiles in the browser local storage so you can
reuse them during demos.

Public websites are blocked by design. The backend validates each connector
through the same safety guard used by attack launches. If the hostname is not
allowlisted and does not resolve to a private or loopback address, CyberSim
returns HTTP 403 before any attack module can run.

To add another Docker target, put it on the `cybersim-net` network and add its
service/container name to `TARGET_ALLOWLIST` in `.env`.

## Mobile App Mode

The dashboard is an installable PWA.

After deploying `dashboard/` to Vercel:

- Android Chrome: tap **Install app**, or use browser menu -> **Add to Home screen**.
- iPhone Safari: tap Share -> **Add to Home Screen**.

For local phone demos, keep the phone and PC on the same Wi-Fi and open the PC
LAN IP, for example:

```text
http://192.168.1.25:5173
```

Do not use `localhost` from the phone. On a phone, `localhost` points to the
phone itself, not the computer running Docker.

## Optional AI Explainer

CyberSim works without an OpenAI key. If `OPENAI_API_KEY` is empty, it uses
built-in offline explanations.

To enable OpenAI explanations, set:

```env
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-4o-mini
```

## SecureWatch SIEM Integration

Set these variables in `.env`:

```env
SECUREWATCH_WEBHOOK_URL=
SECUREWATCH_API_KEY=
```

CyberSim sends each event with a shared `correlation_id`, so the SIEM can match
the simulated attack with its detection timeline.

Example event:

```json
{
  "source": "CyberSim",
  "event_type": "simulated_attack",
  "correlation_id": "a1b2c3d4e5f6",
  "attack_type": "sql_injection",
  "target": "mini-vuln-app",
  "level": "success",
  "message": "Injection succeeded",
  "timestamp": "2026-07-17T00:00:00Z"
}
```

## Manual Pentest Toolbox

CyberSim includes a toolbox container with sqlmap, Hydra, Nmap, curl, and jq:

```bash
docker exec -it cybersim-attacker-tools bash
```

Example commands inside the container:

```bash
nmap -sT -sV -p 3003 mini-vuln-app
curl "http://mini-vuln-app:3003/api/user?username=admin"
```

## Safety Controls

- **Allowlist guard**: attacks are rejected unless the target is local and
  allowlisted.
- **Private network only**: targets run on the `cybersim-net` Docker bridge.
- **DDoS caps**: load simulation is hard-capped at 200 requests and 20
  concurrent workers.
- **Disposable targets**: vulnerable apps are intentionally insecure and should
  never be exposed publicly.
- **No external targets**: public IPs and non-allowlisted domains are blocked.

## Environment Variables

Copy `.env.example` to `.env` and adjust as needed.

| Variable | Required | Description |
| --- | --- | --- |
| `POSTGRES_USER` | No | Local PostgreSQL username |
| `POSTGRES_PASSWORD` | No | Local PostgreSQL password |
| `POSTGRES_DB` | No | Local PostgreSQL database name |
| `OPENAI_API_KEY` | No | Enables AI Explainer |
| `OPENAI_MODEL` | No | OpenAI model name |
| `SECUREWATCH_WEBHOOK_URL` | No | SIEM webhook URL |
| `SECUREWATCH_API_KEY` | No | SIEM API key |
| `TARGET_ALLOWLIST` | Yes | Comma-separated local targets accepted by the safety guard |

## Validation

Run the same checks used by CI:

```powershell
.\validate.bat
```

Or manually:

```bash
docker compose config --quiet
cd dashboard && npm run build
cd ../backend && python -m compileall app
```

## Troubleshooting

### Dashboard says "Failed to fetch"

The backend is not reachable from the dashboard. Check:

```bash
docker compose ps
docker logs cybersim-backend --tail 80
```

Backend should be available at:

```text
http://localhost:8000/health
```

### A target is blocked by the backend

Check `TARGET_ALLOWLIST` in `.env`. The target must be a local Docker service
name or loopback/private address.

### Docker containers are unhealthy

Restart the lab:

```bash
docker compose down
docker compose up --build
```

### Mobile app cannot reach the lab

Use the PC LAN IP instead of `localhost`, and keep the phone on the same Wi-Fi.

## Project Structure

```text
CyberSim/
├── docker-compose.yml
├── .env.example
├── start.bat
├── stop.bat
├── validate.bat
├── backend/
│   └── app/
│       ├── main.py
│       ├── engine.py
│       ├── campaign.py
│       ├── safety.py
│       ├── ai_explainer.py
│       ├── defense.py
│       ├── remediation.py
│       ├── report.py
│       └── attacks/
├── dashboard/
│   ├── public/
│   └── src/
│       ├── components/
│       ├── hooks/
│       └── App.tsx
└── targets/
    ├── mini-vulnerable-app/
    ├── vulnerable-node-api/
    ├── weak-ssh/
    └── attacker-tools/
```

## License

MIT. See `LICENSE`.
