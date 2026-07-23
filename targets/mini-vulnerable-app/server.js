const express = require("express");

const app = express();
const port = Number(process.env.PORT || 3003);

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

const users = [
  { id: 1, username: "admin", password: "admin123", role: "administrator", balance: 9800 },
  { id: 2, username: "ana", password: "summer2026", role: "customer", balance: 1250 },
  { id: 3, username: "demo", password: "demo", role: "auditor", balance: 500 },
];

const auditLog = [];
const securityEvents = [
  {
    id: 1,
    severity: "info",
    category: "system",
    title: "CyberBank API started",
    affected: "api",
    at: new Date().toISOString(),
  },
];
const incidents = [];
const messages = [
  {
    id: 1,
    from: "it-helpdesk@cyberbank.local",
    subject: "Quarterly password review",
    risk: "low",
    status: "delivered",
  },
  {
    id: 2,
    from: "security@cyberbank.local",
    subject: "MFA enrollment reminder",
    risk: "low",
    status: "delivered",
  },
];
const endpoints = [
  { id: "CB-WIN-014", user: "ana", status: "healthy", risk: 12, last_signal: "normal login" },
  { id: "CB-WIN-021", user: "admin", status: "healthy", risk: 18, last_signal: "browser update" },
  { id: "CB-LNX-API", user: "service-api", status: "healthy", risk: 20, last_signal: "api heartbeat" },
];

function recordSecurityEvent(event) {
  const row = {
    id: securityEvents.length + 1,
    at: new Date().toISOString(),
    ...event,
  };
  securityEvents.push(row);
  auditLog.push({ type: "security_event", category: row.category, severity: row.severity, title: row.title, at: row.at });
  return row;
}

function createIncident(summary, severity, affected, events) {
  const row = {
    id: incidents.length + 1,
    summary,
    severity,
    affected,
    status: "open",
    events,
    created_at: new Date().toISOString(),
  };
  incidents.push(row);
  return row;
}

function page(shell) {
  return `<!doctype html>
  <html lang="en">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>CyberBank API Portal</title>
      <style>
        :root { color-scheme: dark; --bg:#081018; --panel:#111b27; --line:#26364a; --text:#e6f1ff; --muted:#8da2bd; --a:#35c9ff; --b:#ffcf4a; --e:#ff6868; --ok:#65e89d; }
        * { box-sizing: border-box; }
        body { margin:0; font-family: Segoe UI, system-ui, sans-serif; background: radial-gradient(circle at top right,#17314a,var(--bg) 52%); color:var(--text); }
        main { max-width: 1120px; margin: 0 auto; padding: 22px; }
        header { display:flex; align-items:center; justify-content:space-between; gap:14px; margin-bottom:18px; }
        h1 { margin:0; color:var(--a); letter-spacing:.2px; }
        .pill { border:1px solid var(--b); color:var(--b); border-radius:999px; padding:6px 10px; font-size:12px; font-weight:800; }
        .nav { display:flex; gap:8px; flex-wrap:wrap; }
        .nav a { color:#06121a; background:var(--a); border-radius:999px; padding:8px 10px; font-weight:900; text-decoration:none; font-size:12px; }
        .grid { display:grid; grid-template-columns: 1fr 1fr; gap:14px; }
        .cards { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; margin-bottom:14px; }
        .panel,.card { background:rgba(17,27,39,.94); border:1px solid var(--line); border-radius:12px; padding:16px; }
        .card { background:#0b1420; }
        .wide { grid-column:1 / -1; }
        h2 { margin:0 0 10px; font-size:16px; color:var(--a); text-transform:uppercase; }
        p { color:var(--muted); line-height:1.5; }
        label { display:block; color:var(--muted); font-size:12px; margin-top:10px; }
        input, button { width:100%; border-radius:9px; border:1px solid var(--line); padding:10px; background:#081018; color:var(--text); }
        button { margin-top:12px; cursor:pointer; background:linear-gradient(90deg,var(--a),#6c5ce7); color:#06121a; font-weight:900; border:0; }
        button.secondary { background:#0b1420; color:var(--text); border:1px solid var(--line); }
        button.danger-action { background:linear-gradient(90deg,var(--e),#ff9f43); color:#170808; }
        .actions { display:grid; grid-template-columns:repeat(2,1fr); gap:8px; }
        .actions button { margin-top:0; }
        .live-dot { display:inline-block; width:9px; height:9px; border-radius:50%; background:var(--ok); box-shadow:0 0 12px var(--ok); margin-right:6px; }
        pre { overflow:auto; background:#050a10; border:1px solid var(--line); padding:12px; border-radius:10px; min-height:96px; }
        table { width:100%; border-collapse:collapse; }
        th,td { border-bottom:1px solid var(--line); text-align:left; padding:9px; vertical-align:top; }
        th { color:var(--muted); font-size:12px; }
        code { color:var(--a); }
        .danger,.sev-critical { color:var(--e); font-weight:800; }
        .sev-high { color:var(--b); font-weight:800; }
        .sev-medium { color:var(--a); font-weight:800; }
        .sev-info { color:var(--ok); font-weight:800; }
        @media (max-width: 760px) { .grid,.cards,.actions { grid-template-columns:1fr; } header { align-items:flex-start; flex-direction:column; } }
      </style>
    </head>
    <body><main>${shell}</main></body>
  </html>`;
}

