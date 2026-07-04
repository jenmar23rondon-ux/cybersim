/* =============================================================================
 *  Vulnerable Node.js API  —  CyberSim lab target
 *
 *  This service is INTENTIONALLY insecure. It exists so CyberSim's attack
 *  modules have a safe, disposable target inside the isolated Docker network.
 *  NEVER expose this to a real network or deploy it anywhere public.
 *
 *  Simulated vulnerabilities:
 *    - SQL injection (string-concatenated query, emulated in-memory DB)
 *    - Reflected XSS (unescaped echo)
 *    - Weak authentication / brute-forceable login (no rate limiting)
 * ========================================================================== */

const express = require("express");
const app = express();
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// ---- Fake "database" -------------------------------------------------------
const USERS = [
  { id: 1, username: "admin", password: "admin123", role: "administrator", secret: "FLAG{sqli_dumped_admin}" },
  { id: 2, username: "alice", password: "password", role: "user", secret: "alice-private-note" },
  { id: 3, username: "bob", password: "letmein", role: "user", secret: "bob-private-note" },
];

/**
 * Emulates a naive, injectable query. We DON'T run a real SQL engine — instead
 * we detect classic injection patterns and mimic how a vulnerable string-built
 * query would behave (auth bypass, UNION-style dump), so the demo is safe and
 * deterministic.
 */
function vulnerableUserLookup(rawInput) {
  const query = `SELECT * FROM users WHERE username = '${rawInput}'`;
  const injection = /'|--|\bOR\b|\bUNION\b|=/i.test(rawInput);
  let rows;
  if (/UNION/i.test(rawInput) || /OR\s+'?1'?\s*=\s*'?1/i.test(rawInput)) {
    rows = USERS; // classic "return everything" injection
  } else {
    rows = USERS.filter((u) => u.username === rawInput);
  }
  return { query, injected: injection, rows };
}

app.get("/", (_req, res) => {
  res.json({
    service: "vuln-node-api",
    warning: "Intentionally vulnerable lab target. Local use only.",
    endpoints: ["/api/user?username=", "/api/login", "/api/search?q=", "/health"],
  });
});

app.get("/health", (_req, res) => res.json({ status: "ok" }));

// ---- SQL Injection endpoint -----------------------------------------------
app.get("/api/user", (req, res) => {
  const username = String(req.query.username || "");
  const result = vulnerableUserLookup(username);
  res.json({
    executed_query: result.query,       // leaks the query — helps the demo
    injection_detected: result.injected,
    count: result.rows.length,
    rows: result.rows,
  });
});

// ---- Weak authentication (brute-forceable) --------------------------------
app.post("/api/login", (req, res) => {
  const { username, password } = req.body || {};
  const user = USERS.find((u) => u.username === username && u.password === password);
  // No rate limiting, no lockout, verbose errors -> brute force friendly.
  if (user) {
    return res.json({ success: true, role: user.role, token: `demo-${user.id}` });
  }
  return res.status(401).json({ success: false, error: "Invalid credentials" });
});

// ---- Reflected XSS endpoint -----------------------------------------------
app.get("/api/search", (req, res) => {
  const q = String(req.query.q || "");
  // Unescaped reflection of user input into HTML.
  res.set("Content-Type", "text/html");
  res.send(`<html><body><h1>Results for: ${q}</h1><p>No results found.</p></body></html>`);
});

const PORT = 3001;
app.listen(PORT, () => console.log(`vuln-node-api listening on ${PORT}`));
