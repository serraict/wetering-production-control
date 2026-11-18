"""Per-lot Zulip conversation panel.

Rendered on the scan view; reusable from any page that has a lot-like object
(needs an `id` attribute).
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from nicegui import events, run, ui

from ...zulip_chat import service as zulip_service
from ...zulip_chat.service import ZulipMessage, ZulipServiceError
from ..auth import get_current_user

logger = logging.getLogger(__name__)

# Zulip's default upload limit is 25 MB; phone photos are well under that.
MAX_IMAGE_BYTES = 25 * 1024 * 1024


def _format_timestamp(message: ZulipMessage) -> str:
    today = datetime.now().astimezone().date()
    local = message.timestamp.astimezone()
    if local.date() == today:
        return local.strftime("%H:%M")
    return local.strftime("%Y-%m-%d %H:%M")


def _render_pinned_remark(lot: Any) -> None:
    """Render the lot's `opmerking` as a pinned message at the top of the thread."""
    remark = (getattr(lot, "opmerking", None) or "").strip()
    if not remark:
        return
    ui.chat_message(text=remark, name="Teeltopmerking").classes("w-full")


@ui.refreshable
def _messages_block(lot: Any, current_user_name: str) -> None:
    try:
        messages = zulip_service.get_messages(lot)
    except ZulipServiceError as e:
        logger.warning("Zulip get_messages failed for lot %s: %s", lot.id, e)
        _render_pinned_remark(lot)
        ui.label(f"Zulip onbereikbaar: {e}").classes("text-sm text-red-600")
        return

    with ui.column().classes("w-full gap-2"):
        _render_pinned_remark(lot)

        if not messages:
            ui.label("Nog geen berichten in deze topic.").classes("text-sm text-gray-500")
            return

        for message in messages:
            is_own = message.author_name == current_user_name
            ui.chat_message(
                text=message.body_html,
                name=None if is_own else message.author_name,
                stamp=_format_timestamp(message),
                sent=is_own,
                text_html=True,
            ).classes("w-full")


def render_communication_card(lot: Any) -> None:
    """Render the Zulip conversation card for `lot`."""
    user_name = get_current_user().get("name", "Guest")

    with ui.card().classes("w-full p-2 sm:p-4"):
        with ui.row().classes("w-full items-center justify-between mb-2"):
            ui.label("Communicatie").classes("text-sm text-gray-600 uppercase")
            narrow = zulip_service.narrow_url(lot)
            if narrow:
                ui.link("Open in Zulip", narrow, new_tab=True).classes("text-xs")

        _messages_block(lot, user_name)

        with ui.row().classes("w-full items-end gap-2 mt-3 flex-nowrap"):
            textarea = (
                ui.textarea(placeholder="Schrijf een bericht…")
                .props("outlined autogrow dense")
                .classes("flex-1")
            )

            def on_send() -> None:
                content = (textarea.value or "").strip()
                if not content:
                    return
                try:
                    zulip_service.post(lot, content, user_name=user_name)
                except ZulipServiceError as e:
                    logger.warning("Zulip post failed for lot %s: %s", lot.id, e)
                    ui.notify(f"Versturen mislukt: {e}", type="negative")
                    return
                textarea.value = ""
                _messages_block.refresh()

            async def on_image(e: events.UploadEventArguments) -> None:
                try:
                    data = await e.file.read()
                    await run.io_bound(
                        zulip_service.post_image,
                        lot,
                        e.file.name,
                        data,
                        caption=textarea.value or "",
                        user_name=user_name,
                    )
                except Exception as err:  # surface every failure; upload handlers fail silently
                    logger.warning("Image post failed for lot %s: %s", lot.id, err, exc_info=True)
                    ui.notify(f"Foto versturen mislukt: {err}", type="negative")
                    return
                finally:
                    uploader.reset()
                photo_dialog.close()
                ui.notify("Foto verstuurd", type="positive")
                textarea.value = ""
                _messages_block.refresh()

            # The uploader must be tapped directly: mobile browsers only open
            # the file picker (camera / gallery) from a real user gesture on
            # the file input, not from a server round-trip like run_method().
            with ui.dialog() as photo_dialog, ui.card().classes("items-stretch"):
                ui.label("Foto toevoegen").classes("text-sm text-gray-600 uppercase")
                ui.label("Tekst in het berichtveld wordt het onderschrift.").classes(
                    "text-xs text-gray-500"
                )
                uploader = (
                    ui.upload(
                        label="Kies of maak een foto",
                        on_upload=on_image,
                        on_rejected=lambda: ui.notify(
                            "Foto is te groot (max 25 MB)", type="negative"
                        ),
                        auto_upload=True,
                        max_file_size=MAX_IMAGE_BYTES,
                    )
                    .props("accept=image/* flat bordered")
                    .classes("w-full")
                )
                ui.button("Annuleren", on_click=photo_dialog.close).props("flat")

            ui.button(icon="photo_camera", on_click=photo_dialog.open).props(
                "dense flat color=primary"
            ).tooltip("Foto toevoegen")
            ui.button(icon="send", on_click=on_send).props("dense flat color=primary").tooltip(
                "Verstuur"
            )
            ui.button(icon="refresh", on_click=lambda: _messages_block.refresh()).props(
                "dense flat color=primary"
            ).tooltip("Vernieuwen")
