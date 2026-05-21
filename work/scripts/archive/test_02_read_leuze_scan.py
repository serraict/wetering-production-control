#!/usr/bin/env python3
"""Test 2: Read LastScanData from the Leuze scanner.

Connects to the Leuze DCR 202iC and reads the LastScanData node.
Optionally polls for changes when --watch is given.

Usage:
    uv run python scripts/test_02_read_leuze_scan.py
    uv run python scripts/test_02_read_leuze_scan.py --watch
"""

import argparse
import asyncio
import logging

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.x509 import load_der_x509_certificate

from asyncua import Client
from asyncua.crypto import uacrypto

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)
logging.getLogger("asyncua").setLevel(logging.WARNING)

LEUZE_ENDPOINT = "opc.tcp://192.168.50.41:4840"
CERT_PATH = "certs/client_cert.der"
KEY_PATH = "certs/client_cert_key.pem"
LAST_SCAN_DATA_NODE = "ns=5;i=6122"


# --- Leuze certificate monkey-patch (malformed ASN.1 workaround) ---


class LenientCertificate:
    """Wraps raw DER bytes, extracting public key via pyasn1."""

    def __init__(self, der_bytes: bytes):
        self._der_bytes = der_bytes
        from pyasn1.codec.der import decoder as der_decoder
        from pyasn1.codec.der import encoder as der_encoder
        from pyasn1.type import univ
        from cryptography.hazmat.primitives.serialization import load_der_public_key

        cert_seq, _ = der_decoder.decode(der_bytes, asn1Spec=univ.Sequence())
        tbs = cert_seq.getComponentByPosition(0)
        spki = tbs.getComponentByPosition(6)
        spki_der = der_encoder.encode(spki)
        self._public_key = load_der_public_key(spki_der, default_backend())

    def public_key(self):
        return self._public_key

    def public_bytes(self, encoding):
        if encoding == Encoding.DER:
            return self._der_bytes
        raise ValueError(f"Unsupported encoding: {encoding}")


_original_x509_from_der = uacrypto.x509_from_der
_original_load_certificate = uacrypto.load_certificate
_original_der_from_x509 = uacrypto.der_from_x509


def _lenient_x509_from_der(data):
    if not data:
        return None
    try:
        return load_der_x509_certificate(data, default_backend())
    except (ValueError, Exception):
        logger.info("Using lenient parser for malformed Leuze server cert")
        return LenientCertificate(data)


async def _lenient_load_certificate(path_or_content, extension=None):
    try:
        return await _original_load_certificate(path_or_content, extension)
    except (ValueError, Exception):
        if isinstance(path_or_content, bytes):
            content = path_or_content
        else:
            content = await uacrypto.get_content(path_or_content)
        return LenientCertificate(content)


def _lenient_der_from_x509(cert):
    if isinstance(cert, LenientCertificate):
        return cert.public_bytes(Encoding.DER)
    return _original_der_from_x509(cert)


uacrypto.x509_from_der = _lenient_x509_from_der
uacrypto.load_certificate = _lenient_load_certificate
uacrypto.der_from_x509 = _lenient_der_from_x509


# --- Main ---


async def main(watch: bool, interval: float):
    client = Client(LEUZE_ENDPOINT)
    client.set_user("Martin")
    client.set_password("12345678")
    await client.set_security_string(
        f"Basic256Sha256,SignAndEncrypt,{CERT_PATH},{KEY_PATH}"
    )

    async with client:
        logger.info("Connected to Leuze scanner")
        node = client.get_node(LAST_SCAN_DATA_NODE)

        value = await node.read_value()
        print(f"LastScanData = {value!r}")

        if watch:
            print(f"\nWatching for changes (poll every {interval}s, Ctrl+C to stop)...")
            previous = value
            while True:
                await asyncio.sleep(interval)
                value = await node.read_value()
                if value != previous:
                    print(f"LastScanData = {value!r}")
                    previous = value


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test 2: Read Leuze LastScanData")
    parser.add_argument("--watch", action="store_true", help="Poll for changes")
    parser.add_argument("--interval", type=float, default=0.5, help="Poll interval in seconds (default: 0.5)")
    args = parser.parse_args()

    asyncio.run(main(args.watch, args.interval))
