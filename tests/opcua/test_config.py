"""Tests for opcua.config — the single source of truth for client wiring."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from production_control.opcua import config


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Strip every VINEAPP_OPCUA_* env var so each test starts from zero."""
    for key in list(__import__("os").environ):
        if key.startswith("VINEAPP_OPCUA_"):
            monkeypatch.delenv(key, raising=False)


# ----------------- current_mode -----------------


@pytest.mark.parametrize(
    "value, expected",
    [
        (None, "secure"),
        ("", "secure"),
        ("None", "none"),
        ("none", "none"),
        ("NONE", "none"),
        ("secure", "secure"),
        ("anything-else", "secure"),
    ],
)
def test_current_mode_classifies_env_var(monkeypatch, value, expected):
    if value is not None:
        monkeypatch.setenv("VINEAPP_OPCUA_SECURITY", value)
    assert config.current_mode() == expected


# ----------------- required_env_for -----------------


def test_required_env_for_none_plc_only_needs_url():
    assert config.required_env_for("none", "plc") == ["VINEAPP_OPCUA_PLC_URL"]


def test_required_env_for_none_leuze_only_needs_url():
    assert config.required_env_for("none", "leuze") == ["VINEAPP_OPCUA_LEUZE_URL"]


def test_required_env_for_secure_plc_lists_url_creds_and_cert_pair():
    assert config.required_env_for("secure", "plc") == [
        "VINEAPP_OPCUA_PLC_URL",
        "VINEAPP_OPCUA_PLC_USER",
        "VINEAPP_OPCUA_PLC_PASSWORD",
        "VINEAPP_OPCUA_CLIENT_CERT",
        "VINEAPP_OPCUA_CLIENT_KEY",
    ]


def test_required_env_for_secure_leuze_lists_url_creds_and_cert_pair():
    assert config.required_env_for("secure", "leuze") == [
        "VINEAPP_OPCUA_LEUZE_URL",
        "VINEAPP_OPCUA_LEUZE_USER",
        "VINEAPP_OPCUA_LEUZE_PASSWORD",
        "VINEAPP_OPCUA_CLIENT_CERT",
        "VINEAPP_OPCUA_CLIENT_KEY",
    ]


# ----------------- require_env -----------------


def test_require_env_returns_value(monkeypatch):
    monkeypatch.setenv("VINEAPP_OPCUA_PLC_URL", "opc.tcp://x")
    assert config.require_env("VINEAPP_OPCUA_PLC_URL") == "opc.tcp://x"


def test_require_env_raises_with_var_name():
    with pytest.raises(RuntimeError, match="VINEAPP_OPCUA_PLC_URL"):
        config.require_env("VINEAPP_OPCUA_PLC_URL")


def test_require_env_treats_empty_as_missing(monkeypatch):
    monkeypatch.setenv("VINEAPP_OPCUA_PLC_URL", "")
    with pytest.raises(RuntimeError, match="VINEAPP_OPCUA_PLC_URL"):
        config.require_env("VINEAPP_OPCUA_PLC_URL")


# ----------------- build_client (none mode) -----------------


@pytest.mark.asyncio
async def test_build_client_none_mode_plc_is_anonymous(monkeypatch):
    monkeypatch.setenv("VINEAPP_OPCUA_SECURITY", "none")
    monkeypatch.setenv("VINEAPP_OPCUA_PLC_URL", "opc.tcp://plc:4840")

    with (patch("production_control.opcua.config.Client") as MockClient,):
        instance = MockClient.return_value
        instance.set_security = AsyncMock()
        await config.build_client("plc")

    MockClient.assert_called_once_with(url="opc.tcp://plc:4840")
    instance.set_user.assert_not_called()
    instance.set_password.assert_not_called()
    instance.set_security.assert_not_called()


