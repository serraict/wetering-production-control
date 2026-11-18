"""Unit tests for ZulipClient.upload_file with the SDK mocked."""

from unittest.mock import MagicMock

import pytest

from production_control.zulip_chat.client import ZulipClient, ZulipClientError


def _client_with_sdk(sdk: MagicMock) -> ZulipClient:
    client = ZulipClient()
    client._client = sdk
    return client


def test_upload_file_sends_named_file_and_returns_url() -> None:
    sdk = MagicMock()
    sdk.upload_file.return_value = {"result": "success", "url": "/user_uploads/1/a/foto.jpg"}

    path = _client_with_sdk(sdk).upload_file("foto.jpg", b"jpegbytes")

    assert path == "/user_uploads/1/a/foto.jpg"
    (fp,), _ = sdk.upload_file.call_args
    assert fp.name == "foto.jpg"
    assert fp.read() == b"jpegbytes"


def test_upload_file_falls_back_to_uri() -> None:
    sdk = MagicMock()
    sdk.upload_file.return_value = {"result": "success", "uri": "/user_uploads/1/a/old.jpg"}
    assert _client_with_sdk(sdk).upload_file("old.jpg", b"x") == "/user_uploads/1/a/old.jpg"


def test_upload_file_raises_on_error() -> None:
    sdk = MagicMock()
    sdk.upload_file.return_value = {"result": "error", "msg": "File too large"}
    with pytest.raises(ZulipClientError, match="File too large"):
        _client_with_sdk(sdk).upload_file("big.jpg", b"x")
