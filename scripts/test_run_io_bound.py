#!/usr/bin/env python3
"""Test if run.io_bound works with OPC controller."""

import asyncio
import logging
import random

from nicegui import run
from production_control.potting_lots.line_controller import get_controller

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def test_send_activation_to_controller(line: int, lot_id: int) -> None:
    """Test the exact _send_activation_to_controller method."""
    controller = get_controller()

    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        success = loop.run_until_complete(controller.set_active_lot(line, lot_id))

        if success:
            action = "activated" if lot_id > 0 else "deactivated"
            logger.info(f"Successfully {action} lot {lot_id} on line {line} via OPC/UA")
        else:
            logger.warning(f"Failed to send lot activation to OPC/UA for line {line}")

    except Exception as e:
        logger.error(f"Error communicating with OPC/UA controller: {e}")
    finally:
        loop.close()


def test_run_io_bound():
    """Test using run.io_bound like the web app does."""
    random_value = random.randint(10000, 99999)

    print("🧪 Testing run.io_bound approach")
    print(f"   Will write {random_value} to Line 2 using run.io_bound")

    # This is exactly what the web app does
    run.io_bound(test_send_activation_to_controller, 2, random_value)

    print("   run.io_bound call completed")
    print("   Waiting 3 seconds for background operation...")

    import time

    time.sleep(3)  # Give it time to complete

    print("   Checking if value was written...")


if __name__ == "__main__":
    print("🧪 run.io_bound OPC Write Test")
    print("Testing if run.io_bound works with OPC controller\n")

    test_run_io_bound()
    print("   Test completed!")
