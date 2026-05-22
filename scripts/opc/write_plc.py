"""Write values to the Omron PLC's OPCScanner protocol variables.

Manual counterpart to the protocol daemon (writes ScanResultaat) and the
web app's PottingLineController (writes ActievePartijnummer{1,2}). Useful
for forcing a guard state or simulating an operator activation outside
the normal flow.

Pre-builds the DataValue with no timestamps so the Omron NX server
accepts the write (see
work/notes/ontstapelmachine/protocol_v1_capture.md).

Connection config is read from the same VINEAPP_OPCUA_* env vars as the
web app — see docs/deployment.md. Set VINEAPP_OPCUA_SECURITY=none to
talk to the local test server anonymously without certs.

Usage:
    python scripts/opc/write_plc.py --scanresultaat 27246
    python scripts/opc/write_plc.py --partij1 12345 --partij2 67890
    python scripts/opc/write_plc.py --clear
"""

import argparse
import asyncio
import logging

from asyncua import ua

from production_control.opcua.config import build_client, require_env

PROTOCOL_NODES: dict[str, str] = {
    "scanresultaat": "ns=4;s=OPCScanner/fbOPC/ScanResultaat",
    "partij1": "ns=4;s=OPCScanner/fbOPC/ActievePartijnummer1",
    "partij2": "ns=4;s=OPCScanner/fbOPC/ActievePartijnummer2",
}


async def write_values(values: dict[str, int]) -> None:
    client = await build_client("plc")
    url = require_env("VINEAPP_OPCUA_PLC_URL")
    print(f"Connecting to {url} ...", flush=True)
    async with client:
        for key, val in values.items():
            node_id = PROTOCOL_NODES[key]
            node = client.get_node(node_id)
            await node.write_value(ua.DataValue(ua.Variant(val, ua.VariantType.Int32)))
            readback = await node.read_value()
            print(f"  {node_id} = {readback}", flush=True)


def parse_args() -> dict[str, int]:
    parser = argparse.ArgumentParser(description="Write PLC OPCScanner protocol variables")
    for key in PROTOCOL_NODES:
        parser.add_argument(f"--{key}", type=int, help=f"value for {PROTOCOL_NODES[key]}")
    parser.add_argument("--clear", action="store_true", help="set all protocol variables to 0")
    args = parser.parse_args()

    if args.clear:
        return {key: 0 for key in PROTOCOL_NODES}

    values: dict[str, int] = {
        key: getattr(args, key) for key in PROTOCOL_NODES if getattr(args, key) is not None
    }
    if not values:
        parser.error("Provide at least one of --" + ", --".join(PROTOCOL_NODES) + ", or --clear")
    return values


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("asyncua").setLevel(logging.WARNING)
    asyncio.run(write_values(parse_args()))
