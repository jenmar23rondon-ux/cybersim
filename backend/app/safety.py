"""Target safety guard.

Every attack MUST pass through :func:`assert_target_allowed` before any packet
is sent. Only hosts on the configured allowlist (local Docker service names and
loopback) are permitted. Public/external addresses are rejected outright.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse

from .config import get_settings


class TargetNotAllowed(Exception):
    """Raised when an attack is aimed at a non-allowlisted destination."""


# Private / loopback ranges are acceptable (the lab lives inside them).
_PRIVATE_NETS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
]


def _is_private_ip(host: str) -> bool:
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return False
    return any(ip in net for net in _PRIVATE_NETS)


def normalize_target(target: str) -> str:
    """Normalize a target string to hostname only."""
    host = target.strip().lower()
    parsed = urlparse(host if "://" in host else f"//{host}", scheme="http")
    host = parsed.hostname or host.split("/")[0].split(":")[0]
    return host


def describe_target(target: str) -> dict:
    """Return normalized target details used by the connector UI."""
    host = normalize_target(target)
    allow = get_settings().allowlist
    explicit = host in allow
    resolved = None
    private = _is_private_ip(host)

    if not private:
        try:
            resolved = socket.gethostbyname(host)
            private = _is_private_ip(resolved)
        except socket.gaierror:
            resolved = None

    return {
        "host": host,
        "explicitly_allowlisted": explicit,
        "resolved_ip": resolved,
        "private_or_loopback": private,
        "allowed": explicit or private,
    }


def assert_target_allowed(target: str) -> str:
    """Return the normalized host if allowed, else raise ``TargetNotAllowed``.

    A target is allowed when it is explicitly on the allowlist, OR it is a
    hostname that resolves to a private/loopback address (i.e. another lab
    container). Anything resolving to a public IP is blocked.
    """
    if not target:
        raise TargetNotAllowed("Empty target.")

    host = normalize_target(target)

    allow = get_settings().allowlist
    if host in allow:
        return host

    if _is_private_ip(host):
        return host

    # Resolve hostname -> must land on a private address to be accepted.
    try:
        resolved = socket.gethostbyname(host)
    except socket.gaierror:
        raise TargetNotAllowed(
            f"Target '{target}' is not on the allowlist and could not be resolved."
        )

    if _is_private_ip(resolved):
        return host

    raise TargetNotAllowed(
        f"Refusing to attack '{target}' -> {resolved}: only local lab targets are permitted."
    )
