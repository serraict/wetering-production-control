#!/usr/bin/env python3
"""Test multiple consecutive OPC writes to verify the fix."""

import asyncio
import logging
import random
import time
import threading

from asyncua import Client, ua

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Suppress noisy asyncua logs
logging.getLogger("asyncua.client").setLevel(logging.WARNING)
logging.getLogger("asyncua.common").setLevel(logging.WARNING)


async def write_to_opc_server(line: int, lot_id: int) -> bool:
    """Write to OPC server using string NodeIds with namespace resolution."""
    endpoint = "opc.tcp://127.0.0.1:4840/potting-lines/"
    client = Client(url=endpoint)
    namespace_uri = "http://wetering.potlilium.nl/potting-lines"

    try:
        await client.connect()

        # Resolve namespace index
        ns_array = await client.get_namespace_array()
        if namespace_uri not in ns_array:
            logger.error(f"Namespace '{namespace_uri}' not found")
            return False
        ns_idx = ns_array.index(namespace_uri)

        # Get node using string NodeId
        node_id_string = f"Lijn{line}_PC_nr_actieve_partij"
        node_id = f"ns={ns_idx};s={node_id_string}"
        active_node = client.get_node(node_id)

        # Write the value
        await active_node.write_value(lot_id, ua.VariantType.Int32)
        return True

    except Exception as e:
        logger.error(f"Failed to write to OPC server: {e}")
        return False
    finally:
        await client.disconnect()


def send_activation_to_controller(line: int, lot_id: int) -> None:
    """Send activation using the same threading approach as the fixed active service."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        success = loop.run_until_complete(write_to_opc_server(line, lot_id))

        if success:
            action = "activated" if lot_id > 0 else "deactivated"
            print(f"✅ Successfully {action} lot {lot_id} on line {line} via OPC/UA")
        else:
            print(f"❌ Failed to send lot activation to OPC/UA for line {line}")

    except Exception as e:
        print(f"💥 Error communicating with OPC/UA controller: {e}")
    finally:
        loop.close()


def test_multiple_writes():
    """Test multiple consecutive writes using threading."""
    print("🧪 Testing Multiple Consecutive OPC Writes")
    print("This simulates multiple lot activations in quick succession\n")

    # Test data: multiple random values
    test_writes = [
        (1, random.randint(1000, 9999)),
        (2, random.randint(1000, 9999)),
        (1, random.randint(1000, 9999)),
        (2, random.randint(1000, 9999)),
        (1, 0),  # deactivate
        (2, 0),  # deactivate
    ]

    print("Planned writes:")
    for i, (line, value) in enumerate(test_writes, 1):
        print(f"  {i}. Line {line} <- {value}")

    print(f"\n🚀 Starting {len(test_writes)} consecutive writes...")

    # Start all writes with slight delays (simulating real usage)
    threads = []
    for i, (line, value) in enumerate(test_writes):
        time.sleep(0.5)  # Small delay between starts

        thread = threading.Thread(
            target=send_activation_to_controller, args=(line, value), daemon=True
        )
        thread.start()
        threads.append(thread)
        print(f"  Started write {i + 1}: Line {line} <- {value}")

    # Wait for all threads to complete
    print("\n⏳ Waiting for all writes to complete...")
    for thread in threads:
        thread.join()

    print("✅ All writes completed!")

    # Give a moment for the last operations to finish
    time.sleep(2)

    print("\n📊 Final values:")


if __name__ == "__main__":
    test_multiple_writes()

    # Read final values
    print("📖 Reading final OPC values...")
    import subprocess

    result = subprocess.run(
        ["python", "scripts/opc_monitor.py", "--once"], capture_output=True, text=True
    )
    print(result.stdout)
