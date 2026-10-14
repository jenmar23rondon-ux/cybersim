"""Evidence-based reporting only; never changes how a test executes."""

from __future__ import annotations

import re
from typing import Any


# These are references, not events observed by the Docker lab.
WINDOWS_REFERENCES = {
    "failed_logon": ("Windows Security", "4625: inicio de sesión fallido"),
    "successful_logon": ("Windows Security", "4624: inicio de sesión correcto"),
    "process_created": ("Windows Security", "4688: proceso nuevo, solo si se abrió un programa"),
    "service_installed": ("Windows System", "7045: servicio nuevo, solo si se instaló un servicio"),
    "account_created": ("Windows Security", "4720: cuenta nueva"),
    "password_reset": ("Windows Security", "4724: contraseña reiniciada por otra persona"),
    "account_locked": ("Windows Security", "4740: cuenta bloqueada"),
    "admin_logon": ("Windows Security", "4672 junto a 4624: privilegios especiales en la misma sesión"),
}

SIMULATIONS = {"malware_sim", "rat_trojan_sim", "phishing_sim"}
WEB_TESTS = {"sql_injection", "sqlmap_juice", "xss", "xss_advanced", "idor_audit", "authz_bypass", "bug_bounty_review"}


def log_reference(attack_type: str, params: dict[str, Any]) -> tuple[str, str]:
    no_windows_id = "No aplica un Event ID de Windows. "
    if attack_type in {"brute_force", "hydra_bruteforce"}:
        ssh = (params.get("mode", "http") == "ssh" if attack_type == "brute_force"
               else params.get("profile", "weak_ssh") == "weak_ssh")
        if ssh:
            return "Linux auth", no_windows_id + "Revisar usuario, IP, hora y mensajes de sshd de autenticación fallida o aceptada."
        return "Aplicación web", no_windows_id + "Revisar HTTP 401 o 403 repetidos, usuario, IP y hora; correlacionar un acceso correcto posterior."
    if attack_type in WEB_TESTS:
        return "Aplicación web", no_windows_id + "Revisar código HTTP, ruta, usuario, IP, hora y respuesta; en IDOR, comparar solicitante con propietario."
    if attack_type == "phishing_sim":
        return "Log de correo (modelado en la simulación)", no_windows_id + "Revisar remitente, destinatario, mensaje, enlace y hora. No hay logs de procesos o accesos Windows adjuntos."
    if attack_type == "port_scan":
        return "Log del firewall (a correlacionar con el resultado del escaneo)", no_windows_id + "Revisar IP origen/destino, puerto, protocolo, acción y hora; un puerto abierto no es un login."
    if attack_type in {"malware_sim", "rat_trojan_sim"}:
        return (
            "Aplicación web (telemetría simulada); Windows Security y Windows System solo para correlación",
            "Sin Event ID confirmado en esta prueba. Windows Security: 4688 solo si se abrió un proceso; "
            "Windows System: 7045 solo si se instaló un servicio. Revisar host, usuario, proceso/servicio y hora; "
            "los indicadores simulados no acreditan esos eventos.",
        )
    if attack_type == "ddos_sim":
        return "Aplicación web", no_windows_id + "Revisar código HTTP, IP, hora, volumen, latencia y errores."
    return "Fuente pendiente de confirmar", "sin Event ID confirmado; revisar usuario, IP y hora en el log original."


def finding_outcome(run: dict[str, Any]) -> tuple[str, str]:
    attack = run.get("attack_type", "")
    result = run.get("result") or {}
    if run.get("status") == "running":
        return "pending", "Prueba en curso; todavía no hay una conclusión."
    if result.get("error"):
        return "inconclusive", "La prueba devolvió un error; revisar conectividad y evidencia antes de cerrar."
    if attack in SIMULATIONS:
        if result.get("safe_simulation") is True:
            return "simulation", "Simulación autorizada del laboratorio; la telemetría modelada no confirma un incidente real."
        return "inconclusive", "No se confirmó el resultado de la simulación; revisar el registro original."
    if attack == "port_scan":
        if "open_ports" in result:
            return "observation", "Escaneo autorizado: los puertos observados requieren revisión de exposición, no acreditan un login o compromiso."
        return "inconclusive", "Sin resultado de puertos; revisar el escaneo y el firewall."
    if attack == "ddos_sim":
        if result.get("latency_degraded") or result.get("errors", 0) > 0:
            return "finding", "La prueba registró degradación o errores; revisar disponibilidad y límites del servicio."
        if result.get("requests_sent") and result.get("success"):
            return "observation", "Prueba de carga autorizada completada sin degradación registrada."
        return "inconclusive", "Sin mediciones suficientes para evaluar disponibilidad."

    evidence = False
    if attack == "idor_audit":
        evidence = (result.get("success") is True and result.get("returned_owner_id") is not None
                    and result.get("requester_id") != result.get("returned_owner_id"))
    elif attack == "authz_bypass":
        evidence = result.get("baseline_status") == 403 and result.get("bypass_status") == 200 and result.get("success") is True
    elif attack == "sql_injection":
        evidence = bool(result.get("working_payloads"))
    elif attack == "xss":
        evidence = bool(result.get("reflected_payloads"))
    elif attack == "xss_advanced":
        evidence = bool(result.get("findings"))
    elif attack == "bug_bounty_review":
        evidence = any(item.get("severity") in {"low", "medium", "high", "critical"}
                       for item in result.get("findings", []) if isinstance(item, dict))
    elif attack == "brute_force":
        evidence = bool(result.get("credentials_found"))
    elif attack == "hydra_bruteforce":
        evidence = any(re.search(r"login:\s*\S+.*password:\s*\S+", line, re.I)
                       for line in result.get("findings", []) if isinstance(line, str))
    elif attack == "sqlmap_juice":
        evidence = any(re.search(r"(?:is vulnerable|is .*injectable|identified the following injection point)", line, re.I)
                       for line in result.get("evidence", []) if isinstance(line, str))
    else:
        return "inconclusive", "Sin criterio de evidencia confirmado para esta prueba; requiere revisión manual."

    if evidence:
        note = ("Se observó contenido sin escapar; revisar el contexto y confirmar por separado la ejecución en navegador."
                if attack in {"xss", "xss_advanced"}
                else "La prueba aportó evidencia de un hallazgo; revisar alcance y remediación con el responsable.")
        return "finding", note
    if any(event.get("level") == "error" for event in run.get("logs") or []):
        return "inconclusive", "Hubo errores durante la prueba; la ausencia de hallazgos no permite cerrar la alerta."
    if not result or result.get("exit_code", 0) != 0:
        return "inconclusive", "El resultado está incompleto o la herramienta falló; revisar antes de cerrar."
    if attack in {"hydra_bruteforce", "sqlmap_juice"} and result.get("success"):
        return "inconclusive", "La herramienta indicó éxito, pero falta evidencia específica que lo confirme."
    return "no_finding", "La prueba terminó sin evidencia que sostenga la alerta en este alcance; no certifica la seguridad del sistema."


def analyst_review(run: dict[str, Any]) -> dict[str, Any]:
    source, reference = log_reference(run.get("attack_type", ""), run.get("params") or {})
    outcome, note = finding_outcome(run)
    decision = {
        "finding": "escalar",
        "inconclusive": "escalar",
        "simulation": "cerrar como benign",
        "observation": "cerrar como benign",
        "no_finding": "cerrar como false positive",
        "pending": None,
    }[outcome]
    return {"log_source": source, "event_reference": reference, "decision": decision,
            "note": note, "outcome": outcome}
