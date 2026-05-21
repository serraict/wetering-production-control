"""Steps that drive the Leuze side of the protocol."""

import asyncio

from asyncua import Client, ua
from behave import when

from production_control.opcua.protocol import LEUZE_LAST_SCAN_NODEID

ENDPOINT = "opc.tcp://127.0.0.1:4840"


async def _write(node_id, value, variant):
    client = Client(url=ENDPOINT)
    async with client:
        await client.get_node(node_id).write_value(value, variant)


@when('a scan arrives with payload "{payload}"')
def step_scan_arrives(context, payload):
    asyncio.run(_write(LEUZE_LAST_SCAN_NODEID, payload, ua.VariantType.String))
