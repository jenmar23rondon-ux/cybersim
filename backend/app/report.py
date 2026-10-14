"""PDF report generator (fpdf2).

Produces an attack report with an executive summary, technical details, the
AI explanation, MITRE mapping, remediation steps, and the correlation ID used
by the SIEM.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fpdf import FPDF

from .analyst import analyst_review
from .defense import enrich_run
from .models import AttackRun

PRIMARY = (13, 71, 161)
DANGER = (198, 40, 40)
OK = (46, 125, 50)
GREY = (90, 90, 90)


class ReportPDF(FPDF):
    def header(self):
        self.set_fill_color(*PRIMARY)
        self.rect(0, 0, self.w, 22, "F")
        self.set_y(6)
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(255, 255, 255)
        self.cell(0, 10, "CyberSim - Attack Simulation Report", align="L")
        self.ln(18)
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(*GREY)
        self.cell(0, 10, f"CyberSim - ethical lab report - page {self.page_no()}", align="C")

    def h2(self, text: str):
        self.ln(2)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(*PRIMARY)
        self.cell(0, 8, text)
        self.ln(9)
        self.set_text_color(0, 0, 0)

    def kv(self, key: str, value: str):
        x = self.get_x()
        y = self.get_y()
        self.set_font("Helvetica", "B", 10)
        self.cell(45, 6, _s(f"{key}:"))
        self.set_xy(x + 45, y)
        self.set_font("Helvetica", "", 10)
        width = self.w - self.r_margin - self.get_x()
        self.multi_cell(max(width, 40), 6, _s(value), new_x="LMARGIN", new_y="NEXT")

    def body(self, text: str):
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 6, _s(text), new_x="LMARGIN", new_y="NEXT")
        self.ln(1)


def _s(v) -> str:
    """Latin-1 safe string for the core PDF fonts."""
    return str(v).encode("latin-1", "replace").decode("latin-1")


OUTCOMES = {
    "finding": "HALLAZGO CON EVIDENCIA",
    "simulation": "SIMULACIÓN COMPLETADA",
    "observation": "OBSERVACIÓN DE LABORATORIO",
    "no_finding": "SIN HALLAZGO EN ESTE ALCANCE",
    "inconclusive": "RESULTADO INCONCLUSO",
    "pending": "PRUEBA EN CURSO",
}


def analyst_section(pdf: ReportPDF, review: dict):
    with pdf.unbreakable():
        pdf.h2("Qué miraría un analista")
        pdf.body(f"1. Fuente del log: {review['log_source']}")
        pdf.body(f"2. Event ID / campo real: {review['event_reference']}")
        decision = review["decision"] or "Pendiente"
        pdf.body(f"3. Decisión: {decision}. {review['note']}")


def build_report(run: AttackRun) -> bytes:
    d = enrich_run(run.to_dict())
    exp = d.get("ai_explanation") or {}
    result = d.get("result") or {}
    status = d.get("status", "unknown")
    playbook = d["defense"]
    review = playbook["analyst_review"]

    pdf = ReportPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # --- Executive summary --------------------------------------------------
    pdf.h2("Executive Summary")
    color = DANGER if review["decision"] == "escalar" else OK
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*color)
    verdict = OUTCOMES[review["outcome"]]
    pdf.cell(0, 7, _s(f"Result: {verdict}"))
    pdf.ln(9)
    pdf.set_text_color(0, 0, 0)
    pdf.body(
        f"This report documents an ethical, lab-only simulation of a "
        f"{exp.get('title', d['attack_type'])} attack executed by CyberSim against the "
        f"lab target '{d['target']}'. {exp.get('what_it_does','')}"
    )

    # --- Attack metadata ----------------------------------------------------
    pdf.h2("Attack Details")
    pdf.kv("Attack type", d["attack_type"])
    pdf.kv("Target", d["target"])
    pdf.kv("Status", status)
    pdf.kv("Correlation ID", d["correlation_id"])
    pdf.kv("Started", d.get("started_at") or "-")
    pdf.kv("Finished", d.get("finished_at") or "-")
    mitre = exp.get("mitre") or {}
    if mitre:
        pdf.kv("MITRE ATT&CK", f"{mitre.get('id','')} - {mitre.get('name','')}")

    analyst_section(pdf, review)

    # --- Technical details --------------------------------------------------
    pdf.h2("Technical Details")
    pdf.body(f"Vulnerability exploited: {exp.get('vulnerability_exploited','n/a')}")
    for k, v in result.items():
        if k in ("success",):
            continue
        pdf.kv(str(k), v)

    # --- Remediation --------------------------------------------------------
    pdf.h2("Remediation Steps")
    remediation = exp.get("remediation") or []
    if remediation:
        for i, step in enumerate(remediation, 1):
            pdf.body(f"{i}. {step}")
    else:
        pdf.body("No remediation guidance available.")

    # --- Defensive operations ----------------------------------------------
    pdf.h2("SOC Detection Playbook")
    pdf.kv("Severity" if playbook["confirmed"] else "Potential severity", playbook["severity"].upper())
    pdf.kv("Risk score", f"{playbook['risk_score']}/100")
    pdf.kv("Business impact", playbook["business_impact"])
    pdf.kv("SecureWatch query", playbook["securewatch_query"])

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Detection signals:")
    pdf.ln(6)
    for item in playbook["detections"]:
        pdf.body(f"- {item}")

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Triage questions:")
    pdf.ln(6)
    for item in playbook["triage"]:
        pdf.body(f"- {item}")

    # --- SIEM correlation ---------------------------------------------------
    pdf.h2("SIEM Correlation (SecureWatch)")
    pdf.body(
        f"CyberSim recorded {len(d.get('logs') or [])} events with correlation ID "
        f"'{d['correlation_id']}'. If SecureWatch forwarding is configured, correlate "
        f"this ID with the original logs to verify receipt."
    )

    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*GREY)
    pdf.multi_cell(0, 5, _s(
        f"Generated by CyberSim on {datetime.now(timezone.utc).isoformat()}. "
        f"Explanation source: {exp.get('generated_by','offline')}. "
        "For authorized security education and defensive testing only."
    ))

    out = pdf.output()
    return bytes(out) if not isinstance(out, (bytes, bytearray)) else bytes(out)


def build_campaign_report(campaign: dict, runs: list[dict]) -> bytes:
    """Consolidated report for a guided-scenario campaign (multiple attacks)."""
    summary = campaign.get("summary") or {}
    status = campaign.get("status", "unknown")
    runs_by_cid = {r["correlation_id"]: r for r in runs}

    pdf = ReportPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # --- Executive summary --------------------------------------------------
    pdf.h2("Campaign Executive Summary")
    total = summary.get("total_steps", len(campaign.get("steps") or []))
    succeeded = sum(analyst_review(run)["outcome"] == "finding" for run in runs)
    color = DANGER if succeeded else OK
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(*color)
    pdf.cell(0, 7, f"Result: {succeeded}/{total} step(s) with finding evidence")
    pdf.ln(9)
    pdf.set_text_color(0, 0, 0)
    pdf.body(
        f"This report documents the guided scenario '{campaign.get('name')}', an "
        f"ethical, lab-only campaign run by CyberSim against isolated Docker targets. "
        f"It chained {total} attack step(s); {succeeded} provided finding evidence. "
        f"All activity is correlated under campaign ID "
        f"'{campaign.get('campaign_id')}' for SecureWatch SIEM matching."
    )

    pdf.kv("Scenario", campaign.get("scenario_id", "-"))
    pdf.kv("Campaign ID", campaign.get("campaign_id", "-"))
    pdf.kv("Status", status)
    pdf.kv("Started", campaign.get("started_at") or "-")
    pdf.kv("Finished", campaign.get("finished_at") or "-")

    # --- Per-step breakdown -------------------------------------------------
    for i, step in enumerate(campaign.get("steps") or [], 1):
        if pdf.will_page_break(75):
            pdf.add_page()
        pdf.h2(f"Step {i}: {step.get('attack_type')}  ->  {step.get('target')}")
        pdf.body(step.get("narrative", ""))
        step_status = step.get("status", "unknown")
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(*(OK if step_status == "success" else DANGER))
        pdf.cell(0, 6, f"Outcome: {step_status.upper()}")
        pdf.ln(8)
        pdf.set_text_color(0, 0, 0)

        run = runs_by_cid.get(step.get("correlation_id"))
        if run:
            exp = run.get("ai_explanation") or {}
            playbook = enrich_run(run.copy())["defense"]
            analyst_section(pdf, playbook["analyst_review"])
            if exp.get("vulnerability_exploited"):
                pdf.kv("Vulnerability", exp["vulnerability_exploited"])
            pdf.kv("Severity" if playbook["confirmed"] else "Potential severity", playbook["severity"].upper())
            pdf.kv("SecureWatch query", playbook["securewatch_query"])
            mitre = exp.get("mitre") or {}
            if mitre:
                pdf.kv("MITRE ATT&CK", f"{mitre.get('id','')} - {mitre.get('name','')}")
            remediation = exp.get("remediation") or []
            if remediation:
                pdf.set_font("Helvetica", "B", 10)
                pdf.cell(0, 6, "Remediation:")
                pdf.ln(6)
                for r in remediation:
                    pdf.body(f"- {r}")
        else:
            analyst_section(pdf, analyst_review({"attack_type": step.get("attack_type", ""),
                                                 "status": "running" if step_status == "pending" else step_status}))

    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(*GREY)
    pdf.multi_cell(0, 5, _s(
        f"Generated by CyberSim on {datetime.now(timezone.utc).isoformat()}. "
        "For authorized security education and defensive testing only."
    ))

    out = pdf.output()
    return bytes(out) if not isinstance(out, (bytes, bytearray)) else bytes(out)
