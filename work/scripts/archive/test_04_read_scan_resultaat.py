#!/usr/bin/env python3
"""Test 4: Read ScanResultaat from PLC, wait for OS to reset to 0.

Reads ScanResultaat and polls until it becomes 0 (OS acknowledges).

Usage:
    uv run python scripts/test_04_read_scan_resultaat.py
    uv run python scripts/test_04_read_scan_resultaat.py --watch
"""

import argparse
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


async def main(watch: bool, interval: float):
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

        value = await node.read_value()
        print(f"ScanResultaat = {value}")

        if watch:
            print(f"\nWatching for changes (poll every {interval}s, Ctrl+C to stop)...")
            previous = value
            while True:
                await asyncio.sleep(interval)
                value = await node.read_value()
                if value != previous:
                    print(f"ScanResultaat = {value}")
                    previous = value


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test 4: Read ScanResultaat from PLC")
    parser.add_argument("--watch", action="store_true", help="Poll for changes")
    parser.add_argument("--interval", type=float, default=0.5, help="Poll interval in seconds (default: 0.5)")
    args = parser.parse_args()

    asyncio.run(main(args.watch, args.interval))
