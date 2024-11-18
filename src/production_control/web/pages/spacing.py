"""Spacing page implementation."""

from typing import List, Dict, Any

from nicegui import APIRouter, ui

from ...spacing.models import SpacingRepository
from ..components import frame
from ..components.styles import CARD_CLASSES, HEADER_CLASSES


router = APIRouter(prefix="/spacing")


@router.page("/")
def spacing_page() -> None:
    """Render the spacing page."""
    repository = SpacingRepository()

    with frame("Spacing"):
        with ui.card().classes(CARD_CLASSES.replace("max-w-3xl", "max-w-5xl")):
            # Header section
            ui.label("Wijderzetten Overzicht").classes(HEADER_CLASSES)

            columns: List[Dict[str, Any]] = [
                {
                    "name": "partij_code",
                    "label": "Partij Code",
                    "field": "partij_code",
                    "sortable": True,
                },
                {
                    "name": "product_naam",
                    "label": "Product",
                    "field": "product_naam",
                    "sortable": True,
                },
                {
                    "name": "productgroep_naam",
                    "label": "Productgroep",
                    "field": "productgroep_naam",
                    "sortable": True,
                },
                {
                    "name": "aantal_tafels_totaal",
                    "label": "Totaal Tafels",
                    "field": "aantal_tafels_totaal",
                    "sortable": True,
                },
                {
                    "name": "wijderzet_registratie_fout",
                    "label": "Heeft Fout",
                    "field": "wijderzet_registratie_fout",
                },
                {"name": "actions", "label": "Acties", "field": "actions"},
            ]

            ui.table(
                columns=columns,
                rows=[],  # Empty rows for now
                row_key="id",
            ).classes("w-full")
