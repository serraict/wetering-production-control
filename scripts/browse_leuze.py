#!/usr/bin/env python3
"""Browse a Leuze scanner via OPC/UA with Basic256Sha256 security.

Works around a malformed server certificate by monkey-patching the
strict ASN.1 parser to use a lenient DER loader.

Usage:
    python scripts/browse_leuze.py
    python scripts/browse_leuze.py --endpoint opc.tcp://192.168.50.41:4840
    python scripts/browse_leuze.py --depth 3
"""

import argparse
import asyncio
import logging

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from cryptography.x509 import load_der_x509_certificate

from asyncua import Client, ua
from asyncua.crypto import security_policies, uacrypto

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Suppress noisy asyncua logs
logging.getLogger("asyncua").setLevel(logging.WARNING)

DEFAULT_ENDPOINT = "opc.tcp://192.168.50.41:4840"
DEFAULT_CERT = "certs/client_cert.der"
DEFAULT_KEY = "certs/client_key.pem"


class LenientCertificate:
    """Wraps raw DER certificate bytes, extracting the public key
    without full x509 parsing. Falls back to providing raw DER bytes
    for operations that need them."""

    def __init__(self, der_bytes: bytes):
        self._der_bytes = der_bytes
        # Extract public key from the DER using the SubjectPublicKeyInfo
        # which is a well-formed subset even if other fields are malformed
        self._public_key = self._extract_public_key(der_bytes)

    def _extract_public_key(self, der_bytes):
        """Extract the public key from DER bytes using pyasn1 minimal parsing."""
        # The SubjectPublicKeyInfo is always valid even if name fields aren't.
        # We can extract it by parsing the raw ASN.1 TBSCertificate structure.
        from pyasn1.codec.der import decoder as der_decoder
        from pyasn1.type import univ

        # Decode the outer SEQUENCE (Certificate)
        cert_seq, _ = der_decoder.decode(der_bytes, asn1Spec=univ.Sequence())
        # TBSCertificate is the first element
        tbs = cert_seq.getComponentByPosition(0)
        # SubjectPublicKeyInfo is at index 6 in TBSCertificate (v3)
        spki = tbs.getComponentByPosition(6)

        from pyasn1.codec.der import encoder as der_encoder
        from cryptography.hazmat.primitives.serialization import load_der_public_key

        spki_der = der_encoder.encode(spki)
        return load_der_public_key(spki_der, default_backend())

    def public_key(self):
        return self._public_key

    def public_bytes(self, encoding):
        """Return the raw certificate bytes (for der_from_x509)."""
        if encoding == Encoding.DER:
            return self._der_bytes
        raise ValueError(f"Unsupported encoding: {encoding}")


def _lenient_x509_from_der(data):
    """Try strict parsing first, fall back to lenient wrapper."""
    if not data:
        return None
    try:
        return load_der_x509_certificate(data, default_backend())
    except (ValueError, Exception):
        logger.info("Using lenient certificate parser for malformed server cert")
        return LenientCertificate(data)


def _lenient_der_from_x509(cert):
    """Handle both real x509 certs and our LenientCertificate wrapper."""
    if isinstance(cert, LenientCertificate):
        return cert.public_bytes(Encoding.DER)
    return uacrypto.der_from_x509(cert)


# Monkey-patch asyncua's certificate functions
_original_x509_from_der = uacrypto.x509_from_der
_original_der_from_x509 = uacrypto.der_from_x509
_original_load_certificate = uacrypto.load_certificate

uacrypto.x509_from_der = _lenient_x509_from_der


async def _lenient_load_certificate(path_or_content, extension=None):
    """Load certificate with lenient fallback."""
    try:
        return await _original_load_certificate(path_or_content, extension)
    except (ValueError, Exception):
        if isinstance(path_or_content, bytes):
            content = path_or_content
        else:
            content = await uacrypto.get_content(path_or_content)
        logger.info("Using lenient certificate loader for malformed cert")
        return LenientCertificate(content)


uacrypto.load_certificate = _lenient_load_certificate

# Also patch der_from_x509 to handle LenientCertificate
_orig_der_from_x509 = uacrypto.der_from_x509


def _patched_der_from_x509(cert):
    if isinstance(cert, LenientCertificate):
        return cert.public_bytes(Encoding.DER)
    return _orig_der_from_x509(cert)


uacrypto.der_from_x509 = _patched_der_from_x509


async def browse_node(node, depth: int, indent: int = 0):
    """Recursively browse and print OPC/UA nodes."""
    children = await node.get_children()
    for child in children:
        name = await child.read_browse_name()
        node_class = await child.read_node_class()
        prefix = "  " * indent

        if node_class == ua.NodeClass.Variable:
            try:
                value = await child.read_value()
                print(f"{prefix}{name.Name} = {value} (NodeId: {child.nodeid})")
            except Exception:
                print(f"{prefix}{name.Name} (NodeId: {child.nodeid}) [unreadable]")
        else:
            print(f"{prefix}{name.Name}/ (NodeId: {child.nodeid})")

        if depth > 1:
            await browse_node(child, depth - 1, indent + 1)


async def main(endpoint: str, cert_path: str, key_path: str, depth: int, user: str = None, password: str = None):
    client = Client(endpoint)
    if user:
        client.set_user(user)
    if password:
        client.set_password(password)
    await client.set_security_string(
        f"Basic256Sha256,SignAndEncrypt,{cert_path},{key_path}"
    )

    async with client:
        logger.info("Connected with Basic256Sha256 SignAndEncrypt")
        root = client.get_root_node()
        print(f"\nBrowsing {endpoint} (depth={depth}):\n")
        await browse_node(root, depth)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Browse Leuze scanner via OPC/UA")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help="OPC/UA endpoint URL")
    parser.add_argument("--cert", default=DEFAULT_CERT, help="Client certificate (DER)")
    parser.add_argument("--key", default=DEFAULT_KEY, help="Client private key (PEM)")
    parser.add_argument("--depth", type=int, default=3, help="Browse depth (default: 3)")
    parser.add_argument("--user", default=None, help="Username for authentication")
    parser.add_argument("--password", default=None, help="Password for authentication")
    args = parser.parse_args()

    asyncio.run(main(args.endpoint, args.cert, args.key, args.depth, args.user, args.password))
