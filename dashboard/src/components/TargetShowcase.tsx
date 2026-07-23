const TARGETS = [
  {
    name: "CyberBank Mini App",
    url: "http://localhost:3003",
    container: "mini-vuln-app:3003",
    purpose: "Visual mini target for live SQLi, XSS, brute force, scans, and fix demos.",
  },
  {
    name: "OWASP Juice Shop",
    url: "http://localhost:3002",
    container: "juice-shop:3000",
    purpose: "Recognized vulnerable web app for SQLi, XSS, auth, and training demos.",
  },
  {
    name: "Vulnerable Node API",
    url: "http://localhost:3001",
    container: "vuln-node-api:3001",
    purpose: "Small custom API used by CyberSim's built-in SQLi, XSS, and auth demos.",
  },
  {
    name: "DVWA",
    url: "http://localhost:4280",
    container: "dvwa:80",
    purpose: "Classic vulnerable web application for manual practice.",
  },
];

export function TargetShowcase() {
  return (
    <div className="showcase">
      <div className="panel vulnerable-face">
        <div className="section-title">
          <h2>Vulnerable Face</h2>
          <div className="spacer" />
          <a className="mini-link" href="http://localhost:3002" target="_blank" rel="noreferrer">
            Open Juice Shop
          </a>
          <a className="mini-link" href="http://localhost:3003" target="_blank" rel="noreferrer">
            Open CyberBank
          </a>
          <a className="mini-link" href="http://localhost:3003/security" target="_blank" rel="noreferrer">
            Open SOC
          </a>
        </div>
        <div className="target-browser">
          <div className="browser-bar">
            <span />
            <span />
            <span />
            <code>http://localhost:3003</code>
          </div>
          <div className="browser-body">
            <strong>CyberBank Mini App is running as a vulnerable Docker target.</strong>
            <p>
              Open it in a second tab or side-by-side window while CyberSim runs
              SQL injection, XSS, brute force, scans, and bounded load tests from
              the attack console.
            </p>
            <a href="http://localhost:3003" target="_blank" rel="noreferrer">
              Open live vulnerable app
            </a>
            <a href="http://localhost:3003/security" target="_blank" rel="noreferrer">
              Open interactive SOC
            </a>
          </div>
        </div>
      </div>

      <div className="panel target-list">
        <h2>Lab Targets</h2>
        {TARGETS.map((target) => (
          <a className="target-card" href={target.url} target="_blank" rel="noreferrer" key={target.name}>
            <strong>{target.name}</strong>
            <span>{target.purpose}</span>
            <code>{target.container}</code>
          </a>
        ))}
        <div className="tool-note">
          <strong>Toolkit container</strong>
          <span>Manual demo shell: docker exec -it cybersim-attacker-tools bash</span>
          <code>sqlmap / hydra / nmap / curl / jq</code>
        </div>
      </div>
    </div>
  );
}