app.get("/", (_req, res) => {
  res.send(page(`
    <header>
      <div>
        <h1>CyberBank API Portal</h1>
        <p>Mini empresa Docker con API normal, usuarios, mensajes, endpoints, SOC e incidentes de laboratorio.</p>
      </div>
      <div class="nav">
        <a href="/portal">Portal</a>
        <a href="/security">SOC</a>
        <a href="/api/status">API JSON</a>
      </div>
    </header>
    <section class="cards">
      <div class="card"><strong>Users</strong><p>${users.length} accounts</p></div>
      <div class="card"><strong>Endpoints</strong><p>${endpoints.length} monitored devices</p></div>
      <div class="card"><strong>Open Incidents</strong><p>${incidents.filter((i) => i.status === "open").length} active</p></div>
    </section>
    <section class="grid">
      <div class="panel">
        <h2>Login vulnerable</h2>
        <p>Credenciales de laboratorio: <code>admin / admin123</code>. No hay rate limit ni lockout.</p>
        <form method="post" action="/login">
          <label>Usuario</label><input name="username" value="admin" />
          <label>Password</label><input name="password" value="admin123" />
          <button>Entrar</button>
        </form>
      </div>
      <div class="panel">
        <h2>Busqueda vulnerable</h2>
        <p>Refleja la busqueda sin escapar HTML. Sirve para demostrar XSS reflejado.</p>
        <form method="get" action="/search">
          <label>Buscar movimiento</label><input name="q" value="<script>alert(1)</script>" />
          <button>Buscar</button>
        </form>
      </div>
      <div class="panel wide">
        <h2>API normal + endpoints vulnerables</h2>
        <table>
          <tr><th>Endpoint</th><th>Uso</th><th>Modulo</th></tr>
          <tr><td><code>/api/status</code></td><td>Estado normal de plataforma</td><td>API health</td></tr>
          <tr><td><code>/api/messages</code></td><td>Mensajes internos simulados</td><td>Phishing drill</td></tr>
          <tr><td><code>/api/security/events</code></td><td>Eventos SOC defensivos</td><td>Malware/Phishing drills</td></tr>
          <tr><td><code>/api/incidents</code></td><td>Incidentes abiertos/cerrados</td><td>Incident Response</td></tr>
          <tr><td><code>/api/user?username=...</code></td><td>SQLi simulado con fuga de filas</td><td>SQL Injection Demonstrator</td></tr>
          <tr><td><code>/api/login</code></td><td>Password guessing sin bloqueo</td><td>Brute Force Simulator</td></tr>
          <tr><td><code>/api/search?q=...</code></td><td>Reflected XSS sin escape</td><td>XSS Payload Injector</td></tr>
        </table>
      </div>
      <div class="panel wide">
        <h2>Ultimos eventos</h2>
        <pre>${JSON.stringify(auditLog.slice(-8), null, 2)}</pre>
      </div>
    </section>
  `));
});

