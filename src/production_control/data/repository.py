"""Base repository for Dremio data access."""

import os
from typing import Optional, Union, Tuple, TypeVar, List, Sequence, Generic, Type

from sqlalchemy import Engine, create_engine, Integer, bindparam, Select, text, desc
from sqlmodel import Session, SQLModel

from .pagination import Pagination


T = TypeVar("T", bound=SQLModel)


class RepositoryError(Exception):
    """Base exception for repository errors."""

    pass


class InvalidParameterError(RepositoryError):
    """Exception raised for invalid parameter values."""

    pass


class DremioRepository(Generic[T]):
    """Base repository for Dremio data access.

    Currently using Dremio Flight protocol which doesn't support parameterized queries.
    """

    def __init__(
        self,
        model: Type[T],
        connection: Optional[Union[str, Engine]] = None,
    ):
        """Initialize repository with model type and optional connection.

        Args:
            model: The model class this repository handles
            connection: Optional connection string or engine
        """
        self.model = model
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

    def _apply_text_filter(
        self,
        query: Select,
        filter_text: str,
        fields: Sequence[str],
    ) -> Select:
        """Apply case-insensitive text filter to query.

        Args:
            query: The base query to filter
            filter_text: Text to filter by
            fields: List of field names to apply filter to

        Returns:
            Query with filter applied
        """
        if not filter_text:
            return query

        # Note: Using string interpolation because Dremio Flight doesn't support parameters
        pattern = f"%{filter_text}%"
        conditions = [f"lower({field}) LIKE lower('{pattern}')" for field in fields]
        filter_expr = text(" OR ".join(conditions))
        return query.where(filter_expr)

    def _apply_sorting(
        self,
        query: Select,
        sort_by: Optional[str],
        descending: bool,
    ) -> Select:
        """Apply sorting to query.

        Args:
            query: The base query to sort
            sort_by: Column name to sort by
            descending: Sort in descending order if True

        Returns:
            Query with sorting applied
        """
        if sort_by:
            column = getattr(self.model, sort_by)
            if descending:
                query = query.order_by(desc(column))
            else:
                query = query.order_by(column)
        else:
            query = self._apply_default_sorting(query)
        return query

    def _apply_default_sorting(self, query: Select) -> Select:
        """Apply default sorting to query. Override in subclasses.

        Args:
            query: The base query to sort

        Returns:
            Query with default sorting applied
        """
        return query

    def _execute_paginated_query(
        self,
        session: Session,
        query: Select,
        count_stmt: Select,
        page: int,
        items_per_page: int,
        search_text: Optional[str] = None,
        search_fields: Optional[Sequence[str]] = None,
        sort_by: Optional[str] = None,
        descending: bool = False,
    ) -> Tuple[List[T], int]:
        """Execute a paginated query and return results with total count.

        Args:
            session: The database session
            query: The base query to execute
            count_stmt: The count query to get total records
            page: The page number (1-based)
            items_per_page: Number of items per page
            search_text: Optional text to filter by
            search_fields: Optional list of fields to search in
            sort_by: Optional column name to sort by
            descending: Sort in descending order if True

        Returns:
            Tuple containing list of items for the requested page and total count
        """
        # Apply filtering if provided
        if search_text and search_fields:
            query = self._apply_text_filter(query, search_text, search_fields)
            count_stmt = self._apply_text_filter(count_stmt, search_text, search_fields)

        # Apply sorting
        query = self._apply_sorting(query, sort_by, descending)

        # Get total count
        total = session.exec(count_stmt).one()

        # Calculate offset
        offset = (page - 1) * items_per_page

        # Apply pagination
        query = query.limit(bindparam("limit", type_=Integer, literal_execute=True)).offset(
            bindparam("offset", type_=Integer, literal_execute=True)
        )

        # Execute with bound parameters
        result = session.exec(
            query,
            params={
                "limit": items_per_page,
                "offset": offset,
            },
        )
        items = list(result)

        return items, total
