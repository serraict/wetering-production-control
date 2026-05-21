"""Leuze scanner source for the OPC/UA monitor.

Subscribes to a fixed three-node set on the Leuze DCR 202iC scanner. Applies
the LenientCertificate monkey-patch from scripts/browse_leuze.py at import
time so asyncua can complete the TLS handshake against the scanner's
malformed server certificate.

Subscribing to the full browse tree trips BadEncodingLimitsExceeded on this
firmware (V2.4.0); the fixed list is intentional.
"""

from __future__ import annotations

import logging
import os

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import Encoding, load_der_public_key
from cryptography.x509 import load_der_x509_certificate

from asyncua import Client, ua
from asyncua.crypto import uacrypto
from asyncua.crypto.security_policies import SecurityPolicyBasic256Sha256

from .monitor import (  # noqa: F401 — re-exporting nothing, importing for shared types
    DEFAULT_APP_URI,
    SUBSCRIPTION_INTERVAL_MS,
    JsonlHandler,
)

logger = logging.getLogger(__name__)

# Fixed node set — subscribing to the full tree trips BadEncodingLimitsExceeded.
LEUZE_NODES: dict[str, str] = {
    "LastScanData":      "ns=5;i=6122",   # protocol: scanned value
    "ScanActive":        "ns=5;i=6199",   # debug:    scanning on/off
    "DeviceTemperature": "ns=5;i=6116",   # debug:    sanity / health
}


# --- LenientCertificate monkey-patch -----------------------------------------
# Lifted from scripts/browse_leuze.py + scripts/monitor_leuze.py. The patch is
# global on asyncua.crypto.uacrypto but only kicks in when strict parsing
# fails, so the PLC connection (which has a well-formed cert) is unaffected.


class LenientCertificate:
    """Wraps malformed DER cert bytes — extracts the public key via minimal
    ASN.1 parsing so asyncua can complete the handshake."""

    def __init__(self, der_bytes: bytes) -> None:
        self._der_bytes = der_bytes
        from pyasn1.codec.der import decoder as der_decoder, encoder as der_encoder
        from pyasn1.type import univ

        cert_seq, _ = der_decoder.decode(der_bytes, asn1Spec=univ.Sequence())
        tbs = cert_seq.getComponentByPosition(0)
        spki = tbs.getComponentByPosition(6)
        self._public_key = load_der_public_key(der_encoder.encode(spki), default_backend())

    def public_key(self):
        return self._public_key

    def public_bytes(self, encoding):
        if encoding == Encoding.DER:
            return self._der_bytes
        raise ValueError(f"Unsupported encoding: {encoding}")


def _lenient_x509_from_der(data):
    if not data:
        return None
    try:
        return load_der_x509_certificate(data, default_backend())
    except Exception:
        logger.info("Using lenient certificate parser for malformed server cert")
        return LenientCertificate(data)


_orig_der_from_x509 = uacrypto.der_from_x509
_orig_load_certificate = uacrypto.load_certificate


def _patched_der_from_x509(cert):
    if isinstance(cert, LenientCertificate):
        return cert.public_bytes(Encoding.DER)
    return _orig_der_from_x509(cert)


async def _lenient_load_certificate(path_or_content, extension=None):
    try:
        return await _orig_load_certificate(path_or_content, extension)
    except Exception:
        if isinstance(path_or_content, bytes):
            content = path_or_content
        else:
            content = await uacrypto.get_content(path_or_content)
        logger.info("Using lenient certificate loader for malformed cert")
        return LenientCertificate(content)


uacrypto.x509_from_der = _lenient_x509_from_der
uacrypto.der_from_x509 = _patched_der_from_x509
uacrypto.load_certificate = _lenient_load_certificate

# -----------------------------------------------------------------------------


def _env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(f"missing env var: {name}")
    return value


async def run_leuze() -> None:
    """One Leuze connection lifetime: connect, subscribe, stream until the
    connection drops. Reconnects are handled by the outer supervisor."""

    url = _env("VINEAPP_OPCUA_LEUZE_URL")
    client = Client(url=url)
    client.application_uri = os.environ.get("VINEAPP_OPCUA_CLIENT_APP_URI", DEFAULT_APP_URI)
    client.set_user(_env("VINEAPP_OPCUA_LEUZE_USER"))
    client.set_password(_env("VINEAPP_OPCUA_LEUZE_PASSWORD"))
    await client.set_security(
        SecurityPolicyBasic256Sha256,
        certificate=_env("VINEAPP_OPCUA_CLIENT_CERT"),
        private_key=_env("VINEAPP_OPCUA_CLIENT_KEY"),
        mode=ua.MessageSecurityMode.SignAndEncrypt,
    )

    logger.info("connecting to %s", url)
    async with client:
        handler = JsonlHandler(source="leuze")
        nodes = []
        for name, nid in LEUZE_NODES.items():
            node = client.get_node(nid)
            handler.register(node, name)
            nodes.append(node)
            logger.info("monitoring %s (%s)", name, nid)

        subscription = await client.create_subscription(SUBSCRIPTION_INTERVAL_MS, handler)
        await subscription.subscribe_data_change(nodes)
        logger.info("subscribed to %d Leuze variables", len(nodes))

        import asyncio  # local import to avoid cycle in __all__-style imports

        try:
            while True:
                await asyncio.sleep(1)
        finally:
            try:
                await subscription.delete()
            except Exception:  # pragma: no cover — best-effort cleanup
                pass
