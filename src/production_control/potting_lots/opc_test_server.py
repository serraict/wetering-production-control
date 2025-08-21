"""OPC/UA test server for potting line integration testing."""

import asyncio
import logging
from datetime import datetime
from typing import Dict

from asyncua import Server, ua

logger = logging.getLogger(__name__)


class PottingLineOPCTestServer:
    """Test OPC/UA server simulating potting line machine controllers."""

    def __init__(self, endpoint: str = "opc.tcp://127.0.0.1:4840/potting-lines/"):
        self.endpoint = endpoint
        self.server = Server()
        self.nodes: Dict[str, ua.Node] = {}
        self._running = False

    async def setup_server(self) -> None:
        """Set up the OPC/UA server with potting line data structure."""
        # Set up server basics
        await self.server.init()
        self.server.set_endpoint(self.endpoint)

        # Set up security (minimal for testing)
        self.server.set_security_policy(
            [
                ua.SecurityPolicyType.NoSecurity,
            ]
        )

        # Get the server namespace
        uri = "http://wetering.potlilium.nl/potting-lines"
        idx = await self.server.register_namespace(uri)

        # Create root object for potting lines
        root = await self.server.get_objects_node().add_object(idx, "PottingLines")

        # Create Line 1 structure
        line1 = await root.add_object(idx, "Lijn1")
        line1_pc = await line1.add_object(idx, "PC")
        self.nodes["line1_active"] = await line1_pc.add_variable(
            idx, "nr_actieve_partij", 0, ua.VariantType.Int32
        )
        await self.nodes["line1_active"].set_writable(True)

        # Create Line 2 structure
        line2 = await root.add_object(idx, "Lijn2")
        line2_pc = await line2.add_object(idx, "PC")
        self.nodes["line2_active"] = await line2_pc.add_variable(
            idx, "nr_actieve_partij", 0, ua.VariantType.Int32
        )
        await self.nodes["line2_active"].set_writable(True)

        # Add timestamp node for monitoring
        self.nodes["timestamp"] = await root.add_variable(
            idx, "last_updated", datetime.now(), ua.VariantType.DateTime
        )
        await self.nodes["timestamp"].set_writable(True)

        logger.info(f"OPC/UA test server set up at {self.endpoint}")
        logger.info("Available nodes:")
        logger.info("  - Lijn1/PC/nr_actieve_partij")
        logger.info("  - Lijn2/PC/nr_actieve_partij")
        logger.info("  - last_updated")

    async def start(self) -> None:
        """Start the OPC/UA server."""
        if self._running:
            return

        await self.setup_server()
        await self.server.start()
        self._running = True
        logger.info(f"OPC/UA test server started at {self.endpoint}")

    async def stop(self) -> None:
        """Stop the OPC/UA server."""
        if not self._running:
            return

        await self.server.stop()
        self._running = False
        logger.info("OPC/UA test server stopped")

    async def get_active_lot(self, line: int) -> int:
        """Get the active lot number for a line."""
        node_key = f"line{line}_active"
        if node_key in self.nodes:
            return await self.nodes[node_key].get_value()
        return 0

    async def update_timestamp(self) -> None:
        """Update the timestamp node."""
        if "timestamp" in self.nodes:
            await self.nodes["timestamp"].set_value(datetime.now())


async def main():
    """Main function to run the test server standalone."""
    logging.basicConfig(level=logging.INFO)
    
    # Suppress noisy asyncua address space messages
    logging.getLogger("asyncua.server.address_space").setLevel(logging.WARNING)

    server = PottingLineOPCTestServer()

    try:
        await server.start()
        logger.info("Test server running. Press Ctrl+C to stop.")

        # Keep server running and update timestamp periodically
        while True:
            await asyncio.sleep(5)
            await server.update_timestamp()

    except KeyboardInterrupt:
        logger.info("Shutting down test server...")
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
