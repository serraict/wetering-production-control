"""Scan-cycle handler: subscribes to Leuze LastScanData, parses, and
writes the parsed partij to ScanResultaat on the PLC — but only when
ScanResultaat == 0 (the guard against overwriting an unread scan).

See docs/protocol.md for the contract.
"""

from __future__ import annotations

import asyncio
import logging
from functools import partial

from asyncua import Node, ua

from .. import config
from ..config import build_client, require_env
from ..heartbeat import beat_while_alive
from ..monitor import supervise
from .scan_parser import parse_scan

logger = logging.getLogger("opcua_protocol")

SUBSCRIPTION_INTERVAL_MS = 500

PLC_SCAN_RESULTAAT_NODEID = "ns=4;s=OPCScanner/fbOPC/ScanResultaat"
PLC_AANTAL_BOLLEN_NODEID = "ns=4;s=OPCScanner/fbOPC/AantalBollenPerKrat"
LEUZE_LAST_SCAN_NODEID = "ns=5;i=6122"


def bollen_per_krat_for(partij: int) -> int:
    """Bulb count to publish for `partij` alongside ScanResultaat.

    Real source is the bollen-picklist; lookup not yet wired. Single
    seam so the protocol write path doesn't change when the lookup
    arrives.
    """
    return 600


class ScanCycleHandler:
    """asyncua subscription handler that:
    - tracks ScanResultaat (from the PLC subscription)
    - on every Leuze LastScanData change, parses + writes back when the
      guard allows.
    """

    def __init__(self) -> None:
        self._last_scan_resultaat: int = 0
        self._plc_write_node: Node | None = None
        self._plc_aantal_bollen_node: Node | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    def register(self, node: Node, name: str) -> None:
        if node.nodeid.to_string() == PLC_SCAN_RESULTAAT_NODEID:
            self._plc_write_node = node
        elif node.nodeid.to_string() == PLC_AANTAL_BOLLEN_NODEID:
            self._plc_aantal_bollen_node = node

    def attach_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        # asyncua's notification thread isn't the loop's thread, so we
        # need an explicit handle to schedule the write back.
        self._loop = loop

    # asyncua subscription handler interface -----------------------------------

    def datachange_notification(self, node: Node, val, data) -> None:
        node_id = node.nodeid.to_string()
        if node_id == PLC_SCAN_RESULTAAT_NODEID:
            self._last_scan_resultaat = int(val) if val is not None else 0
            return
        if node_id == LEUZE_LAST_SCAN_NODEID:
            self._handle_scan(val)

    def status_change_notification(self, status) -> None:  # noqa: D401
        logger.info("status: %s", status)

    def event_notification(self, event) -> None:  # noqa: D401
        pass

    # -------------------------------------------------------------------------

    def _handle_scan(self, payload) -> None:
        partij = parse_scan(payload)
        if partij is None:
            logger.warning("scan dropped: unparseable payload %r", payload)
            return
        if self._last_scan_resultaat != 0:
            logger.warning(
                "scan dropped: guard not zero (ScanResultaat=%d)",
                self._last_scan_resultaat,
            )
            return
        if (
            self._plc_write_node is None
            or self._plc_aantal_bollen_node is None
            or self._loop is None
        ):
            logger.error("scan dropped: handler not fully wired")
            return
        asyncio.run_coroutine_threadsafe(self._write(partij), self._loop)

    async def _write(self, partij: int) -> None:
        try:
            assert self._plc_write_node is not None
            assert self._plc_aantal_bollen_node is not None
            # Pre-build the DataValue so asyncua doesn't auto-set
            # SourceTimestamp; the Omron NX server rejects writes with
            # BadWriteNotSupported when any timestamp/status field is
            # populated.
            # Order matters: paired information fields must be valid
            # by the time OS observes a non-zero ScanResultaat — so
            # write AantalBollenPerKrat first, then ScanResultaat.
            bollen = bollen_per_krat_for(partij)
            await self._plc_aantal_bollen_node.write_value(
                ua.DataValue(ua.Variant(bollen, ua.VariantType.Int32))
            )
            await self._plc_write_node.write_value(
                ua.DataValue(ua.Variant(partij, ua.VariantType.Int32))
            )
            logger.info("wrote partij %d (AantalBollenPerKrat=%d) to PLC", partij, bollen)
        except Exception:  # pragma: no cover — surfaced in logs
            logger.exception("write to PLC failed")


async def _plc_loop(
    handler: ScanCycleHandler,
    ready: asyncio.Event | None,
    stop_event: asyncio.Event,
) -> None:
    client = await build_client("plc")
    url = require_env("VINEAPP_OPCUA_PLC_URL")
    logger.info("connecting to PLC at %s", url)
    async with client:
        node = client.get_node(PLC_SCAN_RESULTAAT_NODEID)
        handler.register(node, "ScanResultaat")
        aantal_node = client.get_node(PLC_AANTAL_BOLLEN_NODEID)
        handler.register(aantal_node, "AantalBollenPerKrat")
        handler.attach_loop(asyncio.get_running_loop())
        # Seed the guard with the current value before subscribing.
        try:
            initial = await node.read_value()
            handler._last_scan_resultaat = int(initial) if initial is not None else 0
        except Exception:
            logger.warning("could not read initial ScanResultaat; assuming 0")
        sub = await client.create_subscription(SUBSCRIPTION_INTERVAL_MS, handler)
        await sub.subscribe_data_change([node])
        logger.info("subscribed to ScanResultaat")
        if ready is not None:
            ready.set()
        beat = asyncio.create_task(beat_while_alive("plc", stop_event))
        try:
            await stop_event.wait()
        finally:
            beat.cancel()
            try:
                await beat
            except (asyncio.CancelledError, Exception):  # pragma: no cover
                pass
            try:
                await sub.delete()
            except Exception:  # pragma: no cover
                pass


