"""Attack module framework.

Each module subclasses :class:`AttackModule` and implements ``run``. Modules emit
log events through the ``emit`` coroutine, which streams them to WebSocket
clients, persists them, and forwards them to the SIEM. Modules must never touch
the network without the target having passed the safety guard (enforced by the
engine before ``run`` is called).
"""

from __future__ import annotations

from typing import Awaitable, Callable, Protocol

# emit(level, message, progress, data) -> awaitable
Emit = Callable[..., Awaitable[None]]

REGISTRY: dict[str, "AttackModule"] = {}


class AttackModule(Protocol):
    id: str
    name: str
    description: str
    default_target: str
    mitre: str
    params_schema: dict


def register(module: "AttackModuleBase") -> "AttackModuleBase":
    REGISTRY[module.id] = module
    return module


class AttackModuleBase:
    id: str = ""
    name: str = ""
    description: str = ""
    default_target: str = ""
    mitre: str = ""
    params_schema: dict = {}

    async def run(self, target: str, params: dict, emit: Emit) -> dict:
        """Execute the attack, emitting progress. Return a result dict with at
        least a ``success`` boolean."""
        raise NotImplementedError

    def info(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "default_target": self.default_target,
            "mitre": self.mitre,
            "params_schema": self.params_schema,
        }
