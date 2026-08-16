import type { DefensePlaybook, DefenseSummary, LogEvent, RemediationGuide } from "../types";

interface Props {
  events: LogEvent[];
  defense: DefensePlaybook | DefenseSummary | null;
  remediation: RemediationGuide | null;
}

const ATTACK_LABELS: Record<string, string> = {
  idor_audit: "IDOR",
  authz_bypass: "bypass de autorizacion",
  sql_injection: "SQL injection",
  xss: "XSS reflejado",
  xss_advanced: "XSS reflejado/almacenado",
  bug_bounty_review: "revision bug bounty read-only",
  malware_sim: "malware behavior simulation",
  rat_trojan_sim: "RAT/troyano simulado",
  phishing_sim: "phishing simulation",
};

export function LiveNarrative({ events, defense, remediation }: Props) {
  const latest = events[events.length - 1];
  const first = events[0];
  const attack = first?.attack_type || defense?.attack_type || remediation?.attack_type || "";
  const successes = events.filter((event) => event.level === "success");
  const warnings = events.filter((event) => event.level === "warn");
  const final = events.find((event) => event.data?.final);

  const whatHappened = final
    ? `La prueba termino en estado ${String(final.data?.status || "desconocido").toUpperCase()}.`
    : latest
      ? latest.message
      : "Esperando eventos para narrar el ataque paso a paso.";

  const evidence = successes[successes.length - 1]?.message || warnings[warnings.length - 1]?.message || "Aun no hay evidencia confirmada.";
  const reinforce = remediation?.steps?.[0] || defense?.remediation?.[0] || "Cuando termine la prueba, aplica el plan de remediacion recomendado.";

  return (
    <div className="narrative">
      <div className="narrative-row">
        <span>Que pasa</span>
        <strong>{whatHappened}</strong>
      </div>
      <div className="narrative-row">
        <span>Con que se probo</span>
        <strong>{attack ? ATTACK_LABELS[attack] || attack : "Sin modulo activo"}</strong>
      </div>
      <div className="narrative-row">
        <span>Evidencia</span>
        <strong>{evidence}</strong>
      </div>
      <div className="narrative-row">
        <span>Se refuerza con</span>
        <strong>{reinforce}</strong>
      </div>
    </div>
  );
}
