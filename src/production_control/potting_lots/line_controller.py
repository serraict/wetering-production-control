"""Potting line controller for OPC/UA machine communication.

Writes the active partij to the Omron PLC over OPC/UA using the protocol
NodeIds (`ns=4;s=OPCScanner/fbOPC/ActievePartijnummer{1,2}`). See
`docs/protocol.md` for the contract.

The OS-side reads from earlier versions are gone — they were never wired
through to shipped UI and the protocol surface doesn't include them.
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Dict, Optional

from asyncua import Client, ua
from asyncua.crypto.security_policies import SecurityPolicyBasic256Sha256

from ..config import get_opc_config, OPCConfig

logger = logging.getLogger(__name__)

DEFAULT_APP_URI = "urn:serra:production-control-client"
ACTIVE_PARTIJ_NODEIDS: Dict[int, str] = {
    1: "ns=4;s=OPCScanner/fbOPC/ActievePartijnummer1",
    2: "ns=4;s=OPCScanner/fbOPC/ActievePartijnummer2",
}


def _env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"missing env var: {name}")
    return value


def _secure_default() -> bool:
    return os.environ.get("VINEAPP_OPCUA_SECURITY", "").lower() != "none"


class PottingLineController:
    """Writes the active partij to the PLC's `ActievePartijnummer{1,2}`."""

    def __init__(self, config: Optional[OPCConfig] = None, *, secure: Optional[bool] = None):
        self.config = config or get_opc_config()
        self.endpoint = os.environ.get("VINEAPP_OPCUA_PLC_URL", self.config.endpoint)
        self.connection_timeout = self.config.connection_timeout
        self.watchdog_interval = self.config.watchdog_interval
        self.retry_attempts = self.config.retry_attempts
        self.retry_delay = self.config.retry_delay

        self.secure = _secure_default() if secure is None else secure
        self.last_error: Optional[str] = None
        self.last_connection_attempt: Optional[datetime] = None

        logger.info(
            "Initialized OPC controller (endpoint=%s, secure=%s)", self.endpoint, self.secure
        )

    @asynccontextmanager
    async def _get_connected_client(self):
        client = Client(url=self.endpoint)
        client.request_timeout = self.connection_timeout * 1000
        client.secure_channel_timeout = self.watchdog_interval * 1000
        client.application_uri = os.environ.get("VINEAPP_OPCUA_CLIENT_APP_URI", DEFAULT_APP_URI)
        if self.secure:
            client.set_user(_env("VINEAPP_OPCUA_PLC_USER"))
            client.set_password(_env("VINEAPP_OPCUA_PLC_PASSWORD"))
            await client.set_security(
                SecurityPolicyBasic256Sha256,
                certificate=_env("VINEAPP_OPCUA_CLIENT_CERT"),
                private_key=_env("VINEAPP_OPCUA_CLIENT_KEY"),
                mode=ua.MessageSecurityMode.SignAndEncrypt,
            )
        try:
            await client.connect()
            yield client
        finally:
            try:
                await client.disconnect()
            except Exception as exc:  # pragma: no cover — best-effort
                logger.debug("disconnect error: %s", exc)

    async def set_active_lot(self, line: int, lot_id: int) -> bool:
        """Write `lot_id` to ActievePartijnummer{line}. `lot_id=0` clears it."""
        node_id = ACTIVE_PARTIJ_NODEIDS.get(line)
        if node_id is None:
            logger.error("Invalid line number: %s", line)
            return False

        for attempt in range(self.retry_attempts):
            try:
                async with self._get_connected_client() as client:
                    await client.get_node(node_id).write_value(lot_id, ua.VariantType.Int32)
                    logger.info("set line %d active partij to %d", line, lot_id)
                    return True
            except Exception as exc:
                logger.warning("write attempt %d failed: %s", attempt + 1, exc)
                self.last_error = str(exc)
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))

        logger.error("failed to set line %d active partij after %d attempts",
                     line, self.retry_attempts)
        return False

    async def get_active_lot(self, line: int) -> Optional[int]:
        """Read ActievePartijnummer{line} back from the PLC."""
        node_id = ACTIVE_PARTIJ_NODEIDS.get(line)
        if node_id is None:
            logger.error("Invalid line number: %s", line)
            return None

        for attempt in range(self.retry_attempts):
            try:
                async with self._get_connected_client() as client:
                    value = await client.get_node(node_id).read_value()
                    return int(value) if value is not None else 0
            except Exception as exc:
                logger.warning("read attempt %d failed: %s", attempt + 1, exc)
                self.last_error = str(exc)
                if attempt < self.retry_attempts - 1:
                    await asyncio.sleep(self.retry_delay * (attempt + 1))

        logger.error("failed to read line %d active partij after %d attempts",
                     line, self.retry_attempts)
        return None

    async def initialize_lines(self) -> bool:
        """Initialize both lines to 'no active partij' (0)."""
        logger.info("Initializing potting lines to no active lot")
        results = await asyncio.gather(
            self.set_active_lot(1, 0), self.set_active_lot(2, 0), return_exceptions=True
        )
        success = all(r is True for r in results)
        if not success:
            logger.error("Failed to initialize one or more potting lines: %s", results)
        return success


_global_controller: Optional[PottingLineController] = None


def get_controller() -> PottingLineController:
    global _global_controller
    if _global_controller is None:
        _global_controller = PottingLineController()
    return _global_controller


async def shutdown_controller() -> None:
    global _global_controller
    if _global_controller:
        _global_controller = None
