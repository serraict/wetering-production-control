#!/usr/bin/env python3
"""Test 0c: Check if PLC protocol variables exist.

Tries to read last_scan_data, actieve_partij_nummer_1, actieve_partij_nummer_2
from the Omron PLC.

Usage:
    uv run python scripts/test_00c_plc_protocol_vars.py
"""

import asyncio
import logging

from asyncua import Client

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
logging.getLogger("asyncua").setLevel(logging.WARNING)

PLC_ENDPOINT = "opc.tcp://192.168.50.36:4840"
APPLICATION_URI = "urn:Laptopper:UnifiedAutomation:UaExpert"
CERT_PATH = "certs/uaexpert_martin/uaexpert.der"
KEY_PATH = "certs/uaexpert_martin/uaexpert_key.pem"

PROTOCOL_VARS = {
    "ScanResultaat": "last_scan_data (int32, 0 = ready)",
    "ActievePartijnummer1": "actieve_partij_nummer_1 (int32, 0 = no active batch)",
    "ActievePartijnummer2": "actieve_partij_nummer_2 (int32, 0 = no active batch)",
}


async def main():
    client = Client(PLC_ENDPOINT)
    client.application_uri = APPLICATION_URI
    client.set_user("Marijn")
    client.set_password("12345678")
    await client.set_security_string(
        f"Basic256Sha256,SignAndEncrypt,{CERT_PATH},{KEY_PATH}"
    )

    async with client:
        logger.info("Connected to Omron PLC")

        print("\n--- Protocol variables ---")
        for node_id, description in PROTOCOL_VARS.items():
            node = client.get_node(f"ns=4;s={node_id}")
            try:
                value = await node.read_value()
                print(f"  {node_id} = {value!r}  ({description})")
            except Exception as e:
                print(f"  {node_id} -> ERROR: {e}  ({description})")


if __name__ == "__main__":
    asyncio.run(main())