app.get("/portal", (_req, res) => {
  res.send(page(`
    <header>
      <div>
        <h1>CyberBank Operations</h1>
        <p>Vista tipo app real: clientes, mensajes, endpoints y servicios internos.</p>
      </div>
      <div class="nav"><a href="/">Home</a><a href="/security">SOC</a></div>
    </header>
    <section class="grid">
      <div class="panel">
        <h2>Customers API</h2>
        <pre>${JSON.stringify(users.map(({ password, ...user }) => user), null, 2)}</pre>
      </div>
      <div class="panel">
        <h2>Messages API</h2>
        <pre>${JSON.stringify(messages.slice(-6), null, 2)}</pre>
      </div>
      <div class="panel wide">
        <h2>Endpoint Inventory</h2>
        <pre>${JSON.stringify(endpoints, null, 2)}</pre>
      </div>
    </section>
  `));
});

app.get("/security", (_req, res) => {
  res.send(page(`
    <header>
      <div>
        <h1>CyberBank SOC</h1>
        <p><span class="live-dot"></span>Live target-side SOC. Esta pantalla se actualiza sola cada 2 segundos.</p>
      </div>
      <div class="nav"><a href="/">Home</a><a href="/portal">Portal</a></div>
    </header>
    <section class="cards">
      <div class="card"><strong>Open Incidents</strong><p id="kpi-open">0</p></div>
      <div class="card"><strong>Critical Endpoint Risk</strong><p id="kpi-risk">0</p></div>
      <div class="card"><strong>Security Events</strong><p id="kpi-events">0</p></div>
    </section>
    <section class="grid">
      <div class="panel">
        <h2>Interactive Drills</h2>
        <p>Lanza eventos seguros desde el propio target. CyberSim tambien puede generarlos desde el dashboard.</p>
        <div class="actions">
          <button onclick="runPhishing()">Simulate Phishing</button>
          <button onclick="runMalware()" class="danger-action">Simulate Malware</button>
          <button onclick="containAll()" class="secondary">Contain Endpoints</button>
          <button onclick="resetLab()" class="secondary">Reset Lab</button>
        </div>
      </div>
      <div class="panel">
        <h2>Open Incidents</h2>
        <pre id="incident-json">Loading...</pre>
      </div>
      <div class="panel">
        <h2>Endpoint Risk</h2>
        <pre id="endpoint-json">Loading...</pre>
      </div>
      <div class="panel">
        <h2>Messages</h2>
        <pre id="message-json">Loading...</pre>
      </div>
      <div class="panel wide">
        <h2>Security Events</h2>
        <table id="events-table"></table>
      </div>
    </section>
    <script>
      async function json(url, options) {
        const res = await fetch(url, options);
        if (!res.ok) throw new Error(await res.text());
        return res.json();
      }
      async function refresh() {
        const [status, events, incidents, endpoints, messages] = await Promise.all([
          json('/api/status'),
          json('/api/security/events'),
          json('/api/incidents'),
          json('/api/endpoints'),
          json('/api/messages')
        ]);
        document.querySelector('#kpi-open').textContent = status.open_incidents;
        document.querySelector('#kpi-risk').textContent = endpoints.endpoints.filter((e) => e.risk >= 80).length;
        document.querySelector('#kpi-events').textContent = status.security_events;
        document.querySelector('#incident-json').textContent = JSON.stringify(incidents.incidents.slice(-6), null, 2);
        document.querySelector('#endpoint-json').textContent = JSON.stringify(endpoints.endpoints, null, 2);
        document.querySelector('#message-json').textContent = JSON.stringify(messages.messages.slice(-6), null, 2);
        document.querySelector('#events-table').innerHTML =
          '<tr><th>Time</th><th>Severity</th><th>Category</th><th>Title</th><th>Affected</th></tr>' +
          events.events.slice(-14).reverse().map((event) =>
            '<tr><td>' + event.at + '</td><td class="sev-' + event.severity + '">' + event.severity +
            '</td><td>' + event.category + '</td><td>' + event.title + '</td><td>' + (event.affected || '') + '</td></tr>'
          ).join('');
      }
      async function runPhishing() {
        await json('/api/security/phishing-drill', {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify({ template: 'mfa_prompt', recipients: 18, reported: 8 })
        });
        await refresh();
      }
      async function runMalware() {
        await json('/api/security/endpoint-telemetry', {
          method: 'POST',
          headers: { 'content-type': 'application/json' },
          body: JSON.stringify({ scenario: 'ransomware_like', affected_hosts: 2, simulate_exfil: 'yes' })
        });
        await refresh();
      }
      async function containAll() {
        await json('/api/security/contain', { method: 'POST' });
        await refresh();
      }
      async function resetLab() {
        await json('/api/security/reset', { method: 'POST' });
        await refresh();
      }
      refresh();
      setInterval(refresh, 2000);
    </script>
  `));
});

