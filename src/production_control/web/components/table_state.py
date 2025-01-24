"""Table state management."""

from dataclasses import dataclass, field
from typing import List, Any, Dict

from nicegui import app

from ...data import Pagination


@dataclass
class ClientStorageTableState:
    """Server-side table state."""

    pagination: Pagination
    filter: str = ""
    warning_filter: bool = False
    rows: List[Any] = field(default_factory=list)
    storage_key: str = field(default="")

    @classmethod
    def initialize(cls, storage_key: str) -> "ClientStorageTableState":
        """Initialize table state in storage if not exists."""
        if storage_key not in app.storage.client:
            app.storage.client[storage_key] = {
                "pagination": Pagination(),
                "filter": "",
                "warning_filter": False,
                "rows": [],
            }
        return cls(
            pagination=app.storage.client[storage_key]["pagination"],
            filter=app.storage.client[storage_key]["filter"],
            warning_filter=app.storage.client[storage_key]["warning_filter"],
            rows=app.storage.client[storage_key]["rows"],
            storage_key=storage_key,
        )

    def update_from_request(self, event: Dict[str, Any]) -> None:
        """Update state from table request event."""
        self.pagination.update(
            event["pagination"] if isinstance(event, dict) else event.args["pagination"]
        )
        self._save()

    def update_filter(self, text: str) -> None:
        """Update filter and reset to first page."""
        self.filter = text
        self.pagination.page = 1
        self._save()

    def update_warning_filter(self, enabled: bool) -> None:
        """Update warning filter and reset to first page."""
        self.warning_filter = enabled
        self.pagination.page = 1
        self._save()

    def update_rows(self, rows: List[Any], total: int) -> None:
        """Update rows and total count."""
        self.rows = rows
        self.pagination.total_rows = total
        self._save()

    def _save(self) -> None:
        """Save state to storage."""
        app.storage.client[self.storage_key] = {
            "pagination": self.pagination,
            "filter": self.filter,
            "warning_filter": self.warning_filter,
            "rows": self.rows,
        }
