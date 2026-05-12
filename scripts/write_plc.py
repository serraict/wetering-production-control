"""Write values to the Omron PLC's OPCScanner protocol variables.

Goal 3 from work/doing.md. Same connection pattern as monitor_plc.py.

WARNING: the OPC UA user currently has read/write on all exposed nodes.
Until the PLC role is restricted to the protocol nodes only, this script
is a sharp tool — only pass node names from PROTOCOL_NODES below.

Env vars (all required except where noted):
    VINEAPP_OPCUA_PLC_URL       opc.tcp://<plc-host>:4840
    VINEAPP_OPCUA_PLC_USER
    VINEAPP_OPCUA_PLC_PASSWORD
    VINEAPP_OPCUA_CLIENT_CERT   path to client_cert.der
    VINEAPP_OPCUA_CLIENT_KEY    path to client_cert_key.pem
    VINEAPP_OPCUA_CLIENT_APP_URI  (optional, default urn:serra:production-control-client)

Usage:
    python scripts/write_plc.py --scanresultaat 27246
    python scripts/write_plc.py --partij1 12345 --partij2 67890
    python scripts/write_plc.py --ziftmaat1 10 --ziftmaat2 12
    python scripts/write_plc.py --clear
"""

import argparse
import asyncio
import logging
import os
import sys

from asyncua import Client, ua
from asyncua.crypto.security_policies import SecurityPolicyBasic256Sha256

DEFAULT_APP_URI = "urn:serra:production-control-client"

PROTOCOL_NODES: dict[str, str] = {
    "scanresultaat": "ns=4;s=OPCScanner/fbOPC/ScanResultaat",
    "partij1": "ns=4;s=OPCScanner/fbOPC/ActievePartijnummer1",
    "partij2": "ns=4;s=OPCScanner/fbOPC/ActievePartijnummer2",
    "ziftmaat1": "ns=4;s=OPCScanner/fbOPC/Ziftmaat1",
    "ziftmaat2": "ns=4;s=OPCScanner/fbOPC/Ziftmaat2",
}


def env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        print(f"missing env var: {name}", file=sys.stderr)
        sys.exit(2)
    return value


async def write_values(values: dict[str, int]) -> None:
    url = env("VINEAPP_OPCUA_PLC_URL")
    client = Client(url=url)
    client.application_uri = os.environ.get("VINEAPP_OPCUA_CLIENT_APP_URI", DEFAULT_APP_URI)
    client.set_user(env("VINEAPP_OPCUA_PLC_USER"))
    client.set_password(env("VINEAPP_OPCUA_PLC_PASSWORD"))

    await client.set_security(
        SecurityPolicyBasic256Sha256,
        certificate=env("VINEAPP_OPCUA_CLIENT_CERT"),
        private_key=env("VINEAPP_OPCUA_CLIENT_KEY"),
        mode=ua.MessageSecurityMode.SignAndEncrypt,
    )

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
