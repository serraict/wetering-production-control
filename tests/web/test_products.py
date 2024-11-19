"""Tests for web interface."""

import asyncio
from unittest.mock import Mock, patch
from nicegui.testing import User
from nicegui import ui

from production_control.products.models import Product
from production_control.data import Pagination


async def test_products_page_shows_table(user: User) -> None:
    """Test that products page shows a table with product data."""
    with patch("production_control.web.pages.products.ProductRepository") as mock_repo_class:
        # Given
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_paginated.return_value = (
            [
                Product(
                    id=12,
                    name="T. Bee 13",
                    product_group_id=113,
                    product_group_name="13 aziaat",
                ),
                Product(
                    id=99,
                    name="S. Okinawa 19",
                    product_group_id=219,
                    product_group_name="19 oriëntal",
                ),
            ],
            2,  # total count
        )

        # When
        await user.open("/products")

        # Then
        table = user.find(ui.table).elements.pop()
        assert table.columns == [
            {"name": "name", "label": "Naam", "field": "name", "sortable": True},
            {
                "name": "product_group_name",
                "label": "Productgroep",
                "field": "product_group_name",
                "sortable": True,
            },
            {"name": "actions", "label": "Acties", "field": "actions"},
        ]
        assert table.rows == [
            {
                "id": 12,
                "name": "T. Bee 13",
                "product_group_name": "13 aziaat",
            },
            {
                "id": 99,
                "name": "S. Okinawa 19",
                "product_group_name": "19 oriëntal",
            },
        ]


async def test_products_page_filtering_calls_repository(user) -> None:
    """Test that entering a filter value calls the repository with the filter text."""

    with patch("production_control.web.pages.products.ProductRepository") as mock_repo_class:
        # Given
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_paginated.return_value = ([], 0)  # Empty initial result

        # An asyncio.Event to signal when the repository is called
        done_event = asyncio.Event()

        def on_get_paginated(*, pagination: Pagination = None, filter_text: str = ""):
            if filter_text == "mix":
                done_event.set()  # Set the event when desired call is made
            return [], 0

        mock_repo.get_paginated.side_effect = on_get_paginated

        # When
        await user.open("/products")
        search_box = user.find(marker="search", kind=ui.input)
        search_box.type("mix")
        search_box.trigger("change")

        # Await until the event is set, or timeout if necessary
        try:
            await asyncio.wait_for(done_event.wait(), timeout=2.0)
        except asyncio.TimeoutError:
            raise RuntimeError("Timeout while waiting for repository call.")

        # Then verify repository was called with filter
        mock_repo.get_paginated.assert_called_with(
            pagination=mock_repo.get_paginated.call_args.kwargs["pagination"],
            filter_text="mix"
        )


async def test_product_detail_page_shows_product(user: User) -> None:
    """Test that product detail page shows product information."""
    with patch("production_control.web.pages.products.ProductRepository") as mock_repo_class:
        # Given
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        test_product = Product(
            id=12,
            name="T. Bee 13",
            product_group_id=113,
            product_group_name="13 aziaat",
        )
        mock_repo.get_by_id.return_value = test_product

        # When
        await user.open("/products/12")

        # Then
        await user.should_see("T. Bee 13")
        await user.should_see("13 aziaat")
        await user.should_see("Product Details")  # Frame title
        await user.should_see("← Terug naar Producten")


async def test_product_detail_page_handles_invalid_id(user: User) -> None:
    """Test that product detail page handles invalid product ID."""
    with patch("production_control.web.pages.products.ProductRepository") as mock_repo_class:
        # Given
        mock_repo = Mock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_id.return_value = None

        # When
        await user.open("/products/999")

        # Then
        await user.should_see("Product niet gevonden")
        await user.should_see("← Terug naar Producten")
