"""Steps that drive the OS side of the protocol.

OS is the destacker; in the test it's simulated by directly writing
the PLC node.
"""

import asyncio

from asyncua import Client, ua
from behave import when

from production_control.opcua.protocol import PLC_SCAN_RESULTAAT_NODEID

ENDPOINT = "opc.tcp://127.0.0.1:4840"


async def _write(node_id, value, variant):
    client = Client(url=ENDPOINT)
    async with client:
        await client.get_node(node_id).write_value(value, variant)


@when("OS resets ScanResultaat to 0")
def step_os_resets(context):
    asyncio.run(_write(PLC_SCAN_RESULTAAT_NODEID, 0, ua.VariantType.Int32))
    context.expected_scan_resultaat = 0
