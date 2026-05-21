#!/usr/bin/env python3
"""OPC/UA test server that mirrors the production protocol surface.

Exposes:
- ns=4 (urn:omron:OPCScanner):  the Omron-shaped PLC nodes
    OPCScanner/fbOPC/ScanResultaat            Int32 RW
    OPCScanner/fbOPC/ActievePartijnummer1     Int32 RW
    OPCScanner/fbOPC/ActievePartijnummer2     Int32 RW
    OPCScanner/fbOPC/AantalBollenPerKrat      Int32 RW
    DeviceStatus.Mode                          String
    DeviceStatus.ErrorStatus                   String
- ns=5 (urn:leuze:DCR202iC):    the Leuze scanner LastScanData
    i=6122  LastScanData                       String RW

Optional OS simulator: when env var OPC_TEST_OS_ACK_DELAY_MS is set to a
positive integer, a background task polls ScanResultaat every 100 ms and
resets it to 0 after the configured delay once it goes non-zero. By
default the OS simulator is disabled — behave steps drive resets
explicitly so they own the timing.

Run:
    uv run python scripts/opc_test_server.py
"""

import asyncio
import logging
import os

from asyncua import Server, ua

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("opc_test_server")
logging.getLogger("asyncua.server").setLevel(logging.WARNING)
logging.getLogger("asyncua.common").setLevel(logging.WARNING)

ENDPOINT = "opc.tcp://127.0.0.1:4840"

OMRON_NS_URI = "urn:omron:OPCScanner"
LEUZE_NS_URI = "urn:leuze:DCR202iC"

# Force the PLC namespace to land at ns=4 and Leuze at ns=5 by registering
# placeholders for ns=2 and ns=3. (asyncua auto-registers OPC UA standard
# at ns=0 and the server's own URI at ns=1.)
PADDING_NAMESPACES = ["urn:opc-test:padding-2", "urn:opc-test:padding-3"]


async def _register_namespaces(server: Server) -> tuple[int, int]:
    for uri in PADDING_NAMESPACES:
        await server.register_namespace(uri)
    omron_idx = await server.register_namespace(OMRON_NS_URI)
    leuze_idx = await server.register_namespace(LEUZE_NS_URI)
    assert omron_idx == 4, f"expected Omron namespace at index 4, got {omron_idx}"
    assert leuze_idx == 5, f"expected Leuze namespace at index 5, got {leuze_idx}"
    return omron_idx, leuze_idx


async def _create_plc_nodes(server: Server, ns: int) -> None:
    objects = server.nodes.objects

    opc_scanner = await objects.add_object(f"ns={ns};s=OPCScanner", "OPCScanner")
    fb_opc = await opc_scanner.add_object(f"ns={ns};s=OPCScanner/fbOPC", "fbOPC")

    for name in ("ScanResultaat", "ActievePartijnummer1", "ActievePartijnummer2",
                 "AantalBollenPerKrat"):
        var = await fb_opc.add_variable(
            f"ns={ns};s=OPCScanner/fbOPC/{name}", name, 0, ua.VariantType.Int32
        )
        await var.set_writable(True)

    device_status = await objects.add_object(f"ns={ns};s=DeviceStatus", "DeviceStatus")
    for name, value in (("Mode", "RUN"), ("ErrorStatus", "None")):
        var = await device_status.add_variable(
            f"ns={ns};s=DeviceStatus.{name}", name, value, ua.VariantType.String
        )
        # Read-only on production; writable here so tests can inject states.
        await var.set_writable(True)


async def _create_leuze_nodes(server: Server, ns: int) -> None:
    objects = server.nodes.objects
    # Production exposes LastScanData with a numeric NodeId (ns=5;i=6122).
    # asyncua's add_variable with `nodeid=` accepts a NodeId object — build
    # one explicitly so the numeric form matches the real device.
    leuze_obj = await objects.add_object(f"ns={ns};s=Leuze", "Leuze")
    last_scan = await leuze_obj.add_variable(
        ua.NodeId(6122, ns), "LastScanData", "", ua.VariantType.String
    )
    await last_scan.set_writable(True)


async def _os_simulator(server: Server, omron_ns: int, ack_delay_ms: int) -> None:
    """Optional auto-ack loop: poll ScanResultaat; when non-zero, sleep the
    configured delay and reset to 0. Disabled when ack_delay_ms <= 0."""
    if ack_delay_ms <= 0:
        return
    node = server.get_node(f"ns={omron_ns};s=OPCScanner/fbOPC/ScanResultaat")
    logger.info("OS simulator enabled (ack delay %d ms)", ack_delay_ms)
    while True:
        try:
            value = await node.read_value()
            if value != 0:
                await asyncio.sleep(ack_delay_ms / 1000.0)
                await node.write_value(0, ua.VariantType.Int32)
                logger.info("OS-sim: ScanResultaat %s → 0", value)
            else:
                await asyncio.sleep(0.1)
        except Exception as exc:  # pragma: no cover — diagnostic only
            logger.warning("OS-sim error: %r", exc)
            await asyncio.sleep(0.5)


async def main() -> None:
    ack_delay_ms = int(os.environ.get("OPC_TEST_OS_ACK_DELAY_MS", "0"))

    server = Server()
    await server.init()
    server.set_endpoint(ENDPOINT)
    server.set_server_name("Production Control test OPC/UA server")
    server.set_security_policy([ua.SecurityPolicyType.NoSecurity])

    omron_ns, leuze_ns = await _register_namespaces(server)
    await _create_plc_nodes(server, omron_ns)
    await _create_leuze_nodes(server, leuze_ns)

    async with server:
        logger.info("test server up at %s (Omron ns=%d, Leuze ns=%d)",
                    ENDPOINT, omron_ns, leuze_ns)
        sim_task = asyncio.create_task(_os_simulator(server, omron_ns, ack_delay_ms))
        try:
            while True:
                await asyncio.sleep(1)
        finally:
            sim_task.cancel()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
