"""PLC monitor: discover all user-namespace variables on the Omron PLC,
subscribe to every one, emit one JSONL record per datachange to stdout.

Run:
    uv run python -m production_control.opcua.monitor
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone

from asyncua import Client, Node, ua

from .config import build_client, require_env

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

    def set_client(self, client: Client | None) -> None:
        """Subscription handlers can override this to keep a live client
        reference for ad-hoc reads/writes. JSONL output doesn't need one."""

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


async def discover_plc_variables(client: Client) -> list[tuple[Node, str]]:
    """Walk every top-level subtree under `client.nodes.objects` and return
    all user-namespace variables, deduped by NodeId.

    Each subtree is walked with its own `seen` set (for cycle safety).
    Dedupe happens after — the Omron tree exposes the same Wetering_Portaal
    subtree from two paths (DeviceSet/.../ vs top-level) and the same
    variables appear in both. Walking with a shared `seen` would prune one
    of the paths and miss vars only reachable within MAX_BROWSE_DEPTH of
    the short path."""
    by_id: dict[str, tuple[Node, str]] = {}
    for child in await client.nodes.objects.get_children():
        if child.nodeid.NamespaceIndex == 0:
            continue
        for node, name in await discover_variables(child):
            key = node.nodeid.to_string()
            if key not in by_id:
                by_id[key] = (node, name)
    return list(by_id.values())


async def run_plc(handler) -> None:
    """One PLC connection lifetime: connect, discover, subscribe, feed the
    given handler. Reconnects are handled by `supervise`.

    `handler` is reused across reconnect attempts — must be safe to call
    `.register(node, name)` repeatedly (JsonlHandler is; StateHandler should
    be too)."""
    client = await build_client("plc")
    logger.info("connecting to %s", require_env("VINEAPP_OPCUA_PLC_URL"))
    async with client:
        handler.set_client(client)
        try:
            variables = await discover_plc_variables(client)

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
        finally:
            handler.set_client(None)


async def supervise(
    name: str,
    run,
    *,
    max_attempts: int | None = RECONNECT_MAX_ATTEMPTS,
    stop_event: asyncio.Event | None = None,
) -> None:
    """Run `run` with exponential backoff on failure.

    `max_attempts`:
      * int — give up after that many consecutive failures (the headless
        monitor's policy; keeps a noisy startup from looping forever).
      * None — never give up. The protocol daemon uses this so a long
        outage doesn't kill the container; Docker `restart: unless-stopped`
        is the right policy for "process truly broken".

    `stop_event`: when provided and set, a clean return from `run()` is
    treated as graceful shutdown — supervise exits without the
    "reconnecting in Ns" log and without sleeping the backoff.

    A run that lasted at least `RECONNECT_RESET_AFTER_S` seconds resets
    the backoff and attempt counter."""

    loop = asyncio.get_event_loop()
    delay = RECONNECT_BASE_DELAY_S
    attempt = 0

    while True:
        if stop_event is not None and stop_event.is_set():
            return
        attempt += 1
        started = loop.time()
        try:
            await run()
            elapsed = loop.time() - started
            if stop_event is not None and stop_event.is_set():
                return
            logger.warning(
                "%s: connection closed cleanly after %.0fs (attempt %d); reconnecting in %ds",
                name,
                elapsed,
                attempt,
                delay,
            )
        except (asyncio.CancelledError, KeyboardInterrupt):
            raise
        except Exception as exc:
            elapsed = loop.time() - started
            if stop_event is not None and stop_event.is_set():
                return
            attempt_label = (
                f"{attempt}/{max_attempts}" if max_attempts is not None else f"{attempt}"
            )
            logger.warning(
                "%s: %s after %.0fs (attempt %s): %r; reconnecting in %ds",
                name,
                type(exc).__name__,
                elapsed,
                attempt_label,
                exc,
                delay,
            )

        if elapsed >= RECONNECT_RESET_AFTER_S:
            delay = RECONNECT_BASE_DELAY_S
            attempt = 0
        elif max_attempts is not None and attempt >= max_attempts:
            logger.error(
                "%s: giving up after %d consecutive failures within %.0fs",
                name,
                attempt,
                loop.time() - started,
            )
            return

        # Break the backoff sleep as soon as stop_event fires — otherwise
        # shutdown waits the full `delay` (up to RECONNECT_MAX_DELAY_S).
        if stop_event is not None:
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=delay)
                return
            except asyncio.TimeoutError:
                pass
        else:
            await asyncio.sleep(delay)
        if elapsed < RECONNECT_RESET_AFTER_S:
            delay = min(delay * 2, RECONNECT_MAX_DELAY_S)


