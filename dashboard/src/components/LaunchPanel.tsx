import { useEffect, useState } from "react";
import type { AttackModule } from "../types";

interface Props {
  module: AttackModule | null;
  launching: boolean;
  onLaunch: (target: string, params: Record<string, any>) => void;
}

export function LaunchPanel({ module, launching, onLaunch }: Props) {
  const [target, setTarget] = useState("");
  const [params, setParams] = useState<Record<string, any>>({});

  useEffect(() => {
    if (!module) return;
    setTarget(module.default_target);
    const defaults: Record<string, any> = {};
    for (const [k, spec] of Object.entries(module.params_schema || {})) {
      defaults[k] = (spec as any).default;
    }
    setParams(defaults);
  }, [module]);

  if (!module) {
    return (
      <div className="panel">
        <h2>2. Configure &amp; Launch</h2>
        <p className="muted">Select an attack module to configure it.</p>
      </div>
    );
  }

  const setParam = (k: string, v: any) => setParams((p) => ({ ...p, [k]: v }));

  return (
    <div className="panel">
      <h2>2. Configure &amp; Launch</h2>

      <label>Target (local lab container)</label>
      <input value={target} onChange={(e) => setTarget(e.target.value)} />

      {Object.entries(module.params_schema || {}).map(([key, spec]) => {
        const s = spec as any;
        const val = params[key] ?? s.default;
        if (s.type === "select") {
          return (
            <div key={key}>
              <label>{s.label || key}</label>
              <select value={val} onChange={(e) => setParam(key, e.target.value)}>
                {(s.options || []).map((o: string) => (
                  <option key={o} value={o}>{o}</option>
                ))}
              </select>
            </div>
          );
        }
        if (s.type === "list") {
          return (
            <div key={key}>
              <label>{s.label || key} (comma-separated)</label>
              <textarea
                value={Array.isArray(val) ? val.join(", ") : val}
                onChange={(e) =>
                  setParam(key, e.target.value.split(",").map((x) => x.trim()).filter(Boolean))
                }
              />
            </div>
          );
        }
        return (
          <div key={key}>
            <label>{s.label || key}</label>
            <input
              type={s.type === "int" ? "number" : "text"}
              value={val ?? ""}
              onChange={(e) =>
                setParam(key, s.type === "int" ? Number(e.target.value) : e.target.value)
              }
            />
          </div>
        );
      })}

      <button className="btn" disabled={launching || !target} onClick={() => onLaunch(target, params)}>
        {launching ? "Running..." : "Launch Attack"}
      </button>
      <p className="muted" style={{ marginTop: 8 }}>
        Attacks run only against allowlisted local containers.
      </p>
    </div>
  );
}