def _make_timestamp_trigger_request(node, client_handle: int) -> ua.MonitoredItemCreateRequest:
    """Build a MonitoredItemCreateRequest with DataChangeTrigger =
    StatusValueTimestamp so identical values with fresh timestamps
    still publish (real Leuze scans repeat the same URL for a duplicate
    krat scan, but with a new SourceTimestamp)."""
    filt = ua.DataChangeFilter()
    filt.Trigger = ua.DataChangeTrigger.StatusValueTimestamp
    filt.DeadbandType = ua.DeadbandType.None_
    filt.DeadbandValue = 0.0

    mparams = ua.MonitoringParameters()
    mparams.ClientHandle = client_handle
    mparams.SamplingInterval = SUBSCRIPTION_INTERVAL_MS
    mparams.QueueSize = 1
    mparams.DiscardOldest = True
    mparams.Filter = filt

    rv = ua.ReadValueId()
    rv.NodeId = node.nodeid
    rv.AttributeId = ua.AttributeIds.Value

    mir = ua.MonitoredItemCreateRequest()
    mir.ItemToMonitor = rv
    mir.MonitoringMode = ua.MonitoringMode.Reporting
    mir.RequestedParameters = mparams
    return mir


async def _leuze_loop(
    handler: ScanCycleHandler,
    ready: asyncio.Event | None,
    stop_event: asyncio.Event,
) -> None:
    if config.current_mode() == "secure":
        # Load-bearing side-effect import: leuze.py's module body monkey-patches
        # asyncua.crypto.uacrypto so the TLS handshake survives the real Leuze's
        # malformed server cert (firmware V2.4.0). Skipped in none-mode — the
        # test server has a well-formed cert and we don't want the patch active.
        # Regression-guarded by tests/opcua/test_leuze.py.
        from .. import leuze  # noqa: F401
    client = await build_client("leuze")
    url = require_env("VINEAPP_OPCUA_LEUZE_URL")
    logger.info("connecting to Leuze at %s", url)
    async with client:
        node = client.get_node(LEUZE_LAST_SCAN_NODEID)
        handler.register(node, "LastScanData")
        sub = await client.create_subscription(SUBSCRIPTION_INTERVAL_MS, handler)
        # Use the timestamp-trigger filter rather than the default
        # subscribe_data_change (StatusValue trigger) so duplicate scans
        # still notify (real Leuze publishes the same URL with a fresh
        # SourceTimestamp on each scan).
        sub._client_handle += 1
        await sub.create_monitored_items(
            [_make_timestamp_trigger_request(node, sub._client_handle)]
        )
        logger.info("subscribed to LastScanData (timestamp-trigger)")
        if ready is not None:
            ready.set()
        beat = asyncio.create_task(beat_while_alive("leuze", stop_event))
        try:
            await stop_event.wait()
        finally:
            beat.cancel()
            try:
                await beat
            except (asyncio.CancelledError, Exception):  # pragma: no cover
                pass
            try:
                await sub.delete()
            except Exception:  # pragma: no cover
                pass


async def run_protocol(
    handler: ScanCycleHandler | None = None,
    *,
    plc_ready: asyncio.Event | None = None,
    leuze_ready: asyncio.Event | None = None,
    stop_event: asyncio.Event | None = None,
) -> None:
    """Run both subscriptions until `stop_event` fires (or cancellation).

    Each role's loop is wrapped in `supervise(..., max_attempts=None)` so
    a failure in one (e.g. Leuze unreachable) doesn't kill the other —
    previously `asyncio.gather` propagated any exception and the daemon
    crash-looped via Docker. No giveup: Docker `restart: unless-stopped`
    is the right policy when something is actually broken.

    `plc_ready` / `leuze_ready` are set once each subscription is live —
    useful for the behave harness which needs to wait before driving
    the scenario. They stay set across supervise-driven reconnects.
    """
    if handler is None:
        handler = ScanCycleHandler()
    if stop_event is None:
        stop_event = asyncio.Event()
    plc_task = asyncio.create_task(
        supervise(
            "protocol-plc",
            partial(_plc_loop, handler, plc_ready, stop_event),
            max_attempts=None,
            stop_event=stop_event,
        ),
        name="protocol-plc",
    )
    leuze_task = asyncio.create_task(
        supervise(
            "protocol-leuze",
            partial(_leuze_loop, handler, leuze_ready, stop_event),
            max_attempts=None,
            stop_event=stop_event,
        ),
        name="protocol-leuze",
    )
    try:
        await asyncio.gather(plc_task, leuze_task)
    except (asyncio.CancelledError, KeyboardInterrupt):
        stop_event.set()
        await asyncio.gather(plc_task, leuze_task, return_exceptions=True)
        raise
