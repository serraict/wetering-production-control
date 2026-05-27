"""Docker HEALTHCHECK for the OPC protocol daemon.

Exits 0 if every role's heartbeat file (written by
`opcua.heartbeat.beat_while_alive`) was touched within
`VINEAPP_OPCUA_HEARTBEAT_MAX_AGE_S` seconds; exits 1 otherwise. Prints
which roles are stale on stderr so `docker inspect` shows the reason.

Run as `python -m production_control.opcua.healthcheck`.
"""

from __future__ import annotations

import os
import sys
import time

from .heartbeat import path_for

ROLES = ("plc", "leuze")
DEFAULT_MAX_AGE_S = 30


def _max_age() -> float:
    raw = os.environ.get("VINEAPP_OPCUA_HEARTBEAT_MAX_AGE_S")
    return float(raw) if raw else DEFAULT_MAX_AGE_S


def check(now: float | None = None) -> list[str]:
    """Return a list of problem descriptions; empty list means healthy."""
    now = time.time() if now is None else now
    max_age = _max_age()
    problems: list[str] = []
    for role in ROLES:
        path = path_for(role)
        if not path.exists():
            problems.append(f"{role}: heartbeat file {path} missing")
            continue
        age = now - path.stat().st_mtime
        if age > max_age:
            problems.append(f"{role}: stale (last beat {age:.0f}s ago, max {max_age:.0f}s)")
    return problems


def main() -> int:
    problems = check()
    if problems:
        for line in problems:
            print(f"unhealthy: {line}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
