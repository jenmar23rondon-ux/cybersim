import type { AttackRun } from "../types";
import { api } from "../api";
import { RotateCcw } from "lucide-react";

interface Props {
  runs: AttackRun[];
  onOpen: (run: AttackRun) => void;
  disabled?: boolean;
  onReset: () => void;
  resetting: boolean;
  resetDisabled: boolean;
  notice: { text: string; error?: boolean } | null;
}

export function HistoryPanel({ runs, onOpen, disabled, onReset, resetting, resetDisabled, notice }: Props) {
  return (
    <section className="panel history-panel" aria-labelledby="history-title">
      <div className="section-title history-heading">
        <h2 id="history-title">Attack History</h2>
        <button className="btn ghost compact history-reset" type="button" onClick={onReset}
          disabled={resetDisabled} aria-busy={resetting}
          title={disabled && !resetting ? "Wait for the current test to finish" : "Reset the reports shown in this session"}>
          <RotateCcw size={16} aria-hidden="true" />
          {resetting ? "Resetting..." : "Reset reports"}
        </button>
      </div>
      {notice && <p className={`history-notice ${notice.error ? "error" : ""}`} role={notice.error ? "alert" : "status"}>{notice.text}</p>}
      {runs.length === 0 && <p className="muted">No hay informes en esta sesión.</p>}
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
    </section>
  );
}
