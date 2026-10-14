import type { AttackRun } from "../types";
import { api } from "../api";

interface Props {
  runs: AttackRun[];
  onOpen: (run: AttackRun) => void;
  disabled?: boolean;
}

export function HistoryPanel({ runs, onOpen, disabled }: Props) {
  return (
    <div className="panel">
      <h2>Attack History</h2>
      {runs.length === 0 && <p className="muted">No attacks yet.</p>}
      {runs.map((r) => (
        <div className="hist-row" key={r.id}>
          <button className="history-open" type="button" disabled={disabled} onClick={() => onOpen(r)}
            aria-label={`Abrir resultado de ${r.attack_type}`}>
            <div className="type">{r.attack_type}</div>
            <div className="meta">
              {r.target} - {r.started_at ? new Date(r.started_at).toLocaleString() : ""}
            </div>
            {r.defense && (
              <div className="meta">
                Risk {r.defense.risk_score}/100 · {r.defense.analyst_review?.decision || "Pendiente de revisión"}
              </div>
            )}
          </button>
          <div className="spacer" />
          <span className={`pill ${r.status}`}>{r.status}</span>
          <a
            className="btn ghost"
            style={{ width: "auto", margin: 0, padding: "6px 10px", fontSize: 12 }}
            href={api.reportUrl(r.correlation_id)}
            target="_blank"
            rel="noreferrer"
            onClick={(e) => e.stopPropagation()}
          >
            PDF
          </a>
        </div>
      ))}
    </div>
  );
}
