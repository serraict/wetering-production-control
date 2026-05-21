#!/usr/bin/env python3
"""Write values to PLC protocol variables.

Usage:
    uv run python scripts/write_plc_vars.py --scan 27246
    uv run python scripts/write_plc_vars.py --partij1 12345 --partij2 67890
    uv run python scripts/write_plc_vars.py --scan 27246 --partij1 12345 --partij2 67890
    uv run python scripts/write_plc_vars.py --clear
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

VARS = {
    "scan": "ScanResultaat",
    "partij1": "ActievePartijnummer1",
    "partij2": "ActievePartijnummer2",
}


async def main(values: dict[str, int]):
    client = Client(PLC_ENDPOINT)
    client.application_uri = APPLICATION_URI
    client.set_user("Marijn")
    client.set_password("12345678")
    await client.set_security_string(
        f"Basic256Sha256,SignAndEncrypt,{CERT_PATH},{KEY_PATH}"
    )

    async with client:
        logger.info("Connected to Omron PLC")

        for key, val in values.items():
            node_id = VARS[key]
            node = client.get_node(f"ns=4;s={node_id}")
            await node.write_value(ua.DataValue(ua.Variant(val, ua.VariantType.Int32)))
            readback = await node.read_value()
            print(f"  {node_id} = {readback}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Write PLC protocol variables")
    parser.add_argument("--scan", type=int, help="ScanResultaat value")
    parser.add_argument("--partij1", type=int, help="ActievePartijnummer1 value")
    parser.add_argument("--partij2", type=int, help="ActievePartijnummer2 value")
    parser.add_argument("--clear", action="store_true", help="Set all to 0")
    args = parser.parse_args()

    if args.clear:
        values = {"scan": 0, "partij1": 0, "partij2": 0}
    else:
        values = {}
        if args.scan is not None:
            values["scan"] = args.scan
        if args.partij1 is not None:
            values["partij1"] = args.partij1
        if args.partij2 is not None:
            values["partij2"] = args.partij2

    if not values:
        parser.error("Provide at least one of --scan, --partij1, --partij2, or --clear")

    asyncio.run(main(values))
