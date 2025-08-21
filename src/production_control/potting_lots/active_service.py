"""Active potting lot service."""

import logging
from datetime import datetime
from typing import Dict, Optional

from nicegui import binding

from .repositories import PottingLotRepository
from .active_models import ActivePottingLot
from .line_controller import get_controller

logger = logging.getLogger(__name__)


class ActivePottingLotService:
    """In-memory service for managing active potting lots with reactive binding."""

    # Use bindable property for reactive updates across all UI instances
    active_lots_state = binding.BindableProperty()

    def __init__(self, potting_lot_repository: PottingLotRepository):
        """Initialize the service with a potting lot repository."""
        self._potting_lot_repository = potting_lot_repository
        self._controller = get_controller()
        # Initialize with both the bindable property and the internal storage
        self._active_lots: Dict[int, ActivePottingLot] = {}  # line -> active lot
        self.active_lots_state = {}  # This will trigger UI updates when changed

    def get_active_lot_for_line(self, line: int) -> Optional[ActivePottingLot]:
        """Get the currently active lot for a specific line."""
        return self._active_lots.get(line)

    def activate_lot(self, line: int, potting_lot_id: int) -> ActivePottingLot:
        """Activate a lot on a specific line. Deactivates any previously active lot on that line."""
        # Get the potting lot details from repository
        potting_lot = self._potting_lot_repository.get_by_id(potting_lot_id)

        # Create active lot
        active_lot = ActivePottingLot(
            line=line, potting_lot_id=potting_lot_id, potting_lot=potting_lot
        )

        # Store it (automatically replaces any existing active lot for this line)
        self._active_lots[line] = active_lot

        # Update bindable property to trigger UI updates
        self.active_lots_state = dict(self._active_lots)  # Create new dict to trigger change

        # Send to OPC/UA controller (run in background thread, don't block UI)
        import threading

        thread = threading.Thread(
            target=self._send_activation_to_controller, args=(line, potting_lot_id), daemon=True
        )
        thread.start()

        return active_lot

    def deactivate_lot(self, line: int) -> bool:
        """Deactivate the currently active lot on a specific line."""
        if line in self._active_lots:
            del self._active_lots[line]
            # Update bindable property to trigger UI updates
            self.active_lots_state = dict(self._active_lots)  # Create new dict to trigger change

            # Send deactivation to OPC/UA controller (run in background thread, don't block UI)
            import threading

            thread = threading.Thread(
                target=self._send_activation_to_controller, args=(line, 0), daemon=True
            )
            thread.start()

            return True
        return False

    def complete_lot(self, line: int, actual_pots: int) -> bool:
        """Mark the active lot as completed and deactivate it.

        Args:
            line: The potting line number
            actual_pots: The actual number of pots that were planted

        Returns:
            True if completion was successful, False if no active lot found
        """
        active_lot = self.get_active_lot_for_line(line)
        if not active_lot:
            logger.warning(f"No active lot found on line {line} for completion")
            return False

        completion_time = datetime.now()

        # Log the completion
        logger.info(
            f"Completed potting lot {active_lot.potting_lot_id} "
            f"({active_lot.potting_lot.naam}) on line {line}. "
            f"Actual pots: {actual_pots}, Completed at: {completion_time}"
        )

        # TODO: In future iterations, write to technison database here
        # TODO: Update potting lot status in main database if needed

        # Auto-deactivate the lot after completion
        self.deactivate_lot(line)

        return True

    def _send_activation_to_controller(self, line: int, lot_id: int) -> None:
        """Send activation/deactivation to OPC/UA controller (runs in thread)."""
        try:
            import asyncio

            # Create a fresh event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            success = loop.run_until_complete(self._controller.set_active_lot(line, lot_id))

            if success:
                action = "activated" if lot_id > 0 else "deactivated"
                logger.info(f"Successfully {action} lot {lot_id} on line {line} via OPC/UA")
            else:
                logger.warning(f"Failed to send lot activation to OPC/UA for line {line}")

        except Exception as e:
            logger.error(f"Error communicating with OPC/UA controller: {e}")
        finally:
            loop.close()

    async def initialize_machine_communication(self) -> bool:
        """Initialize machine communication at application startup.

        Returns:
            True if successful, False otherwise
        """
        try:
            success = await self._controller.initialize_lines()
            if success:
                logger.info("Successfully initialized potting line machine communication")
            else:
                logger.warning("Failed to initialize potting line machine communication")
            return success
        except Exception as e:
            logger.error(f"Error initializing machine communication: {e}")
            return False

    def get_controller_status(self) -> dict:
        """Get the current OPC/UA controller status."""
        return self._controller.get_status()
