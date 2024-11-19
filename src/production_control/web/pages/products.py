"""Products page implementation."""

from typing import Dict, Any

from nicegui import APIRouter, ui, app

from ...products.models import ProductRepository, Product
from ..components import frame
from ..components.model_card import display_model_card
from ..components.message import show_error
from ..components.styles import (
    CARD_CLASSES,
    HEADER_CLASSES,
    LINK_CLASSES,
)
from ..components.data_table import ServerSidePaginatingTable


router = APIRouter(prefix="/products")


def format_product(product: Product) -> Dict[str, Any]:
    """Format product for table display."""
    return {
        "id": product.id,
        "name": product.name,
        "product_group_name": product.product_group_name,
    }


def initialize_table_state() -> None:
    """Initialize table state in client storage if not exists."""
    if "products_table" not in app.storage.client:
        app.storage.client["products_table"] = {
            "pagination": {
                "rowsPerPage": 10,
                "page": 1,
                "rowsNumber": 0,
                "sortBy": None,
                "descending": False,
            },
            "filter": "",
            "rows": [],
        }


@ui.refreshable
def server_side_paginated_table(cls, on_request, row_actions={}) -> ui.table:
    """Create a refreshable table component."""
    table = ServerSidePaginatingTable(
        model_class=cls,
        rows=app.storage.client["products_table"]["rows"],
        title="Products Overview",
        pagination=app.storage.client["products_table"]["pagination"],
    )

    for action_key, action in row_actions.items():
        table.add_slot(
            "body-cell-actions",
            f"""
            <q-td :props="props">
                <q-btn @click="$parent.$emit('{action_key}', props)" icon="{action['icon']}" flat dense color='primary'/>
            </q-td>
        """,
        )
        table.on(action_key, action["handler"])

    table.on("request", on_request)
    return table


@router.page("/")
def products_page() -> None:
    """Render the products page with a table of all products."""
    repository = ProductRepository()
    initialize_table_state()

    with frame("Products"):
        with ui.card().classes(CARD_CLASSES.replace("max-w-3xl", "max-w-5xl")):
            with ui.row().classes("w-full justify-between items-center mb-4"):
                ui.label("Products Overview").classes(HEADER_CLASSES)
                ui.input(
                    placeholder="Search products...",
                    on_change=lambda e: handle_filter(e),
                ).classes("w-64").mark("search")

            async def handle_filter(e: Any) -> None:
                """Handle changes to the search filter."""
                app.storage.client["products_table"]["filter"] = e.value if e.value else ""
                app.storage.client["products_table"]["pagination"]["page"] = 1
                handle_table_request(
                    {"pagination": app.storage.client["products_table"]["pagination"]}
                )

            def handle_table_request(event: Dict[str, Any]) -> None:
                """Handle table request events."""
                new_pagination = (
                    event["pagination"] if isinstance(event, dict) else event.args["pagination"]
                )
                app.storage.client["products_table"]["pagination"].update(new_pagination)

                products, total = repository.get_paginated(
                    page=new_pagination.get("page", 1),
                    items_per_page=new_pagination.get("rowsPerPage", 10),
                    sort_by=new_pagination.get("sortBy"),
                    descending=new_pagination.get("descending", False),
                    filter_text=app.storage.client["products_table"]["filter"],
                )

                app.storage.client["products_table"]["rows"] = [format_product(p) for p in products]
                app.storage.client["products_table"]["pagination"]["rowsNumber"] = total
                server_side_paginated_table.refresh()

            row_actions = {
                "view": {
                    "icon": "visibility",
                    "handler": lambda e: ui.navigate.to(f"/products/{e.args.get('key')}"),
                }
            }

            server_side_paginated_table(Product, handle_table_request, row_actions=row_actions)
            handle_table_request({"pagination": app.storage.client["products_table"]["pagination"]})
            # return table


@router.page("/{product_id:int}")
def product_detail(product_id: int) -> None:
    """Render the product detail page."""
    repository = ProductRepository()

    with frame("Product Details"):
        product = repository.get_by_id(product_id)

        if product:
            with ui.row().classes("w-full justify-between items-center mb-6"):
                ui.link("← Back to Products", "/products").classes(LINK_CLASSES)

            display_model_card(product, title=product.name)
        else:
            show_error("Product not found")
            ui.link("← Back to Products", "/products").classes(LINK_CLASSES + " mt-4")
