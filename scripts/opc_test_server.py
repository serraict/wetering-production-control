#!/usr/bin/env python3
"""Programmatic OPC/UA server for potting lines - creates nodes in code instead of XML."""

import asyncio
import logging
from datetime import datetime
from typing import Dict

from asyncua import Server, ua
from asyncua.common.node import Node

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Suppress noisy asyncua logs
logging.getLogger("asyncua.server").setLevel(logging.WARNING)
logging.getLogger("asyncua.common").setLevel(logging.WARNING)


class ProgrammaticPottingServer:
    """OPC/UA server that creates potting line nodes programmatically."""

    def __init__(self, endpoint: str = "opc.tcp://127.0.0.1:4840/potting-lines/"):
        self.endpoint = endpoint
        self.server = Server()
        self.namespace_uri = "http://wetering.potlilium.nl/potting-lines"
        self.namespace_idx = None

        # Node references for easy access
        self.nodes: Dict[str, Node] = {}

    async def setup_server(self):
        """Configure the OPC/UA server."""
        await self.server.init()

        # Set server endpoint
        self.server.set_endpoint(self.endpoint)

        # Set server name and description
        self.server.set_server_name("Potting Lines OPC/UA Server")

        # Register our namespace
        self.namespace_idx = await self.server.register_namespace(self.namespace_uri)
        logger.info(f"Registered namespace '{self.namespace_uri}' with index {self.namespace_idx}")

        # Set security policies (allow anonymous access for testing)
        self.server.set_security_policy([ua.SecurityPolicyType.NoSecurity])

    async def create_nodes(self):
        """Create the potting line nodes programmatically."""
        objects = self.server.get_objects_node()

        # Create root PottingLines object
        potting_lines = await objects.add_object(
            f"ns={self.namespace_idx};s=PottingLines", "PottingLines"
        )
        self.nodes["PottingLines"] = potting_lines
        logger.info("Created PottingLines root object")

        # Create lines 1 and 2 with PC and OS components/variables
        for line in [1, 2]:
            # Create line object
            line_obj = await potting_lines.add_object(
                f"ns={self.namespace_idx};s=Lijn{line}", f"Lijn{line}"
            )
            self.nodes[f"Lijn{line}"] = line_obj

            # Create PC component
            pc_obj = await line_obj.add_object(f"ns={self.namespace_idx};s=Lijn{line}_PC", "PC")
            self.nodes[f"Lijn{line}_PC"] = pc_obj

            # Create PC variable
            pc_var = await pc_obj.add_variable(
                f"ns={self.namespace_idx};s=Lijn{line}_PC_nr_actieve_partij",
                "nr_actieve_partij",
                0,
                ua.VariantType.Int32,
            )
            await pc_var.set_writable(True)
            self.nodes[f"Lijn{line}_PC_nr_actieve_partij"] = pc_var

            # Create OS component
            os_obj = await line_obj.add_object(f"ns={self.namespace_idx};s=Lijn{line}_OS", "OS")
            self.nodes[f"Lijn{line}_OS"] = os_obj

            # Create OS variable
            os_var = await os_obj.add_variable(
                f"ns={self.namespace_idx};s=Lijn{line}_OS_partij_nr_actieve_pallet",
                "partij_nr_actieve_pallet",
                0,
                ua.VariantType.Int32,
            )
            await os_var.set_writable(True)
            self.nodes[f"Lijn{line}_OS_partij_nr_actieve_pallet"] = os_var

        # Create global timestamp variable
        timestamp_var = await potting_lines.add_variable(
            f"ns={self.namespace_idx};s=last_updated",
            "last_updated",
            datetime(2025, 8, 21, 9, 30, 0),
            ua.VariantType.DateTime,
        )
        await timestamp_var.set_writable(True)
        self.nodes["last_updated"] = timestamp_var

        logger.info(f"Created {len(self.nodes)} nodes programmatically")

    async def start_server(self):
        """Start the OPC/UA server."""
        try:
            await self.setup_server()
            await self.create_nodes()

            # Start the server
            async with self.server:
                logger.info(f"🚀 OPC/UA Server started at {self.endpoint}")
                logger.info(f"📍 Namespace: {self.namespace_uri} (index: {self.namespace_idx})")
                logger.info("Server is running... Press Ctrl+C to stop")

                # Keep server running
                while True:
                    await asyncio.sleep(1)

        except KeyboardInterrupt:
            logger.info("⏹️  Server stopped by user")
        except Exception as e:
            logger.error(f"💥 Server error: {e}")
            raise


async def main():
    """Main function."""
    server = ProgrammaticPottingServer()
    await server.start_server()


if __name__ == "__main__":
    print("🚀 Programmatic OPC/UA Potting Lines Server")
    print("This server creates all nodes programmatically instead of using XML import")
    print()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
