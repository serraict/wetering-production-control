"""Steps that assert on PC-side behavior: no-write guard + log capture.

Log capture is wired up in environment.py — context.warnings is a
list of LogRecord messages at WARNING+ from the `opcua_protocol`
logger, reset per scenario.
"""

import asyncio
import time

from asyncua import Client
from behave import then

from production_control.opcua.protocol import PLC_SCAN_RESULTAAT_NODEID

ENDPOINT = "opc.tcp://127.0.0.1:4840"

# Allow the handler enough time to react to a Leuze change before we
# assert "nothing happened". The Leuze subscription publishes on
# SUBSCRIPTION_INTERVAL_MS (500ms) plus parse + write overhead.
_NO_WRITE_WAIT_S = 1.2


async def _read(node_id):
    client = Client(url=ENDPOINT)
    async with client:
        return await client.get_node(node_id).read_value()


@then("PC does not write to ScanResultaat")
def step_pc_does_not_write(context):
    expected = getattr(context, "expected_scan_resultaat", None)
    assert expected is not None, (
        "step requires a prior step to set context.expected_scan_resultaat "
        "(e.g. 'Given the PLC reports ScanResultaat = N' or "
        "'When OS resets ScanResultaat to 0')"
    )
    time.sleep(_NO_WRITE_WAIT_S)
    actual = int(asyncio.run(_read(PLC_SCAN_RESULTAAT_NODEID)))
    assert actual == expected, (
        f"expected ScanResultaat to stay at {expected}, but it became {actual}"
    )


@then('PC logs "{needle}" at WARNING')
def step_pc_logs_warning(context, needle):
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline:
        for record in list(context.warnings):
            if needle in record:
                return
        time.sleep(0.05)
    raise AssertionError(
        f"no WARNING log containing {needle!r}; captured: {list(context.warnings)}"
    )
