import type { AttackModule } from "../types";

interface Props {
  modules: AttackModule[];
  selected: string | null;
  onSelect: (id: string) => void;
}

export function AttackSelector({ modules, selected, onSelect }: Props) {
  return (
    <div className="panel">
      <h2>1 · Select Attack</h2>
      {modules.length === 0 && <p className="muted">Loading modules…</p>}
      {modules.map((m) => (
        <button
          key={m.id}
          className={`module ${selected === m.id ? "active" : ""}`}
          onClick={() => onSelect(m.id)}
        >
          <span className="name">{m.name}</span>
          <span className="desc">{m.description}</span>
          <span className="mitre">MITRE {m.mitre}</span>
        </button>
      ))}
    </div>
  );
}
