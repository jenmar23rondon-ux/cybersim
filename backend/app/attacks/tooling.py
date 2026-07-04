"""Industry-tool wrappers for the local lab.

These modules run common pentest tools only against allowlisted Docker targets.
They are deliberately bounded: fixed profiles, no arbitrary command strings,
short timeouts, and conservative flags.
"""

from __future__ import annotations

import asyncio
import re
import tempfile
from urllib.parse import quote

from .base import AttackModuleBase, Emit, register

MAX_OUTPUT_LINES = 80


async def _run_tool(args: list[str], emit: Emit, timeout: int = 90) -> tuple[int, list[str]]:
    await emit("info", "Running: " + " ".join(args[:4]) + " ...", 10, {"tool": args[0]})
    proc = await asyncio.create_subprocess_exec(
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )

    lines: list[str] = []

    async def reader():
        assert proc.stdout is not None
        while True:
            raw = await proc.stdout.readline()
            if not raw:
                break
            line = raw.decode("utf-8", "replace").strip()
            if not line:
                continue
            lines.append(line)
            if len(lines) <= MAX_OUTPUT_LINES:
                level = "success" if any(x in line.lower() for x in ("is vulnerable", "valid password", "login:")) else "info"
                progress = min(95, 15 + len(lines))
                await emit(level, line[:500], progress, {"tool_output": True})

    task = asyncio.create_task(reader())
    try:
        await asyncio.wait_for(proc.wait(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        await emit("warn", f"{args[0]} timed out after {timeout}s; partial output captured.", 95)
    await task
    return proc.returncode or 0, lines


@register
class SqlmapJuiceShop(AttackModuleBase):
    id = "sqlmap_juice"
    name = "sqlmap vs Juice Shop"
    description = "Runs sqlmap against OWASP Juice Shop's local search endpoint."
    default_target = "juice-shop"
    mitre = "T1190"
    params_schema = {
        "port": {"type": "int", "default": 3000, "label": "Container port"},
        "search": {"type": "string", "default": "apple", "label": "Search value"},
        "timeout": {"type": "int", "default": 90, "label": "Timeout seconds"},
    }

    async def run(self, target: str, params: dict, emit: Emit) -> dict:
        port = int(params.get("port", 3000))
        search = quote(str(params.get("search", "apple")))
        timeout = max(30, min(int(params.get("timeout", 90)), 180))
        url = f"http://{target}:{port}/rest/products/search?q={search}"

        await emit("info", "Starting sqlmap in safe lab profile.", 5, {"url": url})
        args = [
            "sqlmap",
            "-u", url,
            "--batch",
            "--level", "1",
            "--risk", "1",
            "--threads", "1",
            "--timeout", "10",
            "--answers", "follow=N",
        ]
        code, lines = await _run_tool(args, emit, timeout=timeout)
        joined = "\n".join(lines).lower()
        vulnerable = "is vulnerable" in joined or "sql injection" in joined
        dbms = _first_match(lines, r"back-end DBMS:\s*(.+)")

        await emit("success" if vulnerable else "warn",
                   "sqlmap finished: " + ("injection evidence found." if vulnerable else "no injection confirmed in this run."),
                   100, {"exit_code": code, "dbms": dbms})
        return {
            "success": vulnerable,
            "tool": "sqlmap",
            "url": url,
            "exit_code": code,
            "dbms": dbms,
            "evidence": lines[-20:],
        }


@register
class HydraCredentialAudit(AttackModuleBase):
    id = "hydra_bruteforce"
    name = "Hydra Credential Audit"
    description = "Runs hydra against local SSH or Juice Shop login profiles."
    default_target = "weak-ssh"
    mitre = "T1110"
    params_schema = {
        "profile": {"type": "select", "options": ["weak_ssh", "juice_shop_login"], "default": "weak_ssh"},
        "port": {"type": "int", "default": 22, "label": "Container port"},
        "usernames": {"type": "list", "default": ["labuser", "root", "admin"]},
        "passwords": {"type": "list", "default": ["password123", "toor", "admin123", "123456"]},
        "timeout": {"type": "int", "default": 75, "label": "Timeout seconds"},
    }

    async def run(self, target: str, params: dict, emit: Emit) -> dict:
        profile = params.get("profile", "weak_ssh")
        users = _clean_words(params.get("usernames") or [])
        passwords = _clean_words(params.get("passwords") or [])
        timeout = max(30, min(int(params.get("timeout", 75)), 180))

        if not users or not passwords:
            await emit("error", "Hydra requires at least one username and password.", 100)
            return {"success": False, "error": "empty wordlist"}

        with tempfile.NamedTemporaryFile("w", delete=True) as user_file, tempfile.NamedTemporaryFile("w", delete=True) as pass_file:
            user_file.write("\n".join(users) + "\n")
            pass_file.write("\n".join(passwords) + "\n")
            user_file.flush()
            pass_file.flush()

            if profile == "juice_shop_login":
                port = int(params.get("port", 3000))
                target = "juice-shop" if target in {"weak-ssh", "vuln-node-api"} else target
                args = [
                    "hydra",
                    "-L", user_file.name,
                    "-P", pass_file.name,
                    "-s", str(port),
                    "-V",
                    target,
                    "http-post-form",
                    '/rest/user/login:{"email":"^USER^","password":"^PASS^"}:Invalid email or password:H=Content-Type\\: application/json',
                ]
            else:
                port = int(params.get("port", 22))
                target = "weak-ssh" if target == "juice-shop" else target
                args = [
                    "hydra",
                    "-L", user_file.name,
                    "-P", pass_file.name,
                    "-s", str(port),
                    "-V",
                    f"ssh://{target}",
                ]

            await emit("info", f"Starting hydra profile '{profile}' against {target}.", 5)
            code, lines = await _run_tool(args, emit, timeout=timeout)
        found = [line for line in lines if re.search(r"(login:|password:|\[ssh\])", line, re.I)]
        success = bool(found)

        await emit("success" if success else "warn",
                   f"Hydra finished: {len(found)} credential finding(s).",
                   100, {"findings": found[:10], "exit_code": code})
        return {
            "success": success,
            "tool": "hydra",
            "profile": profile,
            "exit_code": code,
            "findings": found[:10],
            "evidence": lines[-20:],
        }


def _clean_words(values: list[str]) -> list[str]:
    cleaned = []
    for value in values:
        word = str(value).strip()
        if word and re.match(r"^[A-Za-z0-9@._+-]{1,80}$", word):
            cleaned.append(word)
    return cleaned[:20]


def _first_match(lines: list[str], pattern: str) -> str | None:
    rx = re.compile(pattern, re.I)
    for line in lines:
        m = rx.search(line)
        if m:
            return m.group(1).strip()
    return None
