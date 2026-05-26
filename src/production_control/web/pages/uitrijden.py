"""Uitrijden page implementation."""

import os
from datetime import date, timedelta
from typing import Any, Dict, Iterable, List, Set

import httpx
from nicegui import APIRouter, ui

from ...vloerplan.repositories import Vloerplan19cmRepository
from ...vloerplan.models import Vloerplan19cm
from ..components import frame
from ..components.model_detail_page import (
    create_model_view_action,
    create_scan_action,
    display_model_detail_page,
)
from ..components.model_list_page import display_model_list_page
from ..components.table_utils import format_date


router = APIRouter(prefix="/uitrijden")

SYNC_RECENT_DAYS = 7


def get_repository() -> Vloerplan19cmRepository:
    return Vloerplan19cmRepository()


def default_sync_selection(rows: Iterable[Vloerplan19cm], today: date) -> Set[int]:
    """Ids checked by default: rows with a known oppotdatum older than SYNC_RECENT_DAYS."""
    cutoff = today - timedelta(days=SYNC_RECENT_DAYS)
    return {
        row.id
        for row in rows
        if row.datum_oppot_plan is not None and row.datum_oppot_plan <= cutoff
    }


async def sync_to_olsthoorn(rows: List[Vloerplan19cm]) -> Dict[str, Any]:
    """Write tuin_nr_plan to TEELTPL.TUINNUMMER for each row in `rows`."""
    if not rows:
        return {"success": True, "message": "Geen wijzigingen nodig"}

    port = int(os.getenv("NICEGUI_PORT", "8080"))
    api_base_url = f"http://localhost:{port}"
    api_url = "/api/firebird/update-tuin-nr"

    errors = []
    success_count = 0
    async with httpx.AsyncClient(base_url=api_base_url) as client:
        for row in rows:
            try:
                response = await client.post(
                    api_url,
                    json={"teeltnr": row.id, "new_tuinnummer": row.tuin_nr_plan},
                    timeout=10.0,
                )
                if response.status_code == 200:
                    success_count += 1
                else:
                    errors.append(f"{row.id}: {response.text}")
            except Exception as e:
                errors.append(f"{row.id}: {e}")

    if errors:
        return {
            "success": False,
            "message": f"{success_count} bijgewerkt, {len(errors)} fouten: {'; '.join(errors[:3])}",
        }
    return {"success": True, "message": f"{success_count} tuinen bijgewerkt in Olsthoorn"}


class _PendingState:
    """Tracks how many rows still need to be synced to Olsthoorn."""

    def __init__(self, count: int):
        self.count = count

    @property
    def badge(self) -> str:
        return str(self.count) if self.count > 0 else ""


async def _confirm_sync_selection(pending: List[Vloerplan19cm]) -> List[Vloerplan19cm]:
    """Show the confirmation dialog. Returns rows the user wants to sync (empty if cancelled)."""
    selected: Set[int] = default_sync_selection(pending, date.today())

    def _toggle(row_id: int, checked: bool) -> None:
        if checked:
            selected.add(row_id)
        else:
            selected.discard(row_id)

    with ui.dialog() as dialog, ui.card().classes("w-full max-w-3xl"):
        ui.label("Sync naar Olsthoorn").classes("text-xl font-bold")
        ui.label(
            f"{len(pending)} regels met afwijkende tuin. "
            f"Lots opgepot in de laatste {SYNC_RECENT_DAYS} dagen staan standaard uit."
        ).classes("text-sm text-gray-600")

        with ui.scroll_area().classes("w-full").style("max-height: 60vh; min-height: 240px"):
            with ui.grid(columns=5).classes("w-full items-center gap-x-4 gap-y-1"):
                ui.label("").classes("font-bold")
                ui.label("Lot id").classes("font-bold")
                ui.label("Oppotdatum").classes("font-bold")
                ui.label("Tuin plan").classes("font-bold")
                ui.label("Tuin Olsthoorn").classes("font-bold")
                for row in pending:
                    cb = ui.checkbox(value=row.id in selected)
                    cb.on_value_change(lambda e, rid=row.id: _toggle(rid, bool(e.value)))
                    ui.label(str(row.id))
                    ui.label(format_date(row.datum_oppot_plan))
                    ui.label(str(row.tuin_nr_plan) if row.tuin_nr_plan is not None else "-")
                    ui.label(
                        str(row.tuin_nr_olsthoorn) if row.tuin_nr_olsthoorn is not None else "-"
                    )

        with ui.row().classes("w-full justify-end gap-2"):
            ui.button("Annuleer", on_click=lambda: dialog.submit(False)).props("flat")
            ui.button(
                "Sync",
                icon="sync",
                color="primary",
                on_click=lambda: dialog.submit(True),
            )

    accepted = await dialog
    if not accepted:
        return []
    return [row for row in pending if row.id in selected]


async def handle_sync_click(button, pending_state: _PendingState) -> None:
    pending = get_repository().get_pending_olsthoorn_sync()
    if not pending:
        ui.notify("Geen wijzigingen nodig", type="positive")
        return

    rows_to_sync = await _confirm_sync_selection(pending)
    if not rows_to_sync:
        return

    button.disable()
    button.props("loading")
    try:
        result = await sync_to_olsthoorn(rows_to_sync)
        ui.notify(result["message"], type="positive" if result["success"] else "negative")
        pending_state.count = get_repository().count_pending_olsthoorn_sync()
    finally:
        button.props(remove="loading")
        button.enable()


@router.page("/")
def uitrijden_page() -> None:
    # Uitrijden rows ARE potting lots (same id), so the scan action
    # routes to the lot's content page directly, skipping the
    # `/potting-lots/scan/{id}` redirect entry point.
    from .scan import router as scan_router

    row_actions = {
        "view": create_model_view_action(
            repository=get_repository(),
            dialog=True,
        ),
        "scan": create_scan_action(
            scan_url_for=lambda id: scan_router.url_path_for("view_batch", id=id),
        ),
    }

    pending_state = _PendingState(get_repository().count_pending_olsthoorn_sync())

    with frame("Uitrijden"):
        with ui.row().classes("w-full justify-end mb-4"):
            sync_button = ui.button(
                "Sync naar Olsthoorn",
                icon="sync",
                color="primary",
            )
            sync_button.tooltip("Schrijf 'tuin plan' naar Olsthoorn voor alle afwijkende regels")
            with sync_button:
                ui.badge(color="red").bind_text_from(pending_state, "badge").bind_visibility_from(
                    pending_state, "count", backward=lambda c: c > 0
                ).props("floating")
            sync_button.on_click(lambda: handle_sync_click(sync_button, pending_state))

        display_model_list_page(
            repository=get_repository(),
            model_cls=Vloerplan19cm,
            table_state_key="uitrijden_table",
            title="Uitrijden",
            row_actions=row_actions,
        )


@router.page("/{id}")
def uitrijden_detail(id: int) -> None:
    record = get_repository().get_by_id(id)

    with frame("Uitrijden Details"):
        display_model_detail_page(
            model=record,
            title="Uitrijden Details",
            back_link_text="← Terug naar Uitrijden",
            back_link_url="/uitrijden",
        )
