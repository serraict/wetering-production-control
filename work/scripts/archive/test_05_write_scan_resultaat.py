#!/usr/bin/env python3
"""Test 5: Write scan result to PLC and read back.

Writes a value to ScanResultaat, reads it back, then clears to 0.

Usage:
    uv run python scripts/test_05_write_scan_resultaat.py
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

        node = client.get_node("ns=4;s=ScanResultaat")

        # Read initial value
        initial = await node.read_value()
        print(f"\n  ScanResultaat initial = {initial}")

        # Write simulated batch number
        print("\n--- Test 5: Write scan result ---")
        await node.write_value(ua.DataValue(ua.Variant(27246, ua.VariantType.Int32)))

        value = await node.read_value()
        print(f"  ScanResultaat = {value} (expected 27246)")
        assert value == 27246, f"Expected 27246, got {value}"
        print("  PASS")

        # Clear back to 0
        print("\n--- Clear ScanResultaat ---")
        await node.write_value(ua.DataValue(ua.Variant(0, ua.VariantType.Int32)))

        value = await node.read_value()
        print(f"  ScanResultaat = {value} (expected 0)")
        assert value == 0, f"Expected 0, got {value}"
        print("  PASS")


if __name__ == "__main__":
    asyncio.run(main())
