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

function page(shell) {
  return `<!doctype html>
  <html lang="en">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1" />
      <title>CyberBank Vulnerable Target</title>
      <style>
        :root { color-scheme: dark; --bg:#081018; --panel:#111b27; --line:#26364a; --text:#e6f1ff; --muted:#8da2bd; --a:#35c9ff; --b:#ffcf4a; --e:#ff6868; }
        * { box-sizing: border-box; }
        body { margin:0; font-family: Segoe UI, system-ui, sans-serif; background: radial-gradient(circle at top right,#17314a,var(--bg) 52%); color:var(--text); }
        main { max-width: 1120px; margin: 0 auto; padding: 22px; }
        header { display:flex; align-items:center; justify-content:space-between; gap:14px; margin-bottom:18px; }
        h1 { margin:0; color:var(--a); letter-spacing:.2px; }
        .pill { border:1px solid var(--b); color:var(--b); border-radius:999px; padding:6px 10px; font-size:12px; font-weight:800; }
        .grid { display:grid; grid-template-columns: 1fr 1fr; gap:14px; }
        .panel { background:rgba(17,27,39,.94); border:1px solid var(--line); border-radius:12px; padding:16px; }
        .wide { grid-column:1 / -1; }
        h2 { margin:0 0 10px; font-size:16px; color:var(--a); text-transform:uppercase; }
        p { color:var(--muted); line-height:1.5; }
        label { display:block; color:var(--muted); font-size:12px; margin-top:10px; }
        input, button { width:100%; border-radius:9px; border:1px solid var(--line); padding:10px; background:#081018; color:var(--text); }
        button { margin-top:12px; cursor:pointer; background:linear-gradient(90deg,var(--a),#6c5ce7); color:#06121a; font-weight:900; border:0; }
        pre { overflow:auto; background:#050a10; border:1px solid var(--line); padding:12px; border-radius:10px; min-height:96px; }
        table { width:100%; border-collapse:collapse; }
        th,td { border-bottom:1px solid var(--line); text-align:left; padding:9px; }
        th { color:var(--muted); font-size:12px; }
        code { color:var(--a); }
        .danger { color:var(--e); font-weight:800; }
        @media (max-width: 760px) { .grid { grid-template-columns:1fr; } header { align-items:flex-start; flex-direction:column; } }
      </style>
    </head>
    <body><main>${shell}</main></body>
  </html>`;
}

app.get("/", (_req, res) => {
  res.send(page(`
    <header>
      <div>
        <h1>CyberBank</h1>
        <p>Mini app vulnerable intencional para demostrar las dos caras: sistema expuesto y ataque en vivo.</p>
      </div>
      <span class="pill">LOCAL DOCKER TARGET</span>
    </header>
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
        <h2>Endpoints para CyberSim</h2>
        <table>
          <tr><th>Endpoint</th><th>Vulnerabilidad</th><th>Modulo</th></tr>
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

app.get("/health", (_req, res) => res.json({ status: "ok", service: "mini-vulnerable-app" }));

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
  console.log(`CyberBank vulnerable target listening on ${port}`);
});