app.get("/health", (_req, res) => res.json({ status: "ok", service: "mini-vulnerable-app" }));

app.get("/api/status", (_req, res) => {
  res.json({
    service: "CyberBank API",
    status: "ok",
    users: users.length,
    endpoints: endpoints.length,
    messages: messages.length,
    security_events: securityEvents.length,
    open_incidents: incidents.filter((incident) => incident.status === "open").length,
  });
});

app.get("/api/messages", (_req, res) => res.json({ messages }));
app.get("/api/endpoints", (_req, res) => res.json({ endpoints }));
app.get("/api/security/events", (_req, res) => res.json({ events: securityEvents.slice(-50) }));
app.get("/api/incidents", (_req, res) => res.json({ incidents }));

app.post("/api/security/phishing-drill", (req, res) => {
  const template = String(req.body.template || "password_reset");
  const recipients = Number(req.body.recipients || 12);
  const reported = Number(req.body.reported || 0);
  const message = {
    id: messages.length + 1,
    from: "security-alert@cyberbank-support.local",
    subject: template === "invoice" ? "Invoice requires urgent review" : template === "mfa_prompt" ? "MFA verification required" : "Password reset required today",
    risk: "high",
    status: "simulated-quarantined",
  };
  messages.push(message);
  const event = recordSecurityEvent({
    severity: "high",
    category: "email",
    title: `Phishing drill modeled: ${message.subject}`,
    affected: "email,identity",
    details: { template, recipients, reported, emails_sent: 0, credentials_collected: 0 },
  });
  const incident = createIncident("Phishing drill: suspicious message campaign", "high", ["email", "identity"], [event.id]);
  res.status(201).json({ ok: true, message, event, incident });
});

app.post("/api/security/endpoint-telemetry", (req, res) => {
  const scenario = String(req.body.scenario || "info_stealer");
  const affectedHosts = Math.max(1, Math.min(Number(req.body.affected_hosts || 1), endpoints.length));
  const simulateExfil = String(req.body.simulate_exfil || "no") === "yes";
  const touched = endpoints.slice(0, affectedHosts).map((endpoint) => {
    endpoint.status = "contained";
    endpoint.risk = simulateExfil ? 96 : 84;
    endpoint.last_signal = scenario;
    return endpoint.id;
  });
  const event = recordSecurityEvent({
    severity: "critical",
    category: "endpoint",
    title: `Malware behavior drill: ${scenario}`,
    affected: "endpoint,identity,data",
    details: { scenario, touched, simulated_exfiltration: simulateExfil, payload_executed: false, files_created: 0 },
  });
  const incident = createIncident("Malware behavior drill: endpoint containment", "critical", ["endpoint", "identity", "data"], [event.id]);
  res.status(201).json({ ok: true, touched, event, incident });
});

