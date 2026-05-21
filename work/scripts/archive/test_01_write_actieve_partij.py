#!/usr/bin/env python3
"""Test 1: Write actieve_partij_nummer to PLC and read back.

Writes ActievePartijnummer1 and ActievePartijnummer2, reads them back,
then clears both to 0 (test 3).

Usage:
    uv run python scripts/test_01_write_actieve_partij.py
"""

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

        node1 = client.get_node("ns=4;s=ActievePartijnummer1")
        node2 = client.get_node("ns=4;s=ActievePartijnummer2")

        # Test 1: Write non-zero values
        print("\n--- Test 1: Write actieve_partij_nummer ---")
        await node1.write_value(ua.DataValue(ua.Variant(12345, ua.VariantType.Int32)))
        await node2.write_value(ua.DataValue(ua.Variant(67890, ua.VariantType.Int32)))

        v1 = await node1.read_value()
        v2 = await node2.read_value()
        print(f"  ActievePartijnummer1 = {v1} (expected 12345)")
        print(f"  ActievePartijnummer2 = {v2} (expected 67890)")
        assert v1 == 12345, f"Expected 12345, got {v1}"
        assert v2 == 67890, f"Expected 67890, got {v2}"
        print("  PASS")

        # Test 3: Clear to 0
        print("\n--- Test 3: Clear actieve_partij_nummer ---")
        await node1.write_value(ua.DataValue(ua.Variant(0, ua.VariantType.Int32)))
        await node2.write_value(ua.DataValue(ua.Variant(0, ua.VariantType.Int32)))

        v1 = await node1.read_value()
        v2 = await node2.read_value()
        print(f"  ActievePartijnummer1 = {v1} (expected 0)")
        print(f"  ActievePartijnummer2 = {v2} (expected 0)")
        assert v1 == 0, f"Expected 0, got {v1}"
        assert v2 == 0, f"Expected 0, got {v2}"
        print("  PASS")


if __name__ == "__main__":
    asyncio.run(main())
