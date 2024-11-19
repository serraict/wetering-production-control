"""Product data models."""

import os
from typing import List, Optional, Union, Tuple
from sqlalchemy import create_engine, func, Integer, bindparam, desc, text, distinct
from sqlalchemy.engine import Engine
from sqlmodel import Field, Session, SQLModel, select
from sqlalchemy_dremio.flight import DremioDialect_flight
from sqlalchemy.dialects import registry

from ..data import Pagination


class CustomDremioDialect(DremioDialect_flight):
    """Custom Dremio dialect that implements import_dbapi."""

    supports_statement_cache = False

    @classmethod
    def import_dbapi(cls):
        """Import DBAPI module for Dremio."""
        return DremioDialect_flight.dbapi()


# Register our custom dialect
registry.register("dremio.flight", "production_control.products.models", "CustomDremioDialect")


class Product(SQLModel, table=True):
    """View model for products we make."""

    __tablename__ = "products"
    __table_args__ = {"schema": "Vines"}

    id: int = Field(
        primary_key=True,
        title="ID",
        sa_column_kwargs={"info": {"ui_hidden": True}},
    )
    name: str = Field(
        title="Naam",
        description="Naam van het product",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_order": 1}},
    )
    product_group_id: int = Field(
        title="Productgroep ID",
        sa_column_kwargs={"info": {"ui_hidden": True}},
    )
    product_group_name: str = Field(
        title="Productgroep",
        description="Naam van de productgroep",
        sa_column_kwargs={"info": {"ui_sortable": True, "ui_order": 2}},
    )


class RepositoryError(Exception):
    """Base exception for repository errors."""

    pass


class InvalidParameterError(RepositoryError):
    """Exception raised for invalid parameter values."""

    pass


class ProductRepository:
    """Read-only repository for product data access.

    Currently using Dremio Flight protocol which doesn't support parameterized queries.
    """

    def __init__(self, connection: Optional[Union[str, Engine]] = None):
        """Initialize repository with optional connection string or engine."""
        if isinstance(connection, Engine):
            self.engine = connection
        else:
            conn_str = os.getenv("VINEAPP_DB_CONNECTION", "dremio+flight://localhost:32010/dremio")
            self.engine = create_engine(conn_str)

    def get_all(self) -> List[Product]:
        """Get all products from the data source."""
        with Session(self.engine) as session:
            statement = select(Product).order_by(Product.product_group_name, Product.name)
            result = session.execute(statement)
            return [row[0] for row in result]

    def get_by_id(self, product_id: int) -> Optional[Product]:
        """Get a product by its ID.

        Args:
            product_id: The ID of the product to retrieve

        Returns:
            The product if found, None otherwise
        """
        with Session(self.engine) as session:
            # Note: Using string interpolation because Dremio Flight doesn't support parameters
            base_query = select(Product)
            filter_expr = text(f"id = {product_id}")
            query = base_query.where(filter_expr)
            result = session.exec(query)
            return result.first()

    def get_paginated(
        self,
        page: int = 1,
        items_per_page: int = 10,
        sort_by: Optional[str] = None,
        descending: bool = False,
        filter_text: Optional[str] = None,
        pagination: Optional[Pagination] = None,
    ) -> Tuple[List[Product], int]:
        """Get paginated products from the data source.

        Args:
            page: The page number (1-based)
            items_per_page: Number of items per page
            sort_by: Column name to sort by
            descending: Sort in descending order if True
            filter_text: Optional text to filter products by (case-insensitive)
            pagination: Optional Pagination object that overrides other pagination parameters

        Returns:
            Tuple containing list of products for the requested page and total count

        Raises:
            InvalidParameterError: If pagination parameters are invalid
        """
        if pagination is not None:
            page = pagination.page
            items_per_page = pagination.rows_per_page
            sort_by = pagination.sort_by
            descending = pagination.descending

        # Validate pagination parameters
        if page < 1:
            raise InvalidParameterError("Page number must be greater than 0")
        if items_per_page < 1:
            raise InvalidParameterError("Items per page must be greater than 0")

        with Session(self.engine) as session:
            # Create base query
            base_query = select(Product)

            # Apply filter if provided
            if filter_text:
                # Note: Using string interpolation because Dremio Flight doesn't support parameters
                pattern = f"%{filter_text}%"
                filter_expr = text(
                    f"lower(name) LIKE lower('{pattern}') OR "
                    f"lower(product_group_name) LIKE lower('{pattern}')"
                )
                base_query = base_query.where(filter_expr)

            # Get total count using the same filter but without the subquery
            count_stmt = select(func.count(distinct(Product.id)))
            if filter_text:
                count_stmt = count_stmt.where(filter_expr)
            total = session.exec(count_stmt).one()

            # Calculate offset
            offset = (page - 1) * items_per_page

            # Apply sorting
            if sort_by:
                column = getattr(Product, sort_by)
                if descending:
                    base_query = base_query.order_by(desc(column))
                else:
                    base_query = base_query.order_by(column)
            else:
                # Default sorting
                base_query = base_query.order_by(Product.product_group_name, Product.name)

            # Apply pagination
            query = base_query.limit(
                bindparam("limit", type_=Integer, literal_execute=True)
            ).offset(bindparam("offset", type_=Integer, literal_execute=True))

            # Execute with bound parameters
            result = session.exec(
                query,
                params={
                    "limit": items_per_page,
                    "offset": offset,
                },
            )
            products = list(result)

            return products, total
