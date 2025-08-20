"""Active potting lot service."""

import logging
from datetime import datetime
from typing import Dict, Optional

from nicegui import binding

from .repositories import PottingLotRepository
from .active_models import ActivePottingLot

logger = logging.getLogger(__name__)


class ActivePottingLotService:
    """In-memory service for managing active potting lots with reactive binding."""

    # Use bindable property for reactive updates across all UI instances
    active_lots_state = binding.BindableProperty()

    def __init__(self, potting_lot_repository: PottingLotRepository):
        """Initialize the service with a potting lot repository."""
        self._potting_lot_repository = potting_lot_repository
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

        return active_lot

    def deactivate_lot(self, line: int) -> bool:
        """Deactivate the currently active lot on a specific line."""
        if line in self._active_lots:
            del self._active_lots[line]
            # Update bindable property to trigger UI updates
            self.active_lots_state = dict(self._active_lots)  # Create new dict to trigger change
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
