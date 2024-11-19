"""Database pagination and sorting configuration."""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class Pagination:
    """Database pagination and sorting configuration.

    This class represents pagination and sorting parameters for database queries.
    It also provides conversion methods for web UI integration with Quasar tables.
    """

    page: int = 1
    rows_per_page: int = 10
    total_rows: int = 0
    sort_by: Optional[str] = None
    descending: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pagination":
        """Create pagination from dictionary (e.g. from Quasar table state)."""
        return cls(
            page=data.get("page", 1),
            rows_per_page=data.get("rowsPerPage", 10),
            total_rows=data.get("rowsNumber", 0),
            sort_by=data.get("sortBy"),
            descending=data.get("descending", False),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Quasar table."""
        return {
            "page": self.page,
            "rowsPerPage": self.rows_per_page,
            "rowsNumber": self.total_rows,
            "sortBy": self.sort_by,
            "descending": self.descending,
        }

    def update(self, data: Dict[str, Any]) -> None:
        """Update pagination state from dictionary."""
        if "page" in data:
            self.page = data["page"]
        if "rowsPerPage" in data:
            self.rows_per_page = data["rowsPerPage"]
        if "rowsNumber" in data:
            self.total_rows = data["rowsNumber"]
        if "sortBy" in data:
            self.sort_by = data["sortBy"]
        if "descending" in data:
            self.descending = data["descending"]
