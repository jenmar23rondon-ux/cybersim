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

interface Props {
  cloudTargetUrl?: string;
  onUseCloudTarget?: (target: { host: string; port: number; scheme: string }) => void;
}

export function TargetShowcase({ cloudTargetUrl, onUseCloudTarget }: Props) {
  const cloud = parseTargetUrl(cloudTargetUrl);
  const primaryUrl = cloud?.origin || "http://localhost:3003";
  const primarySoc = `${primaryUrl}/security`;

  return (
    <div className="showcase">
      <div className="panel vulnerable-face">
        <div className="section-title">
          <h2>{cloud ? "Cloud Docker Target" : "Vulnerable Face"}</h2>
          <div className="spacer" />
          <a className="mini-link" href="http://localhost:3002" target="_blank" rel="noreferrer">
            Open Juice Shop
          </a>
          <a className="mini-link" href={primaryUrl} target="_blank" rel="noreferrer">
            Open CyberBank
          </a>
          <a className="mini-link" href={primarySoc} target="_blank" rel="noreferrer">
            Open SOC
          </a>
        </div>
        {cloud && (
          <div className="cloud-flow">
            <div>
              <strong>CyberSim attacker</strong>
              <span>localhost:5173</span>
            </div>
            <b>→</b>
            <div className="active">
              <strong>Railway Docker</strong>
              <span>{cloud.host}</span>
            </div>
            <b>→</b>
            <div>
              <strong>CyberBank SOC</strong>
              <span>/security</span>
            </div>
          </div>
        )}
        <div className="target-browser">
          <div className="browser-bar">
            <span />
            <span />
            <span />
            <code>{primaryUrl}</code>
          </div>
          <div className="browser-body">
            <strong>
              {cloud
                ? "CyberBank is running as your Railway Docker target."
                : "CyberBank Mini App is running as a vulnerable Docker target."}
            </strong>
            <p>
              {cloud
                ? "Use the cloud target for safe phishing and malware-behavior drills so other people can see the target SOC update outside your local machine."
                : "Open it in a second tab or side-by-side window while CyberSim runs SQL injection, XSS, brute force, scans, and bounded load tests from the attack console."}
            </p>
            <div className="target-actions">
              <a href={primaryUrl} target="_blank" rel="noreferrer">
                Open target app
              </a>
              <a href={primarySoc} target="_blank" rel="noreferrer">
                Open target SOC
              </a>
              {cloud && onUseCloudTarget && (
                <button
                  type="button"
                  onClick={() => onUseCloudTarget({ host: cloud.host, port: cloud.port, scheme: cloud.scheme })}
                >
                  Use cloud target
                </button>
              )}
            </div>
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

function parseTargetUrl(value?: string) {
  if (!value) return null;
  try {
    const parsed = new URL(value);
    const scheme = parsed.protocol.replace(":", "") || "https";
    const port = parsed.port ? Number(parsed.port) : scheme === "https" ? 443 : 80;
    return {
      origin: parsed.origin,
      host: parsed.hostname,
      port,
      scheme,
    };
  } catch {
    return null;
  }
}