_INT_VARIANTS = {
    ua.VariantType.SByte,
    ua.VariantType.Byte,
    ua.VariantType.Int16,
    ua.VariantType.UInt16,
    ua.VariantType.Int32,
    ua.VariantType.UInt32,
    ua.VariantType.Int64,
    ua.VariantType.UInt64,
}


def _parse_value(raw: str, vtype: ua.VariantType):
    """Parse a CLI-supplied string into the Python type matching `vtype`."""
    if vtype == ua.VariantType.Boolean:
        return raw.strip().lower() in ("1", "true", "yes", "on")
    if vtype in _INT_VARIANTS:
        return int(raw)
    if vtype in (ua.VariantType.Float, ua.VariantType.Double):
        return float(raw)
    return raw


async def _iter_target_variables(target: str) -> list[tuple[str, str, "ua.DataValue | Exception"]]:
    """Connect to `target`, return [(node_id, display_name, current_data_value_or_exc)].

    PLC walks the full tree; Leuze uses the fixed LEUZE_NODES set (a full
    browse trips BadEncodingLimitsExceeded on that firmware)."""
    if target == "leuze":
        from . import leuze  # noqa: F401 — apply LenientCertificate patch

        client = await build_client("leuze")
        async with client:
            out = []
            for name, nid in leuze.LEUZE_NODES.items():
                node = client.get_node(nid)
                try:
                    dv = await node.read_data_value()
                except Exception as exc:  # noqa: BLE001 — surface any read failure
                    dv = exc
                out.append((nid, name, dv))
            return out

    client = await build_client("plc")
    async with client:
        out = []
        for node, name in await discover_plc_variables(client):
            try:
                dv = await node.read_data_value()
            except Exception as exc:  # noqa: BLE001
                dv = exc
            out.append((node.nodeid.to_string(), name, dv))
        return out


async def run_list(target: str) -> None:
    """Print one TSV line per variable: node_id, display name, current value, type."""
    rows = await _iter_target_variables(target)
    for nid, name, dv in rows:
        if isinstance(dv, Exception):
            print(f"{nid}\t{name}\t<read failed: {dv}>")
            continue
        vtype = dv.Value.VariantType.name if dv.Value else "?"
        value = dv.Value.Value if dv.Value else None
        print(f"{nid}\t{name}\t{value!r}\t{vtype}")


async def run_write(target: str, node_id: str, raw_value: str) -> None:
    """Write `raw_value` to `node_id` on `target`. The value is parsed using
    the node's current VariantType.

    DataValue is built without timestamps — the Omron NX server rejects
    WriteValue with any timestamp populated (`BadWriteNotSupported`)."""
    if target == "leuze":
        from . import leuze  # noqa: F401 — apply LenientCertificate patch

    client = await build_client(target)
    url = require_env(f"VINEAPP_OPCUA_{target.upper()}_URL")
    print(f"Connecting to {url} ...", flush=True)
    async with client:
        node = client.get_node(node_id)
        current = await node.read_data_value()
        vtype = current.Value.VariantType
        print(f"  {node_id} before = {current.Value.Value!r} ({vtype.name})", flush=True)
        parsed = _parse_value(raw_value, vtype)
        await node.write_value(ua.DataValue(ua.Variant(parsed, vtype)))
        readback = await node.read_value()
        print(f"  {node_id} after  = {readback!r}", flush=True)


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


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m production_control.opcua.monitor",
        description="Subscribe, list, or write OPC UA nodes on the PLC/Leuze.",
    )
    sub = parser.add_subparsers(dest="cmd")

    sub.add_parser("monitor", help="Subscribe and emit JSONL to stdout (default)")

    p_list = sub.add_parser("list", help="Discover variables and print their current values")
    p_list.add_argument("--target", choices=("plc", "leuze"), default="plc")

    p_write = sub.add_parser("write", help="Write a value to a node")
    p_write.add_argument("--target", choices=("plc", "leuze"), default="plc")
    p_write.add_argument(
        "--node", required=True, help="NodeId, e.g. 'ns=4;s=OPCScanner/.../ScanResultaat'"
    )
    p_write.add_argument(
        "--value",
        required=True,
        help="Value to write; parsed using the node's current VariantType",
    )
    return parser


def cli() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )
    logging.getLogger("asyncua").setLevel(logging.WARNING)

    args = _build_parser().parse_args()
    cmd = args.cmd or "monitor"

    try:
        if cmd == "monitor":
            asyncio.run(main())
        elif cmd == "list":
            asyncio.run(run_list(args.target))
        elif cmd == "write":
            asyncio.run(run_write(args.target, args.node, args.value))
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass


if __name__ == "__main__":
    cli()
