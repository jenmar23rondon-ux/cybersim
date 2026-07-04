const TARGETS = [
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
        </div>
        <div className="target-browser">
          <div className="browser-bar">
            <span />
            <span />
            <span />
            <code>http://localhost:3002</code>
          </div>
          <div className="browser-body">
            <strong>OWASP Juice Shop is running as the vulnerable app.</strong>
            <p>
              Open it in a second tab or side-by-side window while CyberSim runs
              sqlmap, hydra, scans, and bounded load tests from the attack console.
            </p>
            <a href="http://localhost:3002" target="_blank" rel="noreferrer">
              Open live vulnerable app
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
