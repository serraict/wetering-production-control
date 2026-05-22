"""Uitrijden page implementation."""

import os
from typing import Dict, Any

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


router = APIRouter(prefix="/uitrijden")


def get_repository() -> Vloerplan19cmRepository:
    return Vloerplan19cmRepository()


async def sync_to_olsthoorn() -> Dict[str, Any]:
    """Write tuin_nr_plan to TEELTPL.TUINNUMMER for every mismatching row."""
    pending = get_repository().get_pending_olsthoorn_sync()

    if not pending:
        return {"success": True, "message": "Geen wijzigingen nodig"}

    port = int(os.getenv("NICEGUI_PORT", "8080"))
    api_base_url = f"http://localhost:{port}"
    api_url = "/api/firebird/update-tuin-nr"

    errors = []
    success_count = 0
    async with httpx.AsyncClient(base_url=api_base_url) as client:
        for row in pending:
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


async def handle_sync_click(button, pending_state: _PendingState) -> None:
    button.disable()
    button.props("loading")
    try:
        result = await sync_to_olsthoorn()
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
