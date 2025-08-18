"""Active potting lot service."""

from typing import Dict, Optional

from .repositories import PottingLotRepository
from .active_models import ActivePottingLot


class ActivePottingLotService:
    """In-memory service for managing active potting lots."""

    def __init__(self, potting_lot_repository: PottingLotRepository):
        """Initialize the service with a potting lot repository."""
        self._active_lots: Dict[int, ActivePottingLot] = {}  # line -> active lot
        self._potting_lot_repository = potting_lot_repository

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

        return active_lot

    def deactivate_lot(self, line: int) -> bool:
        """Deactivate the currently active lot on a specific line."""
        if line in self._active_lots:
            del self._active_lots[line]
            return True
        return False
