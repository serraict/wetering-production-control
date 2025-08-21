#!/usr/bin/env python3
"""Test the exact same approach used by the web app for OPC writes."""

import asyncio
import logging
import random

from production_control.potting_lots.line_controller import get_controller

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_webapp_write_approach():
    """Test using the exact same approach as the web app active service."""

    controller = get_controller()
    random_value = random.randint(1000, 9999)

    print("🧪 Testing web app approach")
    print(f"   Controller status before: {controller.get_status()}")
    print(f"   Will write {random_value} to Line 1")

    # This mimics exactly what _send_activation_to_controller does
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        print("   Created new event loop")

        success = loop.run_until_complete(controller.set_active_lot(1, random_value))

        print(f"   Write operation returned: {success}")

        if success:
            print("✅ Write reported as successful")
        else:
            print("❌ Write reported as failed")

        # Also test reading back
        read_value = loop.run_until_complete(controller.get_active_lot(1))
        print(f"   Read back value: {read_value}")

        if read_value == random_value:
            print("✅ Verification successful!")
        else:
            print(f"❌ Verification failed! Expected {random_value}, got {read_value}")

    except Exception as e:
        print(f"💥 Error during web app approach test: {e}")
        logger.exception("Full error details:")
    finally:
        loop.close()
        print("   Event loop closed")

    print(f"   Controller status after: {controller.get_status()}")


if __name__ == "__main__":
    print("🧪 Web App OPC Write Approach Test")
    print("Testing the exact threading approach used by the active service\n")

    test_webapp_write_approach()
