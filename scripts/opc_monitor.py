#!/usr/bin/env python3
"""OPC/UA server monitor script - displays current node values in real time."""

import asyncio
import logging
import sys
from datetime import datetime
from typing import Dict, Any

from asyncua import Client, ua

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Suppress noisy asyncua logs
logging.getLogger("asyncua.client").setLevel(logging.WARNING)
logging.getLogger("asyncua.common").setLevel(logging.WARNING)


class OPCMonitor:
    """Monitor OPC/UA server and display node values."""

    def __init__(self, endpoint: str = "opc.tcp://127.0.0.1:4840/potting-lines/"):
        self.endpoint = endpoint
        self.client = Client(url=endpoint)
        self._nodes: Dict[str, ua.Node] = {}
        self._connected = False

        # Define our namespace URI and NodeIds
        self._namespace_uri = "http://wetering.potlilium.nl/potting-lines"
        self._namespace_index = None
        self._node_ids = {
            "Lijn1/PC/nr_actieve_partij": "Lijn1_PC_nr_actieve_partij",
            "Lijn1/OS/partij_nr_actieve_pallet": "Lijn1_OS_partij_nr_actieve_pallet",
            "Lijn2/PC/nr_actieve_partij": "Lijn2_PC_nr_actieve_partij",
            "Lijn2/OS/partij_nr_actieve_pallet": "Lijn2_OS_partij_nr_actieve_pallet",
            "last_updated": "last_updated",
        }

    async def connect(self) -> bool:
        """Connect to OPC server and cache node references."""
        try:
            print(f"🔌 Connecting to OPC server at {self.endpoint}")
            await self.client.connect()

            # Cache node references
            await self._discover_and_cache_nodes()

            self._connected = True
            print("✅ Connected successfully!")
            return True

        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

    async def _resolve_namespace_index(self):
        """Resolve our namespace URI to the runtime namespace index."""
        if self._namespace_index is None:
            try:
                ns_array = await self.client.get_namespace_array()
                if self._namespace_uri in ns_array:
                    self._namespace_index = ns_array.index(self._namespace_uri)
                    print(f"📍 Resolved namespace to index: {self._namespace_index}")
                else:
                    raise ValueError(f"Namespace '{self._namespace_uri}' not found")
            except Exception as e:
                print(f"❌ Failed to resolve namespace: {e}")
                raise
        return self._namespace_index

    async def _discover_and_cache_nodes(self) -> None:
        """Discover and cache all relevant nodes using string NodeIds."""
        try:
            # Resolve namespace index
            await self._resolve_namespace_index()
            ns_idx = self._namespace_index

            # Cache nodes using string-based NodeIds
            for display_name, node_id_string in self._node_ids.items():
                node_id = f"ns={ns_idx};s={node_id_string}"
                self._nodes[display_name] = self.client.get_node(node_id)

            print(f"📋 Cached {len(self._nodes)} nodes")

        except Exception as e:
            print(f"⚠️  Failed to discover nodes: {e}")
            raise

    async def read_all_values(self) -> Dict[str, Any]:
        """Read values from all cached nodes."""
        values = {}

        for node_path, node in self._nodes.items():
            try:
                value = await node.read_value()
                values[node_path] = value
            except Exception as e:
                values[node_path] = f"Error: {e}"

        return values

    async def monitor_loop(self, refresh_seconds: float = 2.0) -> None:
        """Main monitoring loop - displays values continuously."""
        if not self._connected:
            print("❌ Not connected to server")
            return

        print(f"\n📊 Starting monitor (refresh every {refresh_seconds}s)")
        print("Press Ctrl+C to stop\n")

        try:
            while True:
                # Clear screen and move cursor to top
                print("\033[2J\033[H", end="")

                # Header
                print("=" * 60)
                print(f"OPC/UA Server Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Endpoint: {self.endpoint}")
                print("=" * 60)

                # Read and display all values
                values = await self.read_all_values()

                for node_path, value in values.items():
                    # Format different value types
                    if isinstance(value, datetime):
                        formatted_value = value.strftime("%Y-%m-%d %H:%M:%S")
                    elif isinstance(value, (int, float)):
                        formatted_value = str(value)
                    else:
                        formatted_value = str(value)

                    print(f"📍 {node_path:<30} = {formatted_value}")

                print("\n" + "=" * 60)
                print("Press Ctrl+C to stop monitoring")

                await asyncio.sleep(refresh_seconds)

        except KeyboardInterrupt:
            print("\n\n⏹️  Monitoring stopped by user")
        except Exception as e:
            print(f"\n❌ Monitoring error: {e}")

    async def disconnect(self) -> None:
        """Disconnect from OPC server."""
        if self._connected:
            try:
                await self.client.disconnect()
                print("🔌 Disconnected from OPC server")
            except Exception as e:
                print(f"⚠️  Error during disconnect: {e}")

        self._connected = False

    async def read_once(self) -> None:
        """Read values once and display them."""
        if not self._connected:
            print("❌ Not connected to server")
            return

        print("\n📊 Current OPC Node Values:")
        print("=" * 50)

        values = await self.read_all_values()

        for node_path, value in values.items():
            # Format different value types
            if isinstance(value, datetime):
                formatted_value = value.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(value, (int, float)):
                formatted_value = str(value)
            else:
                formatted_value = str(value)

            print(f"📍 {node_path:<30} = {formatted_value}")

        print("=" * 50)


async def main():
    """Main function."""
    # Check for --once flag
    read_once_mode = "--once" in sys.argv

    monitor = OPCMonitor()

    try:
        # Connect to server
        if not await monitor.connect():
            return

        if read_once_mode:
            # Read once and exit
            await monitor.read_once()
        else:
            # Start continuous monitoring
            await monitor.monitor_loop()

    except Exception as e:
        print(f"💥 Unexpected error: {e}")

    finally:
        await monitor.disconnect()


if __name__ == "__main__":
    if "--once" in sys.argv:
        print("🚀 OPC/UA Server Reader")
        print("Reading current node values once\n")
    else:
        print("🚀 OPC/UA Server Monitor")
        print("This script monitors the potting line OPC server and displays node values")
        print("Use --once flag to read values once and exit\n")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
