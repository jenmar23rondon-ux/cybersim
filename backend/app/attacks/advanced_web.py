"""Advanced safe web-attack modules for the CyberBank lab target.

These modules only verify intentionally vulnerable routes in the owned lab
Docker target. They do not attack third-party services and they do not include
malware payloads.
"""

from __future__ import annotations

import asyncio
import html

import httpx

from .base import AttackModuleBase, Emit, register


def _target_origin(target: str, params: dict, default_port: int = 3003) -> str:
    scheme = str(params.get("scheme", "http")).lower()
    port = int(params.get("port", 443 if scheme == "https" else default_port))
    standard = 443 if scheme == "https" else 80
    suffix = "" if port == standard else f":{port}"
    return f"{scheme}://{target}{suffix}"


async def _record_web_finding(origin: str, payload: dict) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            response = await client.post(f"{origin}/api/security/advanced-web-drill", json=payload)
            response.raise_for_status()
            return response.json()
    except Exception:
        return None


@register
class IdorAudit(AttackModuleBase):
    id = "idor_audit"
    name = "IDOR Object Access Audit"
    description = "Checks whether one user can read another user's account object by changing an ID."
    default_target = "mini-vuln-app"
    mitre = "T1190"
    params_schema = {
        "scheme": {"type": "select", "label": "Target scheme", "default": "http", "options": ["http", "https"]},
        "port": {"type": "int", "label": "Target port", "default": 3003},
        "requester_id": {"type": "int", "label": "Requester user ID", "default": 2},
        "account_id": {"type": "int", "label": "Account ID to request", "default": 1001},
    }

    async def run(self, target: str, params: dict, emit: Emit) -> dict:
        origin = _target_origin(target, params)
        requester_id = int(params.get("requester_id", 2))
        account_id = int(params.get("account_id", 1001))
        url = f"{origin}/api/accounts/{account_id}"

        await emit("info", f"Requesting account {account_id} as user {requester_id}.", 10, {"url": url})
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, headers={"x-user-id": str(requester_id)})
        data = response.json()
        account = data.get("account") or {}
        vulnerable = response.status_code == 200 and data.get("idor_vulnerable") is True

        if vulnerable:
            await emit(
                "success",
                f"IDOR confirmed: user {requester_id} read account {account.get('id')} owned by user {account.get('owner_id')}.",
                70,
                {"account": account, "requester_id": requester_id},
            )
            soc_event = await _record_web_finding(origin, {
                "category": "authorization",
                "title": "IDOR confirmed on account object",
                "severity": "high",
                "affected": ["api", "database", "auth"],
                "account_id": account_id,
                "requester_id": requester_id,
            })
        else:
            await emit("warn", "IDOR not confirmed in this run.", 70, {"status_code": response.status_code, "body": data})
            soc_event = None

        result = {
            "success": vulnerable,
            "endpoint": url,
            "requester_id": requester_id,
            "account_id": account_id,
            "returned_owner_id": account.get("owner_id"),
            "soc_event": soc_event,
        }
        await emit("success" if vulnerable else "warn", "IDOR audit complete.", 100, result)
        return result


@register
class AuthorizationBypassAudit(AttackModuleBase):
    id = "authz_bypass"
    name = "Authorization Bypass Audit"
    description = "Tests whether an admin action trusts a client-controlled role header."
    default_target = "mini-vuln-app"
    mitre = "T1548"
    params_schema = {
        "scheme": {"type": "select", "label": "Target scheme", "default": "http", "options": ["http", "https"]},
        "port": {"type": "int", "label": "Target port", "default": 3003},
        "transfer_id": {"type": "int", "label": "Transfer ID", "default": 501},
    }

    async def run(self, target: str, params: dict, emit: Emit) -> dict:
        origin = _target_origin(target, params)
        transfer_id = int(params.get("transfer_id", 501))
        url = f"{origin}/api/admin/approve-transfer"

        await emit("info", "Verifying baseline: normal user role should be denied.", 10, {"url": url})
        async with httpx.AsyncClient(timeout=10) as client:
            denied = await client.post(url, json={"transfer_id": transfer_id}, headers={"x-user-role": "user"})
            await asyncio.sleep(0.2)
            await emit("info", "Testing bypass: client-supplied admin role header.", 45, {"header": "x-user-role: admin"})
            bypass = await client.post(url, json={"transfer_id": transfer_id}, headers={"x-user-role": "admin"})

        body = bypass.json()
        vulnerable = denied.status_code == 403 and bypass.status_code == 200 and body.get("authz_bypass_vulnerable") is True
        if vulnerable:
            await emit(
                "success",
                "Authorization bypass confirmed: server trusted a client-controlled role.",
                75,
                {"baseline_status": denied.status_code, "bypass_status": bypass.status_code, "transfer": body.get("transfer")},
            )
            soc_event = await _record_web_finding(origin, {
                "category": "authorization",
                "title": "Authorization bypass on transfer approval",
                "severity": "critical",
                "affected": ["api", "auth", "database"],
                "transfer_id": transfer_id,
            })
        else:
            await emit("warn", "Authorization bypass not confirmed in this run.", 75, {"status_code": bypass.status_code, "body": body})
            soc_event = None

        result = {
            "success": vulnerable,
            "endpoint": url,
            "baseline_status": denied.status_code,
            "bypass_status": bypass.status_code,
            "soc_event": soc_event,
        }
        await emit("success" if vulnerable else "warn", "Authorization bypass audit complete.", 100, result)
        return result


