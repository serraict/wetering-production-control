"""Products page implementation."""

from typing import Dict, Any

from nicegui import APIRouter, ui

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
from ..components.table_utils import format_row
from ..components.table_state import ClientStorageTableState


router = APIRouter(prefix="/products")


@ui.refreshable
def server_side_paginated_table(
    cls, state: ClientStorageTableState, on_request, title="Items", row_actions={}
) -> ui.table:
    """Create a refreshable table component."""
    table = ServerSidePaginatingTable(
        model_class=cls,
        rows=state.rows,
        title=title,
        pagination=state.pagination,
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
    table_state = ClientStorageTableState.initialize("products_table")

    with frame("Producten"):
        with ui.card().classes(CARD_CLASSES.replace("max-w-3xl", "max-w-5xl")):
            with ui.row().classes("w-full justify-between items-center mb-4"):
                ui.label("Producten Overzicht").classes(HEADER_CLASSES)
                ui.input(
                    placeholder="Zoek producten...",
                    on_change=lambda e: handle_filter(e),
                ).classes("w-64").mark("search")

            async def handle_filter(e: Any) -> None:
                """Handle changes to the search filter."""
                table_state.update_filter(e.value if e.value else "")
                handle_table_request({"pagination": table_state.pagination.to_dict()})

            def handle_table_request(event: Dict[str, Any]) -> None:
                """Handle table request events."""
                table_state.update_from_request(event)

                products, total = repository.get_paginated(
                    pagination=table_state.pagination,
                    filter_text=table_state.filter,
                )

                table_state.update_rows([format_row(p) for p in products], total)
                server_side_paginated_table.refresh()

            row_actions = {
                "view": {
                    "icon": "visibility",
                    "handler": lambda e: ui.navigate.to(f"/products/{e.args.get('key')}"),
                }
            }

            server_side_paginated_table(
                Product, table_state, handle_table_request, row_actions=row_actions
            )
            handle_table_request({"pagination": table_state.pagination.to_dict()})


@router.page("/{product_id:int}")
def product_detail(product_id: int) -> None:
    """Render the product detail page."""
    repository = ProductRepository()

    with frame("Product Details"):
        product = repository.get_by_id(product_id)

        if product:
            with ui.row().classes("w-full justify-between items-center mb-6"):
                ui.link("← Terug naar Producten", "/products").classes(LINK_CLASSES)

            display_model_card(product, title=product.name)
        else:
            show_error("Product niet gevonden")
            ui.link("← Terug naar Producten", "/products").classes(LINK_CLASSES + " mt-4")
