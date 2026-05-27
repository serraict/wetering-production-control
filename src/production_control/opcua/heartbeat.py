"""Per-role liveness heartbeat for the OPC protocol daemon.

Each supervised loop in `protocol.scan_cycle` runs `beat_while_alive`
after its subscription is live. The companion `healthcheck` module
reads the file mtimes to answer the Docker HEALTHCHECK.

Files live under `VINEAPP_OPCUA_HEARTBEAT_DIR` (default `/tmp`). Tests
override the env var to keep `/tmp` clean.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

HEARTBEAT_INTERVAL_S = 10
DEFAULT_DIR = "/tmp"


def _dir() -> Path:
    return Path(os.environ.get("VINEAPP_OPCUA_HEARTBEAT_DIR", DEFAULT_DIR))


def path_for(role: str) -> Path:
    return _dir() / f"opcua-{role}.alive"


async def beat_while_alive(
    role: str,
    stop_event: asyncio.Event,
    *,
    interval_s: float = HEARTBEAT_INTERVAL_S,
) -> None:
    """Touch the role's heartbeat file every `interval_s` seconds until
    `stop_event` fires or the task is cancelled. The first touch happens
    immediately so a freshly-connected subscription is reflected without
    waiting a full interval."""
    target = path_for(role)
    target.parent.mkdir(parents=True, exist_ok=True)
    while not stop_event.is_set():
        target.touch()
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval_s)
        except asyncio.TimeoutError:
            continue
