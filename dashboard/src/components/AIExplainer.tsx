import type { AIExplanation } from "../types";

export function AIExplainer({ explanation }: { explanation: AIExplanation | null }) {
  if (!explanation) {
    return <p className="muted">The AI explanation appears here when the attack finishes.</p>;
  }
  const e = explanation;
  return (
    <div className="ai">
      {e.title && <h3>{e.title}</h3>}

      {e.what_it_does && (
        <div className="block">
          <strong>What it does</strong>
          <p>{e.what_it_does}</p>
        </div>
      )}

      {e.vulnerability_exploited && (
        <div className="block">
          <strong>Vulnerability exploited</strong>
          <p>{e.vulnerability_exploited}</p>
        </div>
      )}

      {e.mitre?.id && (
        <div className="block">
          <strong>MITRE ATT&amp;CK</strong>
          <div style={{ marginTop: 6 }}>
            <span className="mitre-chip">
              {e.mitre.id} - {e.mitre.name}
            </span>
          </div>
        </div>
      )}

      {e.remediation && e.remediation.length > 0 && (
        <div className="block">
          <strong>How to fix it</strong>
          <ul>
            {e.remediation.map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        </div>
      )}

      <p className="muted">
        Explanation source: {e.generated_by || "offline"}
        {e.note ? ` - ${e.note}` : ""}
      </p>
    </div>
  );
}
