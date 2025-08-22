"""Potting line controller for OPC/UA machine communication."""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from typing import Optional, Dict
from contextlib import asynccontextmanager

from asyncua import Client, ua
from asyncua.ua import uaerrors

from ..config import get_opc_config, OPCConfig

logger = logging.getLogger(__name__)


class ConnectionStatus(Enum):
    """OPC/UA connection status."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class PottingLineController:
    """Production-ready service for communicating with potting line machines via OPC/UA."""

    def __init__(self, config: Optional[OPCConfig] = None):
        # Load configuration
        self.config = config or get_opc_config()

        # Connection settings
        self.endpoint = self.config.endpoint
        self.connection_timeout = self.config.connection_timeout
        self.watchdog_interval = self.config.watchdog_interval
        self.retry_attempts = self.config.retry_attempts
        self.retry_delay = self.config.retry_delay

        # Use regular client with proper configuration for production reliability
        self.client = Client(url=self.endpoint)

        # Configure timeouts (in milliseconds)
        self.client.request_timeout = self.connection_timeout * 1000
        self.client.secure_channel_timeout = self.watchdog_interval * 1000
        self.status = ConnectionStatus.DISCONNECTED
        self.last_error: Optional[str] = None
        self.last_connection_attempt: Optional[datetime] = None

        # Define our namespace URI (matches XML)
        self._namespace_uri = "http://wetering.potlilium.nl/potting-lines"
        self._namespace_index = None  # Will be resolved at runtime

        # Use string-based NodeIds - these are stable and namespace-independent!
        self._node_ids: Dict[str, str] = {
            "line1_pc_active": "Lijn1_PC_nr_actieve_partij",
            "line1_os_active": "Lijn1_OS_partij_nr_actieve_pallet",
            "line2_pc_active": "Lijn2_PC_nr_actieve_partij",
            "line2_os_active": "Lijn2_OS_partij_nr_actieve_pallet",
            "last_updated": "last_updated",
        }

        logger.info(f"Initialized OPC controller for environment: {self.config.environment}")

    async def connect(self) -> bool:
        """Connect to the OPC/UA server with retry logic and proper error handling."""
        if self.status == ConnectionStatus.CONNECTED:
            return True

        for attempt in range(self.retry_attempts):
            try:
                self.status = ConnectionStatus.CONNECTING
                self.last_connection_attempt = datetime.now()
                logger.info(
                    f"Connecting to OPC/UA server at {self.endpoint} (attempt {attempt + 1}/{self.retry_attempts})"
                )

                # Connect and test basic functionality
                await self.client.connect()

                # Test connection by reading a basic server node
                try:
                    # Just test that we can read the server's root node
                    root = self.client.get_objects_node()
                    logger.debug(f"Successfully connected - root node: {root}")
                finally:
                    # Always disconnect after connection test
                    await self.client.disconnect()

                self.status = ConnectionStatus.CONNECTED
                self.last_error = None
                logger.info("Successfully connected to OPC/UA server")
                return True

            except uaerrors.BadConnectionClosed as e:
                logger.warning(f"Connection closed: {e}")
                self.last_error = f"Connection closed: {e}"

            except uaerrors.BadTimeout as e:
                logger.warning(f"Connection timeout: {e}")
                self.last_error = f"Connection timeout: {e}"

            except Exception as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                self.last_error = str(e)

            if attempt < self.retry_attempts - 1:
                logger.info(f"Retrying connection in {self.retry_delay} seconds...")
                await asyncio.sleep(self.retry_delay)
                self.retry_delay *= 1.5  # Exponential backoff

        self.status = ConnectionStatus.ERROR
        logger.error(f"Failed to connect after {self.retry_attempts} attempts")
        return False

    async def disconnect(self) -> None:
        """Disconnect from the OPC/UA server with proper cleanup."""
        if self.status == ConnectionStatus.CONNECTED:
            try:
                await self.client.disconnect()
                logger.info("Disconnected from OPC/UA server")
            except Exception as e:
                logger.error(f"Error during disconnect: {e}")

        self.status = ConnectionStatus.DISCONNECTED

    async def _resolve_namespace_index(self, client):
        """Resolve our namespace URI to the runtime namespace index."""
        if self._namespace_index is None:
            try:
                # Get the server's namespace array
                ns_array = await client.get_namespace_array()
                if self._namespace_uri in ns_array:
                    self._namespace_index = ns_array.index(self._namespace_uri)
                    logger.debug(
                        f"Resolved namespace '{self._namespace_uri}' to index {self._namespace_index}"
                    )
                else:
                    logger.error(
                        f"Namespace '{self._namespace_uri}' not found in server namespace array"
                    )
                    raise ValueError(f"Namespace '{self._namespace_uri}' not found")
            except Exception as e:
                logger.error(f"Failed to resolve namespace: {e}")
                raise
        return self._namespace_index

    @asynccontextmanager
    async def _get_connected_client(self):
        """Get a connected client with automatic connection management."""
        # Create a fresh client for this operation to avoid threading issues
        client = Client(url=self.endpoint)
        client.request_timeout = self.connection_timeout * 1000
        client.secure_channel_timeout = self.watchdog_interval * 1000

        try:
            await client.connect()
            # Resolve namespace index on first connection
            await self._resolve_namespace_index(client)
            yield client
        finally:
            try:
                await client.disconnect()
            except Exception as e:
                logger.debug(f"Error during client disconnect: {e}")

    async def set_active_lot(self, line: int, lot_id: int, component: str = "PC") -> bool:
        """Set the active lot number for a potting line with retry logic.

        Args:
            line: Potting line number (1 or 2)
            lot_id: Potting lot ID (0 for no active lot)
            component: Component type ("PC" or "OS")

        Returns:
            True if successful, False otherwise
        """
        if component.upper() == "PC":
            node_key = f"line{line}_pc_active"
        elif component.upper() == "OS":
            node_key = f"line{line}_os_active"
        else:
            logger.error(f"Invalid component: {component}")
            return False

        if node_key not in self._node_ids:
            logger.error(f"Invalid line number: {line}")
            return False

        for attempt in range(self.retry_attempts):
            try:
                async with self._get_connected_client() as client:
                    # Use string-based NodeId with resolved namespace index
                    ns_idx = self._namespace_index
                    node_id = f"ns={ns_idx};s={self._node_ids[node_key]}"
                    node = client.get_node(node_id)
                    await node.write_value(lot_id, ua.VariantType.Int32)

                    logger.info(f"Successfully set line {line} {component} active lot to {lot_id}")
                    return True

            except uaerrors.BadTimeout as e:
                logger.warning(f"Write timeout on attempt {attempt + 1}: {e}")
                self.last_error = f"Write timeout: {e}"

            except uaerrors.BadConnectionClosed as e:
                logger.warning(f"Connection closed during write attempt {attempt + 1}: {e}")
                self.last_error = f"Connection closed: {e}"
                self.status = ConnectionStatus.DISCONNECTED

            except Exception as e:
                logger.warning(f"Write attempt {attempt + 1} failed: {e}")
                self.last_error = str(e)

            if attempt < self.retry_attempts - 1:
                await asyncio.sleep(self.retry_delay * (attempt + 1))

        logger.error(
            f"Failed to set active lot for line {line} after {self.retry_attempts} attempts"
        )
        return False

    async def get_active_lot(self, line: int, component: str = "PC") -> Optional[int]:
        """Get the active lot number for a potting line with retry logic.

        Args:
            line: Potting line number (1 or 2)
            component: Component type ("PC" or "OS")

        Returns:
            Active lot ID, or None if error
        """
        if component.upper() == "PC":
            node_key = f"line{line}_pc_active"
        elif component.upper() == "OS":
            node_key = f"line{line}_os_active"
        else:
            logger.error(f"Invalid component: {component}")
            return None

        if node_key not in self._node_ids:
            logger.error(f"Invalid line number: {line}")
            return None

        for attempt in range(self.retry_attempts):
            try:
                async with self._get_connected_client() as client:
                    # Use string-based NodeId with resolved namespace index
                    ns_idx = self._namespace_index
                    node_id = f"ns={ns_idx};s={self._node_ids[node_key]}"
                    node = client.get_node(node_id)
                    value = await node.read_value()
                    return int(value) if value is not None else 0

            except uaerrors.BadTimeout as e:
                logger.warning(f"Read timeout on attempt {attempt + 1}: {e}")
                self.last_error = f"Read timeout: {e}"

            except uaerrors.BadConnectionClosed as e:
                logger.warning(f"Connection closed during read attempt {attempt + 1}: {e}")
                self.last_error = f"Connection closed: {e}"
                self.status = ConnectionStatus.DISCONNECTED

            except Exception as e:
                logger.warning(f"Read attempt {attempt + 1} failed: {e}")
                self.last_error = str(e)

            if attempt < self.retry_attempts - 1:
                await asyncio.sleep(self.retry_delay * (attempt + 1))

        logger.error(
            f"Failed to get active lot for line {line} after {self.retry_attempts} attempts"
        )
        return None

    async def initialize_lines(self) -> bool:
        """Initialize both potting lines to no active lot (0).

        This should be called at application startup.

        Returns:
            True if successful, False otherwise
        """
        logger.info("Initializing potting lines to no active lot")

        try:
            # Use asyncio.gather for concurrent initialization
            results = await asyncio.gather(
                self.set_active_lot(1, 0), self.set_active_lot(2, 0), return_exceptions=True
            )

            success = all(result is True for result in results)

            if success:
                logger.info("Successfully initialized potting lines")
            else:
                logger.error(f"Failed to initialize one or more potting lines: {results}")

            return success

        except Exception as e:
            logger.error(f"Error during line initialization: {e}")
            return False

    def get_status(self) -> Dict:
        """Get current controller status information."""
        return {
            "status": self.status.value,
            "endpoint": self.endpoint,
            "last_error": self.last_error,
            "last_connection_attempt": (
                self.last_connection_attempt.isoformat() if self.last_connection_attempt else None
            ),
            "cached_node_ids": len(self._node_ids),
            "namespace_uri": self._namespace_uri,
            "resolved_namespace_index": self._namespace_index,
            "connection_timeout": self.connection_timeout,
            "watchdog_interval": self.watchdog_interval,
            "retry_attempts": self.retry_attempts,
        }


# Global controller instance for dependency injection
_global_controller: Optional[PottingLineController] = None


def get_controller() -> PottingLineController:
    """Get the global potting line controller instance with current configuration."""
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
