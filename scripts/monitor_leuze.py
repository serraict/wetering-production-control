"""Browse the Leuze scanner's user namespaces and subscribe to every variable.

Goal 4 from work/doing.md: log datachange notifications from the scanner.
Mirrors monitor_plc.py, plus the LenientCertificate monkey-patch from
scripts/browse_leuze.py — the Leuze ships a malformed server certificate
that the strict asn1 parser rejects.

Env vars (all required except where noted):
    VINEAPP_OPCUA_LEUZE_URL       opc.tcp://<leuze-host>:4840
    VINEAPP_OPCUA_LEUZE_USER
    VINEAPP_OPCUA_LEUZE_PASSWORD
    VINEAPP_OPCUA_CLIENT_CERT     path to client_cert.der
    VINEAPP_OPCUA_CLIENT_KEY      path to client_cert_key.pem
    VINEAPP_OPCUA_CLIENT_APP_URI  (optional, default urn:serra:production-control-client)

Usage:
    python scripts/monitor_leuze.py
"""

import asyncio
import logging
import os
import sys

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import Encoding, load_der_public_key
from cryptography.x509 import load_der_x509_certificate

from asyncua import Client, ua
from asyncua.crypto import uacrypto
from asyncua.crypto.security_policies import SecurityPolicyBasic256Sha256

DEFAULT_APP_URI = "urn:serra:production-control-client"

logger = logging.getLogger(__name__)


class LenientCertificate:
    """Wraps malformed DER cert bytes — extracts the public key via minimal
    ASN.1 parsing so asyncua can complete the handshake."""

    def __init__(self, der_bytes: bytes):
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


class Handler:
    def datachange_notification(self, node, val, data):
        print(f"  {node} -> {val}", flush=True)

    def status_change_notification(self, status):
        print(f"  status change: {status}", flush=True)

    def event_notification(self, event):
        print(f"  event: {event}", flush=True)


def env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        print(f"missing env var: {name}", file=sys.stderr)
        sys.exit(2)
    return value


async def main() -> None:
    url = env("VINEAPP_OPCUA_LEUZE_URL")
    client = Client(url=url)
    client.application_uri = os.environ.get("VINEAPP_OPCUA_CLIENT_APP_URI", DEFAULT_APP_URI)
    client.set_user(env("VINEAPP_OPCUA_LEUZE_USER"))
    client.set_password(env("VINEAPP_OPCUA_LEUZE_PASSWORD"))

    await client.set_security(
        SecurityPolicyBasic256Sha256,
        certificate=env("VINEAPP_OPCUA_CLIENT_CERT"),
        private_key=env("VINEAPP_OPCUA_CLIENT_KEY"),
        mode=ua.MessageSecurityMode.SignAndEncrypt,
    )

    # Fixed set: the protocol field plus a couple of debug fields.
    # Subscribing to the full browse tree trips BadEncodingLimitsExceeded
    # on this firmware.
    NODES = {
        "LastScanData":      "ns=5;i=6122",   # protocol: scanned value
        "ScanActive":        "ns=5;i=6199",   # debug:    scanning on/off
        "DeviceTemperature": "ns=5;i=6116",   # debug:    sanity / health
    }

    print(f"Connecting to {url} ...", flush=True)
    async with client:
        nodes = [client.get_node(nid) for nid in NODES.values()]
        # initial read
        for label, nid in NODES.items():
            try:
                value = await client.get_node(nid).read_value()
            except Exception as exc:
                value = f"<read error: {exc}>"
            print(f"  {label} ({nid}) = {value}")

        subscription = await client.create_subscription(500, Handler())
        await subscription.subscribe_data_change(nodes)
        print(f"\nSubscribed to {len(nodes)} nodes (Ctrl+C to stop)", flush=True)
        try:
            while True:
                await asyncio.sleep(1)
        except (asyncio.CancelledError, KeyboardInterrupt):
            pass
        await subscription.delete()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("asyncua").setLevel(logging.WARNING)
    asyncio.run(main())
