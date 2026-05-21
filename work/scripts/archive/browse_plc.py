#!/usr/bin/env python3
"""Browse the Omron PLC OPC/UA namespace.

Usage:
    uv run python scripts/browse_plc.py
    uv run python scripts/browse_plc.py --depth 5
"""

import argparse
import asyncio
import logging

from asyncua import Client, ua

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
logging.getLogger("asyncua").setLevel(logging.WARNING)

PLC_ENDPOINT = "opc.tcp://192.168.50.36:4840"
APPLICATION_URI = "urn:Laptopper:UnifiedAutomation:UaExpert"
CERT_PATH = "certs/uaexpert_martin/uaexpert.der"
KEY_PATH = "certs/uaexpert_martin/uaexpert_key.pem"


async def browse_node(node, depth: int, indent: int = 0):
    """Recursively browse and print OPC/UA nodes."""
    children = await node.get_children()
    for child in children:
        name = await child.read_browse_name()
        node_class = await child.read_node_class()
        prefix = "  " * indent

        if node_class == ua.NodeClass.Variable:
            try:
                value = await child.read_value()
                print(f"{prefix}{name.Name} = {value!r} (NodeId: {child.nodeid})")
            except Exception:
                print(f"{prefix}{name.Name} (NodeId: {child.nodeid}) [unreadable]")
        else:
            print(f"{prefix}{name.Name}/ (NodeId: {child.nodeid})")

        if depth > 1:
            await browse_node(child, depth - 1, indent + 1)


async def main(depth: int):
    client = Client(PLC_ENDPOINT)
    client.application_uri = APPLICATION_URI
    client.set_user("Marijn")
    client.set_password("12345678")
    await client.set_security_string(
        f"Basic256Sha256,SignAndEncrypt,{CERT_PATH},{KEY_PATH}"
    )

    async with client:
        logger.info("Connected to Omron PLC")
        root = client.get_root_node()
        print(f"\nBrowsing {PLC_ENDPOINT} (depth={depth}):\n")
        await browse_node(root, depth)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Browse Omron PLC via OPC/UA")
    parser.add_argument("--depth", type=int, default=3, help="Browse depth (default: 3)")
    args = parser.parse_args()

    asyncio.run(main(args.depth))