@pytest.mark.asyncio
async def test_build_client_none_mode_leuze_only_needs_url(monkeypatch):
    monkeypatch.setenv("VINEAPP_OPCUA_SECURITY", "none")
    monkeypatch.setenv("VINEAPP_OPCUA_LEUZE_URL", "opc.tcp://leuze:4840")

    with patch("production_control.opcua.config.Client") as MockClient:
        instance = MockClient.return_value
        instance.set_security = AsyncMock()
        await config.build_client("leuze")

    MockClient.assert_called_once_with(url="opc.tcp://leuze:4840")
    instance.set_user.assert_not_called()


@pytest.mark.asyncio
async def test_build_client_none_mode_missing_url_raises(monkeypatch):
    monkeypatch.setenv("VINEAPP_OPCUA_SECURITY", "none")
    with pytest.raises(RuntimeError, match="VINEAPP_OPCUA_PLC_URL"):
        await config.build_client("plc")


# ----------------- build_client (secure mode) -----------------


@pytest.mark.asyncio
async def test_build_client_secure_mode_plc_wires_user_password_and_security(monkeypatch):
    monkeypatch.setenv("VINEAPP_OPCUA_PLC_URL", "opc.tcp://plc:4840")
    monkeypatch.setenv("VINEAPP_OPCUA_PLC_USER", "marijn")
    monkeypatch.setenv("VINEAPP_OPCUA_PLC_PASSWORD", "pwd")
    monkeypatch.setenv("VINEAPP_OPCUA_CLIENT_CERT", "/certs/client.der")
    monkeypatch.setenv("VINEAPP_OPCUA_CLIENT_KEY", "/certs/client.pem")

    with patch("production_control.opcua.config.Client") as MockClient:
        instance = MockClient.return_value
        instance.set_security = AsyncMock()
        await config.build_client("plc")

    instance.set_user.assert_called_once_with("marijn")
    instance.set_password.assert_called_once_with("pwd")
    instance.set_security.assert_awaited_once()
    kwargs = instance.set_security.await_args.kwargs
    assert kwargs["certificate"] == "/certs/client.der"
    assert kwargs["private_key"] == "/certs/client.pem"


@pytest.mark.asyncio
async def test_build_client_secure_mode_missing_password_raises(monkeypatch):
    monkeypatch.setenv("VINEAPP_OPCUA_PLC_URL", "opc.tcp://plc:4840")
    monkeypatch.setenv("VINEAPP_OPCUA_PLC_USER", "marijn")
    monkeypatch.setenv("VINEAPP_OPCUA_CLIENT_CERT", "/certs/client.der")
    monkeypatch.setenv("VINEAPP_OPCUA_CLIENT_KEY", "/certs/client.pem")

    with patch("production_control.opcua.config.Client"):
        with pytest.raises(RuntimeError, match="VINEAPP_OPCUA_PLC_PASSWORD"):
            await config.build_client("plc")


@pytest.mark.asyncio
async def test_build_client_applies_app_uri_default(monkeypatch):
    monkeypatch.setenv("VINEAPP_OPCUA_SECURITY", "none")
    monkeypatch.setenv("VINEAPP_OPCUA_PLC_URL", "opc.tcp://plc:4840")

    with patch("production_control.opcua.config.Client") as MockClient:
        instance = MockClient.return_value
        instance.set_security = AsyncMock()
        await config.build_client("plc")

    assert instance.application_uri == config.DEFAULT_APP_URI


@pytest.mark.asyncio
async def test_build_client_applies_app_uri_override(monkeypatch):
    monkeypatch.setenv("VINEAPP_OPCUA_SECURITY", "none")
    monkeypatch.setenv("VINEAPP_OPCUA_PLC_URL", "opc.tcp://plc:4840")
    monkeypatch.setenv("VINEAPP_OPCUA_CLIENT_APP_URI", "urn:custom:app")

    with patch("production_control.opcua.config.Client") as MockClient:
        instance = MockClient.return_value
        instance.set_security = AsyncMock()
        await config.build_client("plc")

    assert instance.application_uri == "urn:custom:app"
