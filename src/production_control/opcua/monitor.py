"""PLC monitor v1: discover all user-namespace variables on the Omron PLC,
subscribe to every one, emit one JSONL record per datachange to stdout.

Verifies the discover-and-subscribe approach against the production PLC.
See work/doing.md and work/notes/plc_monitoring_app.md.

Run:
    uv run python -m production_control.opcua.monitor
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone

from asyncua import Client, Node, ua
from asyncua.crypto.security_policies import SecurityPolicyBasic256Sha256

DEFAULT_APP_URI = "urn:serra:production-control-client"
MAX_BROWSE_DEPTH = 20
SUBSCRIPTION_INTERVAL_MS = 500

# Reconnect backoff: start at BASE, double up to MAX. Reset to BASE if a run
# lasts at least RESET_AFTER seconds (it was healthy, treat next failure as
# fresh). Give up entirely after MAX_ATTEMPTS consecutive failures.
RECONNECT_BASE_DELAY_S = 5
RECONNECT_MAX_DELAY_S = 60
RECONNECT_RESET_AFTER_S = 60
RECONNECT_MAX_ATTEMPTS = 10

logger = logging.getLogger("opcua_monitor")


class JsonlHandler:
    """asyncua subscription handler that emits one JSONL line per datachange."""

    def __init__(self, source: str) -> None:
        self._source = source
        self._names: dict[str, str] = {}

    def register(self, node: Node, name: str) -> None:
        self._names[node.nodeid.to_string()] = name

    def datachange_notification(self, node, val, data) -> None:
        node_id = node.nodeid.to_string()
        monitored = data.monitored_item.Value
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "source": self._source,
            "node_id": node_id,
            "node": self._names.get(node_id, node_id),
            "value": _jsonable(val),
            "server_ts": _isoformat(monitored.ServerTimestamp),
            "source_ts": _isoformat(monitored.SourceTimestamp),
            "status": str(monitored.StatusCode.name) if monitored.StatusCode else None,
        }
        sys.stdout.write(json.dumps(record, default=str) + "\n")
        sys.stdout.flush()

    def status_change_notification(self, status) -> None:  # noqa: D401
        logger.warning("status change: %s", status)

    def event_notification(self, event) -> None:  # noqa: D401
        logger.info("event: %s", event)


def _isoformat(ts) -> str | None:
    if ts is None:
        return None
    if isinstance(ts, datetime):
        return ts.replace(tzinfo=ts.tzinfo or timezone.utc).isoformat()
    return str(ts)


def _jsonable(value):
    """Best-effort conversion of asyncua Variant payloads to JSON-friendly types."""
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        print(f"missing env var: {name}", file=sys.stderr)
        sys.exit(2)
    return value


async def discover_variables(
    root: Node,
    *,
    depth: int = 0,
    seen: set[str] | None = None,
) -> list[tuple[Node, str]]:
    """Walk the OPC tree from `root`, return [(node, display_name)] for every
    Variable in a user namespace. Skips ns=0 (OPC UA standard) and refs that
    have already been visited (guards against cycles)."""

    if depth > MAX_BROWSE_DEPTH:
        return []

    if seen is None:
        seen = set()

    key = root.nodeid.to_string()
    if key in seen:
        return []
    seen.add(key)

    found: list[tuple[Node, str]] = []

    try:
        node_class = await root.read_node_class()
    except ua.UaError as exc:
        logger.debug("read_node_class failed for %s: %s", key, exc)
        return found

    if node_class == ua.NodeClass.Variable:
        try:
            name = (await root.read_display_name()).Text
        except ua.UaError:
            name = key
        found.append((root, name))

    try:
        children = await root.get_children()
    except ua.UaError as exc:
        logger.debug("get_children failed for %s: %s", key, exc)
        return found

    for child in children:
        if child.nodeid.NamespaceIndex == 0:
            continue
        found.extend(await discover_variables(child, depth=depth + 1, seen=seen))

    return found


def _build_client(url: str, *, secure: bool) -> Client:
    client = Client(url=url)
    client.application_uri = os.environ.get("VINEAPP_OPCUA_CLIENT_APP_URI", DEFAULT_APP_URI)
    if secure:
        client.set_user(_env("VINEAPP_OPCUA_PLC_USER"))
        client.set_password(_env("VINEAPP_OPCUA_PLC_PASSWORD"))
    return client


async def run_plc(handler) -> None:
    """One PLC connection lifetime: connect, discover, subscribe, feed the
    given handler. Reconnects are handled by `supervise`.

    `handler` is reused across reconnect attempts — must be safe to call
    `.register(node, name)` repeatedly (JsonlHandler is; StateHandler should
    be too)."""
    url = _env("VINEAPP_OPCUA_PLC_URL")
    secure = os.environ.get("VINEAPP_OPCUA_SECURITY", "").lower() != "none"
    client = _build_client(url, secure=secure)
    if secure:
        await client.set_security(
            SecurityPolicyBasic256Sha256,
            certificate=_env("VINEAPP_OPCUA_CLIENT_CERT"),
            private_key=_env("VINEAPP_OPCUA_CLIENT_KEY"),
            mode=ua.MessageSecurityMode.SignAndEncrypt,
        )

    logger.info("connecting to %s", url)
    async with client:
        objects = client.nodes.objects
        # Walk each top-level subtree with its own `seen` set (for cycle
        # safety). Dedupe variables by NodeId after — the Omron tree exposes
        # the same Wetering_Portaal subtree from two paths (DeviceSet/.../
        # vs top-level), and the same variables appear in both. Walking with
        # a shared seen would prune one of the paths and miss vars only
        # reachable within MAX_BROWSE_DEPTH of the short path.
        by_id: dict[str, tuple[Node, str]] = {}
        for child in await objects.get_children():
            if child.nodeid.NamespaceIndex == 0:
                continue
            for node, name in await discover_variables(child):
                key = node.nodeid.to_string()
                if key not in by_id:
                    by_id[key] = (node, name)
        variables = list(by_id.values())

        if not variables:
            logger.warning("no user-namespace variables found; nothing to subscribe to")
            return

        for node, name in variables:
            handler.register(node, name)
            logger.info("discovered %s (%s)", name, node.nodeid.to_string())

        subscription = await client.create_subscription(SUBSCRIPTION_INTERVAL_MS, handler)
        await subscription.subscribe_data_change([node for node, _ in variables])
        logger.info("subscribed to %d variables", len(variables))

        try:
            while True:
                await asyncio.sleep(1)
        finally:
            try:
                await subscription.delete()
            except Exception:  # pragma: no cover - best-effort cleanup
                pass


async def supervise(name: str, run) -> None:
    """Run `run` with exponential backoff on failure. Give up after
    RECONNECT_MAX_ATTEMPTS consecutive failures. A run that lasted at least
    RECONNECT_RESET_AFTER_S seconds resets the backoff and attempt counter."""

    loop = asyncio.get_event_loop()
    delay = RECONNECT_BASE_DELAY_S
    attempt = 0

    while True:
        attempt += 1
        started = loop.time()
        try:
            await run()
            elapsed = loop.time() - started
            logger.warning(
                "%s: connection closed cleanly after %.0fs (attempt %d); reconnecting in %ds",
                name, elapsed, attempt, delay,
            )
        except (asyncio.CancelledError, KeyboardInterrupt):
            raise
        except Exception as exc:
            elapsed = loop.time() - started
            logger.warning(
                "%s: %s after %.0fs (attempt %d/%d): %r; reconnecting in %ds",
                name, type(exc).__name__, elapsed, attempt, RECONNECT_MAX_ATTEMPTS,
                exc, delay,
            )

        if elapsed >= RECONNECT_RESET_AFTER_S:
            delay = RECONNECT_BASE_DELAY_S
            attempt = 0
        elif attempt >= RECONNECT_MAX_ATTEMPTS:
            logger.error(
                "%s: giving up after %d consecutive failures within %.0fs",
                name, attempt, loop.time() - started,
            )
            return

        await asyncio.sleep(delay)
        if elapsed < RECONNECT_RESET_AFTER_S:
            delay = min(delay * 2, RECONNECT_MAX_DELAY_S)


async def main() -> None:
    from functools import partial

    plc_handler = JsonlHandler(source="plc")
    tasks: list[asyncio.Task] = [
        asyncio.create_task(supervise("plc", partial(run_plc, plc_handler)), name="plc"),
    ]

    if os.environ.get("VINEAPP_OPCUA_LEUZE_URL"):
        # Import lazily so the LenientCertificate monkey-patch only takes effect
        # when we actually plan to talk to a Leuze.
        from .leuze import run_leuze

        leuze_handler = JsonlHandler(source="leuze")
        tasks.append(
            asyncio.create_task(supervise("leuze", partial(run_leuze, leuze_handler)), name="leuze")
        )
    else:
        logger.info("VINEAPP_OPCUA_LEUZE_URL not set; Leuze source skipped")

    try:
        await asyncio.gather(*tasks)
    except (asyncio.CancelledError, KeyboardInterrupt):
        for t in tasks:
            t.cancel()
        raise


def cli() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )
    logging.getLogger("asyncua").setLevel(logging.WARNING)
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass


if __name__ == "__main__":
    cli()
