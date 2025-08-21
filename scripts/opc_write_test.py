#!/usr/bin/env python3
"""OPC/UA write test script - writes random values to test OPC server write functionality."""

import asyncio
import logging
import random
from datetime import datetime

from asyncua import Client, ua

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Suppress noisy asyncua logs
logging.getLogger("asyncua.client").setLevel(logging.WARNING)
logging.getLogger("asyncua.common").setLevel(logging.WARNING)


async def test_opc_write():
    """Test writing values to OPC server."""
    endpoint = "opc.tcp://127.0.0.1:4840/potting-lines/"
    client = Client(url=endpoint)

    try:
        print(f"🔌 Connecting to OPC server at {endpoint}")
        await client.connect()
        print("✅ Connected!")

        # Get node references
        root = client.get_objects_node()
        potting_lines = await root.get_child("2:PottingLines")

        # Get Line 1 node
        line1 = await potting_lines.get_child("2:Lijn1")
        line1_pc = await line1.get_child("2:PC")
        line1_active_node = await line1_pc.get_child("2:nr_actieve_partij")

        # Get Line 2 node
        line2 = await potting_lines.get_child("2:Lijn2")
        line2_pc = await line2.get_child("2:PC")
        line2_active_node = await line2_pc.get_child("2:nr_actieve_partij")

        # Read current values before writing
        print("\n📖 Reading current values:")
        line1_current = await line1_active_node.read_value()
        line2_current = await line2_active_node.read_value()
        print(f"   Lijn1 current value: {line1_current}")
        print(f"   Lijn2 current value: {line2_current}")

        # Generate random test values
        random_value_1 = random.randint(100, 999)
        random_value_2 = random.randint(1000, 9999)

        print(f"\n✏️  Writing test values:")
        print(f"   Lijn1 <- {random_value_1}")
        print(f"   Lijn2 <- {random_value_2}")

        # Write values using the same approach as the controller
        await line1_active_node.write_value(random_value_1, ua.VariantType.Int32)
        await line2_active_node.write_value(random_value_2, ua.VariantType.Int32)

        print("✅ Write operations completed!")

        # Read back values to verify
        print("\n📖 Reading back values to verify:")
        line1_new = await line1_active_node.read_value()
        line2_new = await line2_active_node.read_value()
        print(f"   Lijn1 new value: {line1_new}")
        print(f"   Lijn2 new value: {line2_new}")

        # Verify the writes worked
        success = True
        if line1_new != random_value_1:
            print(f"❌ Line 1 write failed! Expected {random_value_1}, got {line1_new}")
            success = False
        else:
            print("✅ Line 1 write successful!")

        if line2_new != random_value_2:
            print(f"❌ Line 2 write failed! Expected {random_value_2}, got {line2_new}")
            success = False
        else:
            print("✅ Line 2 write successful!")

        if success:
            print("\n🎉 All write operations successful!")
        else:
            print("\n💥 Some write operations failed!")

        # DON'T reset - leave values so we can check persistence

    except Exception as e:
        print(f"❌ Error: {e}")
        logger.exception("Full error details:")
    finally:
        await client.disconnect()
        print("🔌 Disconnected")


if __name__ == "__main__":
    print("🚀 OPC/UA Write Test")
    print("This script writes random test values to both potting lines\n")

    try:
        asyncio.run(test_opc_write())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
