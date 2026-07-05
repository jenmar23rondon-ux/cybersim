import type { RemediationGuide } from "../types";

export function RemediationLab({ guide }: { guide: RemediationGuide | null }) {
  if (!guide) {
    return (
      <div className="panel remediation">
        <h2>Remediation Lab</h2>
        <p className="muted">Select or open an attack to see the fix plan and validation checklist.</p>
      </div>
    );
  }

  return (
    <div className="panel remediation">
      <div className="section-title">
        <h2>Remediation Lab</h2>
        <div className="spacer" />
        <span className={`difficulty ${guide.difficulty}`}>{guide.difficulty}</span>
      </div>

      <div className="remedy-hero">
        <strong>{guide.title}</strong>
        <p>{guide.goal}</p>
      </div>

      {guide.applies_to.length > 0 && (
        <div className="remedy-block">
          <strong>Where to fix</strong>
          <div className="file-list">
            {guide.applies_to.map((item) => <code key={item}>{item}</code>)}
          </div>
        </div>
      )}

      <div className="remedy-grid">
        <Checklist title="Fix steps" items={guide.steps} />
        <Checklist title="Validate" items={guide.verify} />
      </div>

      {guide.secure_pattern && (
        <div className="remedy-block">
          <strong>Secure pattern</strong>
          <pre>{guide.secure_pattern}</pre>
        </div>
      )}
    </div>
  );
}

function Checklist({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="remedy-block">
      <strong>{title}</strong>
      <ul className="checklist">
        {items.map((item) => (
          <li key={item}>
            <span />
            {item}
          </li>
        ))}
      </ul>
    </div>
  );
}
