import type { Metrics } from "../types";

export function MetricsStrip({ metrics }: { metrics: Metrics | null }) {
  const total = metrics?.total_runs ?? 0;
  const confirmed = metrics?.confirmed_findings ?? 0;
  const campaigns = metrics?.campaigns ?? 0;
  const risk = metrics?.average_risk_score ?? 0;

  return (
    <div className="metrics-strip">
      <Metric label="Runs" value={total} />
      <Metric label="Confirmed findings" value={confirmed} tone="warn" />
      <Metric label="Campaigns" value={campaigns} />
      <Metric label="Avg risk" value={risk} tone={risk >= 70 ? "danger" : risk >= 45 ? "warn" : "ok"} />
    </div>
  );
}

function Metric({ label, value, tone = "plain" }: { label: string; value: string | number; tone?: string }) {
  return (
    <div className={`metric ${tone}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}
