"""Potting line controller for OPC/UA machine communication."""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Optional, Dict

from asyncua import Client, ua

logger = logging.getLogger(__name__)


class ConnectionStatus(Enum):
    """OPC/UA connection status."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class PottingLineController:
    """Service for communicating with potting line machines via OPC/UA."""

    def __init__(self, endpoint: str = "opc.tcp://127.0.0.1:4840/potting-lines/"):
        self.endpoint = endpoint
        self.client = Client(url=endpoint)
        self.status = ConnectionStatus.DISCONNECTED
        self.last_error: Optional[str] = None
        self.last_connection_attempt: Optional[datetime] = None
        self._nodes: Dict[str, ua.Node] = {}

    async def connect(self) -> bool:
        """Connect to the OPC/UA server."""
        if self.status == ConnectionStatus.CONNECTED:
            return True

        try:
            self.status = ConnectionStatus.CONNECTING
            self.last_connection_attempt = datetime.now()
            logger.info(f"Connecting to OPC/UA server at {self.endpoint}")

            await self.client.connect()

            # Cache node references for performance
            await self._cache_nodes()

            self.status = ConnectionStatus.CONNECTED
            self.last_error = None
            logger.info("Successfully connected to OPC/UA server")
            return True

        except Exception as e:
            self.status = ConnectionStatus.ERROR
            self.last_error = str(e)
            logger.error(f"Failed to connect to OPC/UA server: {e}")
            return False

    async def disconnect(self) -> None:
        """Disconnect from the OPC/UA server."""
        if self.status == ConnectionStatus.CONNECTED:
            try:
                await self.client.disconnect()
                logger.info("Disconnected from OPC/UA server")
            except Exception as e:
                logger.error(f"Error during disconnect: {e}")

        self.status = ConnectionStatus.DISCONNECTED
        self._nodes.clear()

    async def _cache_nodes(self) -> None:
        """Cache frequently used node references."""
        try:
            # Get root object
            root = self.client.get_objects_node()
            potting_lines = await root.get_child("2:PottingLines")

            # Cache Line 1 nodes
            line1 = await potting_lines.get_child("2:Lijn1")
            line1_pc = await line1.get_child("2:PC")
            self._nodes["line1_active"] = await line1_pc.get_child("2:nr_actieve_partij")

            # Cache Line 2 nodes
            line2 = await potting_lines.get_child("2:Lijn2")
            line2_pc = await line2.get_child("2:PC")
            self._nodes["line2_active"] = await line2_pc.get_child("2:nr_actieve_partij")

            logger.info("Successfully cached OPC/UA node references")

        except Exception as e:
            logger.error(f"Failed to cache OPC/UA nodes: {e}")
            raise

    async def set_active_lot(self, line: int, lot_id: int) -> bool:
        """Set the active lot number for a potting line.

        Args:
            line: Potting line number (1 or 2)
            lot_id: Potting lot ID (0 for no active lot)

        Returns:
            True if successful, False otherwise
        """
        if self.status != ConnectionStatus.CONNECTED:
            if not await self.connect():
                return False

        try:
            node_key = f"line{line}_active"
            if node_key not in self._nodes:
                logger.error(f"Node not found for line {line}")
                return False

            await self._nodes[node_key].write_value(lot_id, ua.VariantType.Int32)

            logger.info(f"Successfully set line {line} active lot to {lot_id}")
            return True

        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Failed to set active lot for line {line}: {e}")
            return False

    async def get_active_lot(self, line: int) -> Optional[int]:
        """Get the active lot number for a potting line.

        Args:
            line: Potting line number (1 or 2)

        Returns:
            Active lot ID, or None if error
        """
        if self.status != ConnectionStatus.CONNECTED:
            if not await self.connect():
                return None

        try:
            node_key = f"line{line}_active"
            if node_key not in self._nodes:
                logger.error(f"Node not found for line {line}")
                return None

            value = await self._nodes[node_key].read_value()
            return int(value) if value is not None else 0

        except Exception as e:
            self.last_error = str(e)
            logger.error(f"Failed to get active lot for line {line}: {e}")
            return None

    async def initialize_lines(self) -> bool:
        """Initialize both potting lines to no active lot (0).

        This should be called at application startup.

        Returns:
            True if successful, False otherwise
        """
        logger.info("Initializing potting lines to no active lot")

        success = True
        success &= await self.set_active_lot(1, 0)
        success &= await self.set_active_lot(2, 0)

        if success:
            logger.info("Successfully initialized potting lines")
        else:
            logger.error("Failed to initialize one or more potting lines")

        return success

    def get_status(self) -> Dict:
        """Get current controller status information."""
        return {
            "status": self.status.value,
            "endpoint": self.endpoint,
            "last_error": self.last_error,
            "last_connection_attempt": (
                self.last_connection_attempt.isoformat() if self.last_connection_attempt else None
            ),
            "connected_nodes": len(self._nodes),
        }


# Global controller instance for dependency injection
_global_controller: Optional[PottingLineController] = None


def get_controller() -> PottingLineController:
    """Get the global potting line controller instance."""
    global _global_controller
    if _global_controller is None:
        _global_controller = PottingLineController()
    return _global_controller


async def shutdown_controller() -> None:
    """Shutdown the global controller (for application cleanup)."""
    global _global_controller
    if _global_controller:
        await _global_controller.disconnect()
        _global_controller = None
