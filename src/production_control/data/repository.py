"""Base repository for Dremio data access."""

import os
from typing import Optional, Union, Tuple

from sqlalchemy import Engine, create_engine

from .pagination import Pagination


class RepositoryError(Exception):
    """Base exception for repository errors."""

    pass


class InvalidParameterError(RepositoryError):
    """Exception raised for invalid parameter values."""

    pass


class DremioRepository:
    """Base repository for Dremio data access.

    Currently using Dremio Flight protocol which doesn't support parameterized queries.
    """

    def __init__(self, connection: Optional[Union[str, Engine]] = None):
        """Initialize repository with optional connection string or engine."""
        if isinstance(connection, Engine):
            self.engine = connection
        else:
            conn_str = os.getenv(
                "VINEAPP_DB_CONNECTION",
                "dremio+flight://bot:serra1bot@localhost:32010/dremio?UseEncryption=false",
            )
            self.engine = create_engine(conn_str)

    def _validate_pagination(
        self,
        page: int = 1,
        items_per_page: int = 10,
        sort_by: Optional[str] = None,
        descending: bool = False,
        pagination: Optional[Pagination] = None,
    ) -> Tuple[int, int, Optional[str], bool]:
        """Validate and normalize pagination parameters.

        Args:
            page: The page number (1-based)
            items_per_page: Number of items per page
            sort_by: Column name to sort by
            descending: Sort in descending order if True
            pagination: Optional Pagination object that overrides other parameters

        Returns:
            Tuple of (page, items_per_page, sort_by, descending)

        Raises:
            InvalidParameterError: If pagination parameters are invalid
        """
        if pagination is not None:
            page = pagination.page
            items_per_page = pagination.rows_per_page
            sort_by = pagination.sort_by
            descending = pagination.descending

        if page < 1:
            raise InvalidParameterError("Page number must be greater than 0")
        if items_per_page < 1:
            raise InvalidParameterError("Items per page must be greater than 0")

        return page, items_per_page, sort_by, descending
