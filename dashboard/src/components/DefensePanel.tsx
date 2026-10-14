import type { DefensePlaybook, DefenseSummary } from "../types";
import { AnalystReview } from "./AnalystReview";

interface Props {
  playbook: DefensePlaybook | DefenseSummary | null;
  attackName?: string;
  running?: boolean;
}

export function DefensePanel({ playbook, attackName, running }: Props) {
  if (!playbook) {
    return (
      <div className="panel">
        <h2>Detection Lab</h2>
        <p className="muted">{attackName ? `Aún no se ha ejecutado ${attackName} en esta sesión.` : "Sin pruebas ejecutadas en esta sesión."}</p>
      </div>
    );
  }

  const confirmed = "confirmed" in playbook ? playbook.confirmed : false;
  const events = "event_count" in playbook ? playbook.event_count : null;
  const review = "analyst_review" in playbook ? playbook.analyst_review : null;
  const outcomeLabels = {
    finding: "Hallazgo con evidencia", simulation: "Simulación", observation: "Observación",
    no_finding: "Sin hallazgo", inconclusive: "Inconcluso", pending: "En curso",
  };

  return (
    <div className="panel defense">
      <div className="section-title">
        <h2>Detection Lab{attackName ? ` · ${attackName}` : ""}</h2>
        <div className="spacer" />
        {confirmed && <span className={`severity ${playbook.severity}`}>{playbook.severity}</span>}
      </div>

      <div className="risk-row">
        <div>
          <span className="muted">Risk score</span>
          <strong>{running ? "Pendiente" : `${playbook.risk_score}/100`}</strong>
        </div>
        <div>
          <span className="muted">Finding</span>
          <strong>{running ? "En curso" : review ? outcomeLabels[review.outcome] : "Pendiente de revisión"}</strong>
        </div>
        {events !== null && (
          <div>
            <span className="muted">Events</span>
            <strong>{events}</strong>
          </div>
        )}
      </div>

      {review && <AnalystReview review={review} />}

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
