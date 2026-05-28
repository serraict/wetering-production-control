"""Potting lots module.

Top-level re-exports are limited to the lightweight model + repository.
The heavier symbols (`LabelGenerator`, `ActivePottingLot`,
`ActivePottingLotService`) pull in jinja2, weasyprint, and nicegui;
import them from their submodules directly. Keeping this `__init__`
slim lets the bot package import `PottingLot` without dragging in
FastAPI through nicegui.
"""

from .models import PottingLot
from .repositories import PottingLotRepository

__all__ = [
    "PottingLot",
    "PottingLotRepository",
]
