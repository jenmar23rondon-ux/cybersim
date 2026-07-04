import type { Scenario } from "../types";

interface Props {
  scenarios: Scenario[];
  selected: string | null;
  running: boolean;
  onSelect: (id: string) => void;
  onLaunch: () => void;
}

export function ScenarioPanel({ scenarios, selected, running, onSelect, onLaunch }: Props) {
  const current = scenarios.find((s) => s.id === selected) || null;
  return (
    <div className="panel">
      <h2>Guided Scenario</h2>
      {scenarios.length === 0 && <p className="muted">Loading scenarios...</p>}
      {scenarios.map((s) => (
        <button
          key={s.id}
          className={`module ${selected === s.id ? "active" : ""}`}
          onClick={() => onSelect(s.id)}
        >
          <span className="name">{s.name}</span>
          <span className="desc">{s.description}</span>
          <span className="mitre">
            {s.steps.length} steps - {s.steps.map((x) => x.attack_type).join(" to ")}
          </span>
        </button>
      ))}

      {current && (
        <button className="btn" disabled={running} onClick={onLaunch}>
          {running ? "Running campaign..." : `Launch "${current.name}"`}
        </button>
      )}
      <p className="muted" style={{ marginTop: 8 }}>
        Runs every step in sequence against local targets, correlated under one campaign ID.
      </p>
    </div>
  );
}
