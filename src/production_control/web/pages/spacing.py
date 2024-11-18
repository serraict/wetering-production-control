"""Spacing page implementation."""

from nicegui import APIRouter, ui

from ..components import frame
from ..components.styles import HEADER_CLASSES


router = APIRouter(prefix="/spacing")


@router.page("/")
def spacing_page() -> None:
    """Render the spacing page."""
    with frame("Spacing"):
        ui.label("Spacing Overview").classes(HEADER_CLASSES)
