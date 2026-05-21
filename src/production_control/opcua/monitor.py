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
MAX_BROWSE_DEPTH = 6
RECONNECT_DELAY_S = 5
SUBSCRIPTION_INTERVAL_MS = 500

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


async def _connect_and_run(url: str) -> None:
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
        variables: list[tuple[Node, str]] = []
        for child in await objects.get_children():
            if child.nodeid.NamespaceIndex == 0:
                continue
            variables.extend(await discover_variables(child))

        if not variables:
            logger.warning("no user-namespace variables found; nothing to subscribe to")
            return

        handler = JsonlHandler(source="plc")
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


async def main() -> None:
    url = _env("VINEAPP_OPCUA_PLC_URL")
    while True:
        try:
            await _connect_and_run(url)
            logger.warning("connection closed cleanly; reconnecting in %ds", RECONNECT_DELAY_S)
        except (asyncio.CancelledError, KeyboardInterrupt):
            raise
        except Exception as exc:
            logger.warning("connection error: %s; reconnecting in %ds", exc, RECONNECT_DELAY_S)
        await asyncio.sleep(RECONNECT_DELAY_S)


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
