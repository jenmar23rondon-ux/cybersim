"""Port scanner.

Uses nmap (via python-nmap) when available, otherwise falls back to a plain
asyncio TCP-connect scan. Only scans the local lab target.
"""

from __future__ import annotations

import asyncio

from .base import AttackModuleBase, Emit, register

COMMON_PORTS = [21, 22, 23, 25, 53, 80, 110, 143, 443, 445, 3000, 3001, 3306, 4280, 5432, 8000, 8080]


@register
class PortScan(AttackModuleBase):
    id = "port_scan"
    name = "Port Scanner (Nmap)"
    description = "Enumerates open TCP ports and services on a lab host."
    default_target = "vuln-node-api"
    mitre = "T1046"
    params_schema = {
        "ports": {"type": "string", "default": "21-25,80,443,3001,3306,5432,8000",
                  "label": "Port range"},
    }

    async def run(self, target: str, params: dict, emit: Emit) -> dict:
        port_spec = str(params.get("ports", "")).strip()
        await emit("info", f"Scanning {target} ({port_spec or 'common ports'})", 5)

        try:
            result = await self._nmap(target, port_spec, emit)
            if result is not None:
                return result
        except Exception as exc:
            await emit("warn", f"nmap unavailable ({exc}); using TCP-connect fallback.", 10)

        return await self._tcp_connect(target, emit)

    async def _nmap(self, target, port_spec, emit) -> dict | None:
        import nmap

        scanner = nmap.PortScanner()
        await emit("info", "Running nmap -sT -sV ...", 20)
        args = f"-sT -sV -p {port_spec}" if port_spec else "-sT -sV -F"
        await asyncio.to_thread(scanner.scan, hosts=target, arguments=args)

        if target not in scanner.all_hosts():
            # container name may resolve differently; try scanned hosts.
            hosts = scanner.all_hosts()
            if not hosts:
                return None
            target = hosts[0]

        open_ports = []
        for proto in scanner[target].all_protocols():
            for port in sorted(scanner[target][proto].keys()):
                info = scanner[target][proto][port]
                if info.get("state") == "open":
                    svc = f"{info.get('name','?')} {info.get('product','')} {info.get('version','')}".strip()
                    await emit("success", f"OPEN {port}/tcp — {svc}", 60,
                               {"port": port, "service": svc})
                    open_ports.append({"port": port, "service": svc})
        await emit("success", f"Scan complete: {len(open_ports)} open port(s).", 100,
                   {"open_ports": open_ports})
        return {"success": True, "engine": "nmap", "open_ports": open_ports}

    async def _tcp_connect(self, target, emit) -> dict:
        open_ports = []
        total = len(COMMON_PORTS)
        for i, port in enumerate(COMMON_PORTS):
            progress = int(15 + (i / total) * 80)
            try:
                fut = asyncio.open_connection(target, port)
                reader, writer = await asyncio.wait_for(fut, timeout=1.0)
                writer.close()
                await emit("success", f"OPEN {port}/tcp", progress, {"port": port})
                open_ports.append({"port": port, "service": "unknown"})
            except Exception:
                await emit("info", f"Closed {port}/tcp", progress)
        await emit("success", f"Scan complete: {len(open_ports)} open port(s).", 100,
                   {"open_ports": open_ports})
        return {"success": len(open_ports) > 0, "engine": "tcp-connect", "open_ports": open_ports}
