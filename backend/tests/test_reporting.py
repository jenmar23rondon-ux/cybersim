import unittest

from app.analyst import WINDOWS_REFERENCES, analyst_review, log_reference
from app.attacks import REGISTRY
from app.defense import enrich_run
from app.models import AttackRun
from app.report import build_campaign_report, build_report
import pymupdf


def sample(attack="idor_audit", result=None, status="success", params=None, logs=None):
    return {"attack_type": attack, "status": status, "target": "lab.example",
            "correlation_id": "report-test", "params": params or {}, "logs": logs or [],
            "result": result if result is not None else {"success": True, "requester_id": 2, "returned_owner_id": 1}}


class ReportingTests(unittest.TestCase):
    def test_every_existing_module_has_log_guidance(self):
        for attack in REGISTRY:
            with self.subTest(attack=attack):
                source, reference = log_reference(attack, {})
                self.assertNotEqual(source, "Fuente pendiente de confirmar")
                self.assertTrue(reference)

    def test_web_tests_do_not_claim_windows_ids(self):
        for attack in ["sql_injection", "sqlmap_juice", "xss", "xss_advanced", "idor_audit", "authz_bypass", "bug_bounty_review"]:
            source, reference = log_reference(attack, {})
            self.assertEqual(source, "Aplicación web")
            self.assertIn("No aplica un Event ID de Windows", reference)
            self.assertNotRegex(reference, r"\b(?:4624|4625|4688|7045)\b")

    def test_http_brute_force_and_ssh_are_distinct(self):
        for attack, web, ssh in [("brute_force", {"mode": "http"}, {"mode": "ssh"}),
                                  ("hydra_bruteforce", {"profile": "juice_shop_login"}, {"profile": "weak_ssh"})]:
            self.assertIn("401 o 403 repetidos", log_reference(attack, web)[1])
            self.assertNotIn("4625", log_reference(attack, web)[1])
            self.assertEqual(log_reference(attack, ssh)[0], "Linux auth")

    def test_phishing_scan_and_malware_sources(self):
        self.assertIn("correo", log_reference("phishing_sim", {})[0])
        self.assertNotIn("4688", log_reference("phishing_sim", {})[1])
        self.assertIn("firewall", log_reference("port_scan", {})[0])
        self.assertIn("no es un login", log_reference("port_scan", {})[1])
        source, reference = log_reference("malware_sim", {})
        self.assertIn("Windows Security", source)
        self.assertIn("Windows System", source)
        self.assertIn("4688 solo si", reference)
        self.assertIn("7045 solo si", reference)
        self.assertIn("Sin Event ID confirmado", reference)

    def test_windows_reference_numbers_and_channels(self):
        expected = {"failed_logon": "4625", "successful_logon": "4624", "process_created": "4688",
                    "service_installed": "7045", "account_created": "4720", "password_reset": "4724",
                    "account_locked": "4740", "admin_logon": "4672 junto a 4624"}
        for name, number in expected.items():
            self.assertTrue(WINDOWS_REFERENCES[name][1].startswith(number))
            self.assertEqual(WINDOWS_REFERENCES[name][0], "Windows System" if name == "service_installed" else "Windows Security")

    def test_simulations_and_scans_are_not_confirmed_compromises(self):
        for attack in ["malware_sim", "rat_trojan_sim", "phishing_sim"]:
            run = enrich_run(sample(attack, {"success": True, "safe_simulation": True}))
            self.assertFalse(run["defense"]["confirmed"])
            self.assertEqual(run["defense"]["analyst_review"]["decision"], "cerrar como benign")
        run = enrich_run(sample("port_scan", {"success": True, "open_ports": [{"port": 443}]}))
        self.assertFalse(run["defense"]["confirmed"])

    def test_informational_bounty_note_does_not_confirm_vulnerability(self):
        review = analyst_review(sample("bug_bounty_review", {"success": True, "findings": [{"severity": "informational"}]}))
        self.assertEqual(review["decision"], "cerrar como false positive")

    def test_evidence_escalates_and_clean_check_can_close(self):
        self.assertEqual(analyst_review(sample())["decision"], "escalar")
        self.assertEqual(analyst_review(sample(result={"success": False}))["decision"], "cerrar como false positive")
        self.assertEqual(analyst_review(sample(result={"error": "timeout"}, status="failed"))["decision"], "escalar")
        self.assertEqual(analyst_review(sample(result={"success": False}, status="failed", logs=[{"level": "error"}]))["decision"], "escalar")
        self.assertIsNone(analyst_review(sample(status="running"))["decision"])

    def test_tool_banner_is_not_credential_or_sqli_evidence(self):
        for attack, result in [("hydra_bruteforce", {"success": True, "findings": ["[ssh] checking passwords"]}),
                               ("sqlmap_juice", {"success": True, "evidence": ["testing SQL injection"]})]:
            self.assertEqual(analyst_review(sample(attack, result))["outcome"], "inconclusive")

    def test_single_pdf_contains_three_analyst_lines(self):
        model = AttackRun(**sample())
        with pymupdf.open(stream=build_report(model), filetype="pdf") as document:
            text = "\n".join(page.get_text() for page in document)
        self.assertIn("Qué miraría un analista", text)
        self.assertIn("1. Fuente del log", text)
        self.assertIn("2. Event ID / campo real", text)
        self.assertIn("3. Decisión: escalar", text)
        self.assertIn("No aplica un Event ID de Windows", text)

    def test_campaign_pdf_has_guidance_for_each_step(self):
        run = sample("phishing_sim", {"success": True, "safe_simulation": True})
        campaign = {"name": "Existing lab drill", "steps": [
            {"attack_type": "phishing_sim", "status": "success", "correlation_id": run["correlation_id"]},
            {"attack_type": "idor_audit", "status": "pending", "correlation_id": None},
        ]}
        with pymupdf.open(stream=build_campaign_report(campaign, [run]), filetype="pdf") as document:
            text = "\n".join(page.get_text() for page in document)
        self.assertEqual(text.count("Qué miraría un analista"), 2)
        self.assertIn("cerrar como benign", text)
        self.assertIn("0/2 step(s) with finding evidence", text)


if __name__ == "__main__":
    unittest.main()
