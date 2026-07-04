import { api } from "../api";

export function ReportButton({ correlationId, disabled }: { correlationId: string | null; disabled?: boolean }) {
  if (!correlationId) return null;
  return (
    <a
      className="btn ghost"
      href={api.reportUrl(correlationId)}
      target="_blank"
      rel="noreferrer"
      style={disabled ? { pointerEvents: "none", opacity: 0.5 } : undefined}
    >
      Download PDF Report
    </a>
  );
}
