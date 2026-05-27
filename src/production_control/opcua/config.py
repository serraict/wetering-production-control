"""Single source of truth for OPC UA client configuration.

Five callers used to wire `asyncua.Client` from `VINEAPP_OPCUA_*` env
vars independently, each with its own `_env()` helper and only some of
them honoring `VINEAPP_OPCUA_SECURITY=none`. This module replaces all
of that: every OPC UA caller goes through `build_client(role)` and the
env contract lives in one place.

Behavior matrix:

    VINEAPP_OPCUA_SECURITY    Auth        Transport                      Required env (per role)
    ----------------------    ---------   ----------------------------   ----------------------------------
    unset / anything else     user+pwd    Basic256Sha256_SignAndEncrypt  URL, USER, PASSWORD, CLIENT_CERT, CLIENT_KEY
    none                      anonymous   NoSecurity                     URL only

`VINEAPP_OPCUA_CLIENT_APP_URI` is optional in both modes.
"""

from __future__ import annotations

import os
from typing import Literal

from asyncua import Client, ua
from asyncua.crypto.security_policies import SecurityPolicyBasic256Sha256

SecurityMode = Literal["secure", "none"]
Role = Literal["plc", "leuze"]

DEFAULT_APP_URI = "urn:serra:production-control"

_ROLE_ENV: dict[Role, dict[str, str]] = {
    "plc": {
        "url": "VINEAPP_OPCUA_PLC_URL",
        "user": "VINEAPP_OPCUA_PLC_USER",
        "password": "VINEAPP_OPCUA_PLC_PASSWORD",
    },
    "leuze": {
        "url": "VINEAPP_OPCUA_LEUZE_URL",
        "user": "VINEAPP_OPCUA_LEUZE_USER",
        "password": "VINEAPP_OPCUA_LEUZE_PASSWORD",
    },
}

_SECURE_SHARED_ENV = (
    "VINEAPP_OPCUA_CLIENT_CERT",
    "VINEAPP_OPCUA_CLIENT_KEY",
)


def current_mode() -> SecurityMode:
    """Read `VINEAPP_OPCUA_SECURITY` and classify the mode."""
    return "none" if os.environ.get("VINEAPP_OPCUA_SECURITY", "").lower() == "none" else "secure"


def required_env_for(mode: SecurityMode, role: Role) -> list[str]:
    """Env vars that must be set for `build_client(role)` to succeed in `mode`."""
    role_env = _ROLE_ENV[role]
    if mode == "none":
        return [role_env["url"]]
    return [
        role_env["url"],
        role_env["user"],
        role_env["password"],
        *_SECURE_SHARED_ENV,
    ]


def require_env(name: str) -> str:
    """Return the env var's value or raise `RuntimeError` naming it."""
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"missing env var: {name}")
    return value


async def build_client(role: Role) -> Client:
    """Build a connection-ready `asyncua.Client` for the given role.

    Honors `VINEAPP_OPCUA_SECURITY=none` (anonymous + NoSecurity) and
    otherwise applies user/pwd + Basic256Sha256_SignAndEncrypt with the
    cert/key from env. The client is configured but not connected.
    """
    role_env = _ROLE_ENV[role]
    url = require_env(role_env["url"])

    client = Client(url=url)
    client.application_uri = os.environ.get("VINEAPP_OPCUA_CLIENT_APP_URI", DEFAULT_APP_URI)

    if current_mode() == "secure":
        client.set_user(require_env(role_env["user"]))
        client.set_password(require_env(role_env["password"]))
        await client.set_security(
            SecurityPolicyBasic256Sha256,
            certificate=require_env("VINEAPP_OPCUA_CLIENT_CERT"),
            private_key=require_env("VINEAPP_OPCUA_CLIENT_KEY"),
            mode=ua.MessageSecurityMode.SignAndEncrypt,
        )

    return client
