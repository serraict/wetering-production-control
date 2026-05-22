"""Generate a self-signed OPC UA client (Application Instance) certificate.

Mirrors the pattern in docs/notes/opcua-examples/client/generate_cert.py:
asyncua.crypto.cert_gen.setup_self_signed_certificate builds the cert with
the SAN URI matching the application URI, SAN DNS matching the hostname,
and both clientAuth + serverAuth EKUs (Omron requires both).

Usage:
    python scripts/opc/generate_client_cert.py
    python scripts/opc/generate_client_cert.py --hostname serraserver --app-uri urn:serra:pc-client
"""

import argparse
import asyncio
import socket
from pathlib import Path

from asyncua.crypto.cert_gen import setup_self_signed_certificate
from cryptography.x509.oid import ExtendedKeyUsageOID

DEFAULT_APP_URI = "urn:serra:production-control-client"


async def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an OPC UA client cert.")
    parser.add_argument("--out-dir", type=Path, default=Path("certs"))
    parser.add_argument("--hostname", default=socket.gethostname())
    parser.add_argument("--app-uri", default=DEFAULT_APP_URI)
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    cert = args.out_dir / "client_cert.der"
    key = args.out_dir / "client_cert_key.pem"

    await setup_self_signed_certificate(
        key,
        cert,
        args.app_uri,
        args.hostname,
        [ExtendedKeyUsageOID.CLIENT_AUTH, ExtendedKeyUsageOID.SERVER_AUTH],
        {
            "countryName": "NL",
            "stateOrProvinceName": "Zuid-Holland",
            "localityName": "Bergschenhoek",
            "organizationName": "Serra ICT",
        },
    )

    print(f"Cert:    {cert}")
    print(f"Key:     {key}")
    print(f"App URI: {args.app_uri}")
    print(f"DNS SAN: {args.hostname}")
    print()
    print(f"Inspect: openssl x509 -in {cert} -inform der -text -noout")


if __name__ == "__main__":
    asyncio.run(main())