app.post("/api/security/contain", (_req, res) => {
  endpoints.forEach((endpoint) => {
    if (endpoint.risk >= 80) {
      endpoint.status = "contained";
      endpoint.last_signal = "manual containment";
    }
  });
  incidents.forEach((incident) => {
    if (incident.status === "open") incident.status = "contained";
  });
  const event = recordSecurityEvent({
    severity: "medium",
    category: "response",
    title: "Manual containment applied from CyberBank SOC",
    affected: "endpoint,identity",
  });
  res.json({ ok: true, event, endpoints, incidents });
});

app.post("/api/security/reset", (_req, res) => {
  auditLog.length = 0;
  incidents.length = 0;
  messages.splice(2);
  securityEvents.length = 0;
  securityEvents.push({
    id: 1,
    severity: "info",
    category: "system",
    title: "CyberBank lab reset",
    affected: "api",
    at: new Date().toISOString(),
  });
  endpoints[0] = { id: "CB-WIN-014", user: "ana", status: "healthy", risk: 12, last_signal: "normal login" };
  endpoints[1] = { id: "CB-WIN-021", user: "admin", status: "healthy", risk: 18, last_signal: "browser update" };
  endpoints[2] = { id: "CB-LNX-API", user: "service-api", status: "healthy", risk: 20, last_signal: "api heartbeat" };
  res.json({ ok: true, endpoints, incidents, messages, securityEvents });
});

app.get("/api/user", (req, res) => {
  const username = String(req.query.username || "");
  const normalized = username.toLowerCase();
  const injectionDetected = /('|--|union|or\s+1=1|or\s+'1'='1)/i.test(username);
  const rows = injectionDetected
    ? users.map(({ password, ...publicUser }) => ({ ...publicUser, leaked_password: password }))
    : users.filter((user) => user.username === username).map(({ password, ...publicUser }) => publicUser);
  const executedQuery = `SELECT id, username, role, balance FROM users WHERE username = '${username}'`;

  auditLog.push({ type: "api_user", username, injectionDetected, count: rows.length, at: new Date().toISOString() });
  res.json({
    count: rows.length,
    rows,
    injection_detected: injectionDetected || normalized.includes("union"),
    executed_query: executedQuery,
  });
});

app.post("/api/login", (req, res) => {
  const { username, password } = req.body || {};
  const user = users.find((candidate) => candidate.username === username && candidate.password === password);
  auditLog.push({ type: "login", username, success: Boolean(user), at: new Date().toISOString() });
  if (!user) {
    return res.status(401).json({ success: false, error: "Invalid login" });
  }
  res.json({ success: true, user: { id: user.id, username: user.username, role: user.role } });
});

app.post("/login", (req, res) => {
  const { username, password } = req.body || {};
  const user = users.find((candidate) => candidate.username === username && candidate.password === password);
  auditLog.push({ type: "browser_login", username, success: Boolean(user), at: new Date().toISOString() });
  res.send(page(`
    <header><h1>CyberBank</h1><a class="pill" href="/">volver</a></header>
    <div class="panel">
      <h2>${user ? "Sesion iniciada" : "Login fallido"}</h2>
      <p>${user ? `Bienvenido ${user.username}. Rol: <code>${user.role}</code>` : "Usuario o password incorrecto."}</p>
    </div>
  `));
});

app.get("/api/search", (req, res) => {
  const q = String(req.query.q || "");
  auditLog.push({ type: "search", q, at: new Date().toISOString() });
  res.type("html").send(`<html><body><h1>Results for: ${q}</h1><p>Transfer report, invoice, customer note.</p></body></html>`);
});

app.get("/search", (req, res) => {
  const q = String(req.query.q || "");
  auditLog.push({ type: "browser_search", q, at: new Date().toISOString() });
  res.send(page(`
    <header><h1>CyberBank Search</h1><a class="pill" href="/">volver</a></header>
    <div class="panel">
      <h2>Resultados para:</h2>
      <p class="danger">${q}</p>
      <pre>Transfer report
Invoice history
Customer note</pre>
    </div>
  `));
});

app.listen(port, "0.0.0.0", () => {
  console.log(`CyberBank API target listening on ${port}`);
});