@register
class AdvancedXssAudit(AttackModuleBase):
    id = "xss_advanced"
    name = "Advanced XSS Audit"
    description = "Checks reflected and stored XSS sinks using harmless lab-only browser payloads."
    default_target = "mini-vuln-app"
    mitre = "T1059.007"
    params_schema = {
        "scheme": {"type": "select", "label": "Target scheme", "default": "http", "options": ["http", "https"]},
        "port": {"type": "int", "label": "Target port", "default": 3003},
        "payload": {
            "type": "text",
            "label": "Harmless XSS marker",
            "default": "<img src=x onerror=\"console.log('cybersim-xss')\">",
        },
    }

    async def run(self, target: str, params: dict, emit: Emit) -> dict:
        origin = _target_origin(target, params)
        payload = str(params.get("payload") or "<img src=x onerror=\"console.log('cybersim-xss')\">")
        findings = []

        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            await emit("info", "Testing reflected XSS in /search.", 15, {"payload": payload})
            reflected = await client.get(f"{origin}/search", params={"q": payload})
            if payload in reflected.text and html.escape(payload) not in reflected.text:
                findings.append({"type": "reflected", "endpoint": f"{origin}/search", "payload": payload})
                await emit("success", "Reflected XSS confirmed: payload returned unescaped in HTML.", 38)
            else:
                await emit("info", "Reflected sink did not echo the raw marker.", 38)

            await emit("info", "Testing stored XSS in /api/comments -> /comments.", 55, {"payload": payload})
            stored_post = await client.post(f"{origin}/api/comments", json={"author": "cybersim", "body": payload})
            stored_page = await client.get(f"{origin}/comments")
            if stored_post.status_code == 201 and payload in stored_page.text:
                findings.append({"type": "stored", "endpoint": f"{origin}/comments", "payload": payload})
                await emit("success", "Stored XSS confirmed: comment rendered raw on /comments.", 78)
            else:
                await emit("info", "Stored sink did not render the raw marker.", 78)

        soc_event = None
        if findings:
            soc_event = await _record_web_finding(origin, {
                "category": "browser",
                "title": "Advanced XSS findings confirmed",
                "severity": "high",
                "affected": ["browser", "api"],
                "findings": findings,
            })

        result = {
            "success": bool(findings),
            "findings": findings,
            "payload_executes_external_code": False,
            "soc_event": soc_event,
        }
        await emit("success" if findings else "warn", f"Advanced XSS audit complete: {len(findings)} finding(s).", 100, result)
        return result


@register
class RatTrojanSimulation(AttackModuleBase):
    id = "rat_trojan_sim"
    name = "RAT/Trojan Behavior Simulation"
    description = "Safe SOC drill for RAT/trojan indicators: C2 beacons, persistence signals, and credential-access telemetry."
    default_target = "mini-vuln-app"
    mitre = "T1219"
    params_schema = {
        "scheme": {"type": "select", "label": "Target scheme", "default": "http", "options": ["http", "https"]},
        "port": {"type": "int", "label": "Target port", "default": 3003},
        "family": {
            "type": "select",
            "label": "Simulation family",
            "default": "rat_simulated",
            "options": ["rat_simulated", "trojan_loader_simulated", "keylogger_signal_simulated"],
        },
        "affected_hosts": {"type": "int", "label": "Affected hosts", "default": 2, "max": 3},
    }

    async def run(self, target: str, params: dict, emit: Emit) -> dict:
        origin = _target_origin(target, params)
        family = str(params.get("family", "rat_simulated"))
        affected_hosts = max(1, min(int(params.get("affected_hosts", 2)), 3))

        await emit("info", "Starting safe RAT/trojan drill. No payload is created, downloaded, or executed.", 5, {
            "safe_simulation": True,
            "family": family,
        })
        await asyncio.sleep(0.2)
        await emit("warn", "C2-like signal: simulated periodic HTTPS beacon pattern.", 25, {
            "indicator": "simulated_c2_beacon",
            "network_connection_created": False,
        })
        await asyncio.sleep(0.2)
        await emit("warn", "Persistence-like signal: simulated autorun/service registration alert.", 48, {
            "indicator": "simulated_persistence",
            "registry_or_service_modified": False,
        })
        await asyncio.sleep(0.2)
        await emit("warn", "Credential-access signal: simulated browser/session credential touch.", 68, {
            "indicator": "simulated_credential_access",
            "credentials_collected": 0,
        })

        target_event = None
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.post(
                    f"{origin}/api/security/rat-telemetry",
                    json={
                        "family": family,
                        "affected_hosts": affected_hosts,
                        "c2_profile": "simulated periodic HTTPS beacon",
                    },
                )
                response.raise_for_status()
                target_event = response.json()
            await emit("info", "Target SOC updated with safe RAT/trojan telemetry.", 88, {
                "target_api": f"{origin}/api/security/rat-telemetry",
                "incident_id": target_event.get("incident", {}).get("id"),
            })
        except Exception as exc:
            await emit("warn", f"Target SOC telemetry could not be recorded: {exc}", 88)

        result = {
            "success": True,
            "safe_simulation": True,
            "family": family,
            "affected_hosts": affected_hosts,
            "payload_executed": False,
            "files_created": 0,
            "credentials_collected": 0,
            "remote_control_enabled": False,
            "target_api_event": target_event,
            "recommended_actions": [
                "Isolate affected hosts from the network.",
                "Collect EDR timeline and process tree.",
                "Revoke sessions and rotate credentials for affected users.",
                "Hunt for persistence, suspicious remote-access tools, and beacon patterns.",
            ],
        }
        await emit("success", "Safe RAT/trojan drill complete: SOC telemetry generated without malware execution.", 100, result)
        return result
