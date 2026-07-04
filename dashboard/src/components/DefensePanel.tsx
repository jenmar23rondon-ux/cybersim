import type { DefensePlaybook, DefenseSummary } from "../types";

interface Props {
  playbook: DefensePlaybook | DefenseSummary | null;
}

export function DefensePanel({ playbook }: Props) {
  if (!playbook) {
    return (
      <div className="panel">
        <h2>Detection Lab</h2>
        <p className="muted">Select an attack to load SOC detection logic and remediation guidance.</p>
      </div>
    );
  }

  const confirmed = "confirmed" in playbook ? playbook.confirmed : false;
  const events = "event_count" in playbook ? playbook.event_count : null;

  return (
    <div className="panel defense">
      <div className="section-title">
        <h2>Detection Lab</h2>
        <div className="spacer" />
        <span className={`severity ${playbook.severity}`}>{playbook.severity}</span>
      </div>

      <div className="risk-row">
        <div>
          <span className="muted">Risk score</span>
          <strong>{playbook.risk_score}/100</strong>
        </div>
        <div>
          <span className="muted">Finding</span>
          <strong>{confirmed ? "Confirmed" : "Prepared"}</strong>
        </div>
        {events !== null && (
          <div>
            <span className="muted">Events</span>
            <strong>{events}</strong>
          </div>
        )}
      </div>

      <div className="block">
        <strong>Business impact</strong>
        <p>{playbook.business_impact}</p>
      </div>

      <div className="block">
        <strong>SecureWatch query</strong>
        <code>{playbook.securewatch_query}</code>
      </div>

      <ListBlock title="Detection signals" items={playbook.detections} />
      <ListBlock title="Triage questions" items={playbook.triage} />
      <ListBlock title="Remediation" items={playbook.remediation} />
    </div>
  );
}

function ListBlock({ title, items }: { title: string; items: string[] }) {
  if (!items.length) return null;
  return (
    <div className="block">
      <strong>{title}</strong>
      <ul>
        {items.map((item) => <li key={item}>{item}</li>)}
      </ul>
    </div>
  );
}
