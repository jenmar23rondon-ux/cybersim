import type { AttackRun, Campaign, DefensePlaybook, DefenseSummary, LogEvent, Metrics } from "../types";

type ImpactState = "affected" | "watch" | "clear";

interface AssetImpact {
  id: string;
  label: string;
  detail: string;
  state: ImpactState;
  confidence: number;
}

interface Props {
  metrics: Metrics | null;
  history: AttackRun[];
  events: LogEvent[];
  selectedAttack: string | null;
  defense: DefensePlaybook | DefenseSummary | null;
  campaign: Campaign | null;
  isCampaign: boolean;
}

const ASSETS = [
  { id: "network", label: "Network Surface", detail: "Open ports, reachable services, Docker exposure." },
  { id: "api", label: "Application API", detail: "Routes, parameters, and server-side request handling." },
  { id: "auth", label: "Authentication", detail: "Login controls, passwords, lockout, and SSH access." },
  { id: "database", label: "Database/Data", detail: "Rows, secrets, balances, and query behavior." },
  { id: "browser", label: "Browser/Session", detail: "Client-side script execution and session safety." },
  { id: "availability", label: "Availability", detail: "Latency, errors, and service responsiveness." },
  { id: "endpoint", label: "Endpoint Fleet", detail: "Workstations, processes, persistence, and local file activity." },
  { id: "email", label: "Email/Identity", detail: "Inbox security, user reports, MFA prompts, and account takeover risk." },
];

const ATTACK_ASSETS: Record<string, string[]> = {
  port_scan: ["network"],
  sql_injection: ["api", "database", "auth"],
  sqlmap_juice: ["api", "database"],
  brute_force: ["auth"],
  hydra_bruteforce: ["auth"],
  xss: ["browser", "api"],
  ddos_sim: ["availability"],
  malware_sim: ["endpoint", "auth", "database"],
  phishing_sim: ["email", "auth", "browser"],
};

export function ImpactMap({ metrics, history, events, selectedAttack, defense, campaign, isCampaign }: Props) {
  const activeAttacks = getActiveAttacks({ selectedAttack, events, campaign, isCampaign });
  const confirmedAttacks = new Set(
    activeAttacks.filter((item) => item.status === "success").map((item) => item.attack)
  );
  const watchedAttacks = new Set(activeAttacks.map((item) => item.attack));
  const affectedAssetIds = new Set<string>();
  const watchedAssetIds = new Set<string>();

  for (const attack of confirmedAttacks) {
    for (const asset of ATTACK_ASSETS[attack] || ["api"]) affectedAssetIds.add(asset);
  }
  for (const attack of watchedAttacks) {
    for (const asset of ATTACK_ASSETS[attack] || ["api"]) watchedAssetIds.add(asset);
  }

  const impacts: AssetImpact[] = ASSETS.map((asset) => {
    const state: ImpactState = affectedAssetIds.has(asset.id)
      ? "affected"
      : watchedAssetIds.has(asset.id)
        ? "watch"
        : "clear";
    return {
      ...asset,
      state,
      confidence: state === "affected" ? 92 : state === "watch" ? 58 : 18,
    };
  });

  const affected = impacts.filter((item) => item.state === "affected").length;
  const watched = impacts.filter((item) => item.state === "watch").length;
  const clear = impacts.filter((item) => item.state === "clear").length;
  const maxAttackCount = Math.max(1, ...Object.values(metrics?.attack_counts || {}));
  const statusCounts = metrics?.status_counts || {};
  const totalStatus = Math.max(1, Object.values(statusCounts).reduce((sum, value) => sum + value, 0));
  const risk = defense?.risk_score ?? metrics?.average_risk_score ?? 0;
  const latest = history[0];

  return (
    <div className="panel impact">
      <div className="section-title">
        <h2>Impact Map</h2>
        <div className="spacer" />
        <span className={`impact-score ${risk >= 80 ? "danger" : risk >= 55 ? "warn" : "ok"}`}>
          Risk {risk}/100
        </span>
      </div>

      <div className="impact-summary">
        <ImpactSummary label="Affected" value={affected} tone="danger" />
        <ImpactSummary label="Under watch" value={watched} tone="warn" />
        <ImpactSummary label="No evidence" value={clear} tone="ok" />
      </div>

      <div className="asset-grid">
        {impacts.map((asset) => (
          <div className={`asset-card ${asset.state}`} key={asset.id}>
            <div className="asset-head">
              <strong>{asset.label}</strong>
              <span>{labelFor(asset.state)}</span>
            </div>
            <p>{asset.detail}</p>
            <div className="confidence">
              <div style={{ width: `${asset.confidence}%` }} />
            </div>
          </div>
        ))}
      </div>

      <div className="chart-grid">
        <div className="mini-chart">
          <strong>Run status</strong>
          {["success", "failed", "running"].map((status) => {
            const value = statusCounts[status] || 0;
            return (
              <div className="chart-row" key={status}>
                <span>{status}</span>
                <div><i style={{ width: `${(value / totalStatus) * 100}%` }} /></div>
                <b>{value}</b>
              </div>
            );
          })}
        </div>

        <div className="mini-chart">
          <strong>Attack coverage</strong>
          {Object.entries(metrics?.attack_counts || {}).slice(0, 5).map(([attack, count]) => (
            <div className="chart-row" key={attack}>
              <span>{attack}</span>
              <div><i style={{ width: `${(count / maxAttackCount) * 100}%` }} /></div>
              <b>{count}</b>
            </div>
          ))}
          {!Object.keys(metrics?.attack_counts || {}).length && (
            <p className="muted">Run an attack to populate coverage.</p>
          )}
        </div>
      </div>

      <div className="impact-note">
        <strong>{latest ? `Latest: ${latest.attack_type} -> ${latest.target}` : "Waiting for first run"}</strong>
        <span>
          {isCampaign && campaign
            ? `Campaign ${campaign.name} is ${campaign.status}.`
            : "Open a history item or launch an attack to refresh the affected areas."}
        </span>
      </div>
    </div>
  );
}

function ImpactSummary({ label, value, tone }: { label: string; value: number; tone: string }) {
  return (
    <div className={`impact-kpi ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function labelFor(state: ImpactState) {
  if (state === "affected") return "Affected";
  if (state === "watch") return "Watched";
  return "No evidence";
}

function getActiveAttacks({
  selectedAttack,
  events,
  campaign,
  isCampaign,
}: Pick<Props, "selectedAttack" | "events" | "campaign" | "isCampaign">) {
  if (isCampaign && campaign?.steps?.length) {
    return campaign.steps.map((step) => ({ attack: step.attack_type, status: step.status }));
  }
  if (events.length) {
    const final = events.find((event) => event.data?.final);
    return [{ attack: events[0].attack_type, status: final?.data?.status || "running" }];
  }
  return selectedAttack ? [{ attack: selectedAttack, status: "prepared" }] : [];
}
