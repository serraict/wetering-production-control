"""Base repository for Dremio data access."""

import os
from typing import Optional, Union

from sqlalchemy import Engine, create_engine


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
