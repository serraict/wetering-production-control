"""Photo upload on the communication card, with the Zulip service mocked."""

from __future__ import annotations

import io
from dataclasses import dataclass
from types import SimpleNamespace
from unittest.mock import patch

from nicegui import ui
from nicegui.testing import User
from starlette.datastructures import UploadFile

from production_control.web.components.communication_card import (
    read_upload,
    render_communication_card,
)

SERVICE = "production_control.web.components.communication_card.zulip_service"


@dataclass
class FakeLot:
    id: int = 42
    opmerking: str = ""


async def _open_card(user: User) -> None:
    @ui.page("/test-communication-card")
    def page() -> None:
        render_communication_card(FakeLot())

    await user.open("/test-communication-card")


async def test_uploaded_photo_is_posted_with_caption(user: User) -> None:
    with patch(SERVICE) as service:
        service.get_messages.return_value = []
        service.narrow_url.return_value = ""
        await _open_card(user)

        user.find(ui.textarea).type("blad geel")
        upload = user.find(ui.upload).elements.pop()
        upload.handle_uploads([UploadFile(io.BytesIO(b"jpegbytes"), filename="foto.jpg")])

        await user.should_see("Foto verstuurd")
        service.post_image.assert_called_once()
        args, kwargs = service.post_image.call_args
        assert args[1:] == ("foto.jpg", b"jpegbytes")
        assert kwargs["caption"] == "blad geel"


async def test_failed_photo_upload_is_reported(user: User) -> None:
    with patch(SERVICE) as service:
        service.get_messages.return_value = []
        service.narrow_url.return_value = ""
        service.post_image.side_effect = RuntimeError("network down")
        await _open_card(user)

        upload = user.find(ui.upload).elements.pop()
        upload.handle_uploads([UploadFile(io.BytesIO(b"x"), filename="foto.jpg")])

        await user.should_see("Foto versturen mislukt: network down")


async def test_read_upload_supports_nicegui_3_event_shape() -> None:
    """Production resolves NiceGUI 3, where the event carries `file` with an async read()."""

    class FakeFile:
        name = "foto.jpg"

        async def read(self) -> bytes:
            return b"jpegbytes"

    event = SimpleNamespace(file=FakeFile())
    assert await read_upload(event) == ("foto.jpg", b"jpegbytes")


async def test_read_upload_supports_nicegui_2_event_shape() -> None:
    event = SimpleNamespace(name="foto.jpg", content=io.BytesIO(b"jpegbytes"))
    assert await read_upload(event) == ("foto.jpg", b"jpegbytes")
