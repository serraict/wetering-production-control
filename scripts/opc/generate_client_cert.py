"""Generate a self-signed OPC UA client (Application Instance) certificate.

Mirrors the pattern in docs/notes/opcua-examples/client/generate_cert.py:
asyncua.crypto.cert_gen.setup_self_signed_certificate builds the cert with
the SAN URI matching the application URI, SAN DNS matching the hostname,
and both clientAuth + serverAuth EKUs (Omron requires both).

Defaults:
    --out-dir   certs
    --hostname  socket.gethostname() of the machine running the script
    --app-uri   urn:serra:production-control (must match runtime
                client.application_uri and be ≤44 chars for Omron)
    --days      365

Usage:
    python scripts/opc/generate_client_cert.py --days 3650
    python scripts/opc/generate_client_cert.py --hostname serraserver --app-uri urn:serra:pc-client --days 3650
"""

import argparse
import asyncio
import socket
from pathlib import Path

from asyncua.crypto.cert_gen import (
    check_certificate,
    dump_private_key_as_pem,
    generate_private_key,
    generate_self_signed_app_certificate,
    load_certificate,
    load_private_key,
)
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.serialization import Encoding
from cryptography.x509 import DNSName, UniformResourceIdentifier
from cryptography.x509.oid import ExtendedKeyUsageOID

DEFAULT_APP_URI = "urn:serra:production-control"
SUBJECT_ATTRS = {
    "countryName": "NL",
    "stateOrProvinceName": "Zuid-Holland",
    "localityName": "Bergschenhoek",
    "organizationName": "Serra ICT",
}


async def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an OPC UA client cert.")
    parser.add_argument("--out-dir", type=Path, default=Path("certs"))
    parser.add_argument("--hostname", default=socket.gethostname())
    parser.add_argument("--app-uri", default=DEFAULT_APP_URI)
    parser.add_argument(
        "--days",
        type=int,
        default=365,
        help="Cert validity in days (default: 365). 3650 = 10 years.",
    )
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    cert_path = args.out_dir / "client_cert.der"
    key_path = args.out_dir / "client_cert_key.pem"

    # Inlined from asyncua.crypto.cert_gen.setup_self_signed_certificate
    # so we can pass `days`; the convenience helper hardcodes 365.
    # Skip-if-valid behavior preserved: only regenerate when missing or
    # the existing cert no longer matches app URI / hostname.
    generate_key = not key_path.is_file()
    generate_cert = generate_key or not cert_path.is_file()

    if generate_key:
        key = generate_private_key()
        key_path.write_bytes(dump_private_key_as_pem(key))
    else:
        key = await load_private_key(key_path)
        # load_private_key returns the PrivateKeyTypes union; narrow to RSA
        # (we only ever generate RSA here) so the cert builder typechecks.
        assert isinstance(key, RSAPrivateKey), f"expected RSA key, got {type(key).__name__}"

    if not generate_cert:
        existing = await load_certificate(cert_path)
        generate_cert = check_certificate(existing, args.app_uri, args.hostname)

    if generate_cert:
        cert = generate_self_signed_app_certificate(
            key,
            args.app_uri,
            SUBJECT_ATTRS,
            [UniformResourceIdentifier(args.app_uri), DNSName(args.hostname)],
            extended=[ExtendedKeyUsageOID.CLIENT_AUTH, ExtendedKeyUsageOID.SERVER_AUTH],
            days=args.days,
        )
        cert_path.write_bytes(cert.public_bytes(encoding=Encoding.DER))

    print(f"Cert:    {cert_path}")
    print(f"Key:     {key_path}")
    print(f"App URI: {args.app_uri}")
    print(f"DNS SAN: {args.hostname}")
    print(f"Valid:   {args.days} days")
    print()
    print(f"Inspect: openssl x509 -in {cert_path} -inform der -text -noout")


if __name__ == "__main__":
    asyncio.run(main())
