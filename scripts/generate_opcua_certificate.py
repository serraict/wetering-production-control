#!/usr/bin/env python3
"""Generate OPC/UA certificates: a CA (issuer) certificate and a client certificate signed by it.

The CA cert is uploaded to the PLC's "Trusted Issuers" list.
The client cert (signed by the CA) is used to connect.

Usage:
    # Generate both CA and client cert:
    python scripts/generate_opcua_certificate.py --output-dir certs --hostname 192.168.50.140

    # Regenerate client cert only (reusing existing CA):
    python scripts/generate_opcua_certificate.py --output-dir certs --hostname 192.168.50.140 --client-only
"""

import argparse
import ipaddress
import logging
import random
import socket
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# asyncua/uabrowse default application URI
DEFAULT_APPLICATION_URI = "urn:freeopcua:client"
APPLICATION_NAME = "Wetering Production Control"


def _write_cert_and_key(output_dir, name, certificate, private_key):
    """Write certificate (DER + PEM) and private key (PEM) to files."""
    der_path = output_dir / f"{name}.der"
    der_path.write_bytes(certificate.public_bytes(serialization.Encoding.DER))
    logger.info(f"Certificate (DER): {der_path}")

    pem_path = output_dir / f"{name}.pem"
    pem_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    logger.info(f"Certificate (PEM): {pem_path}")

    key_path = output_dir / f"{name}_key.pem"
    key_path.write_bytes(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    key_path.chmod(0o600)
    logger.info(f"Private key (PEM): {key_path}")

    return der_path, pem_path, key_path


def generate_ca(output_dir: Path, days_valid: int = 365 * 10):
    """Generate a CA (issuer) certificate for signing client certificates."""
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Generating CA key pair...")
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = datetime.now(timezone.utc)

    ca_name = x509.Name(
        [
            x509.NameAttribute(x509.oid.NameOID.COUNTRY_NAME, "NL"),
            x509.NameAttribute(x509.oid.NameOID.ORGANIZATION_NAME, "Wetering Potlilium"),
            x509.NameAttribute(x509.oid.NameOID.COMMON_NAME, "Wetering OPC-UA CA"),
        ]
    )

    ca_cert = (
        x509.CertificateBuilder()
        .subject_name(ca_name)
        .issuer_name(ca_name)
        .public_key(ca_key.public_key())
        .serial_number(random.randint(1, 2**31 - 1))
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=days_valid))
        .add_extension(
            x509.BasicConstraints(ca=True, path_length=0),
            critical=True,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=False,
                key_encipherment=False,
                data_encipherment=False,
                key_agreement=False,
                key_cert_sign=True,
                crl_sign=True,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()),
            critical=False,
        )
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()),
            critical=False,
        )
        .sign(ca_key, hashes.SHA256())
    )

    der_path, pem_path, key_path = _write_cert_and_key(output_dir, "ca", ca_cert, ca_key)

    logger.info("--- CA Certificate ---")
    logger.info(f"  Subject:    {ca_cert.subject}")
    logger.info(f"  Valid from: {ca_cert.not_valid_before_utc}")
    logger.info(f"  Valid until:{ca_cert.not_valid_after_utc}")
    logger.info(f"  Serial:     {ca_cert.serial_number}")

    return ca_cert, ca_key


def load_ca(output_dir: Path):
    """Load existing CA certificate and key from disk."""
    ca_pem = output_dir / "ca.pem"
    ca_key_pem = output_dir / "ca_key.pem"

    if not ca_pem.exists() or not ca_key_pem.exists():
        raise FileNotFoundError(f"CA files not found in {output_dir}. Run without --client-only first.")

    ca_cert = x509.load_pem_x509_certificate(ca_pem.read_bytes())
    ca_key = serialization.load_pem_private_key(ca_key_pem.read_bytes(), password=None)
    logger.info(f"Loaded existing CA: {ca_cert.subject}")
    return ca_cert, ca_key


def generate_client_cert(
    output_dir: Path,
    ca_cert,
    ca_key,
    hostname: str = "localhost",
    application_uri: str = DEFAULT_APPLICATION_URI,
    days_valid: int = 365 * 5,
):
    """Generate a client certificate signed by the CA."""
    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Generating client key pair...")
    client_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    now = datetime.now(timezone.utc)

    subject = x509.Name(
        [
            x509.NameAttribute(x509.oid.NameOID.COUNTRY_NAME, "NL"),
            x509.NameAttribute(x509.oid.NameOID.ORGANIZATION_NAME, "Wetering Potlilium"),
            x509.NameAttribute(x509.oid.NameOID.COMMON_NAME, APPLICATION_NAME),
        ]
    )

    # Subject Alternative Names
    local_hostname = socket.gethostname()
    san_names = [
        x509.UniformResourceIdentifier(application_uri),
        x509.DNSName(local_hostname),
        x509.DNSName(hostname),
    ]
    try:
        san_names.append(x509.IPAddress(ipaddress.ip_address(hostname)))
    except ValueError:
        pass

    client_cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(ca_cert.subject)  # Signed by CA
        .public_key(client_key.public_key())
        .serial_number(random.randint(1, 2**31 - 1))
        .not_valid_before(now)
        .not_valid_after(now + timedelta(days=days_valid))
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )
        .add_extension(
            x509.KeyUsage(
                digital_signature=True,
                content_commitment=True,
                key_encipherment=True,
                data_encipherment=True,
                key_agreement=False,
                key_cert_sign=False,
                crl_sign=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        )
        .add_extension(
            x509.ExtendedKeyUsage(
                [
                    ExtendedKeyUsageOID.SERVER_AUTH,
                    ExtendedKeyUsageOID.CLIENT_AUTH,
                ]
            ),
            critical=True,
        )
        .add_extension(
            x509.SubjectAlternativeName(san_names),
            critical=False,
        )
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(client_key.public_key()),
            critical=False,
        )
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()),
            critical=False,
        )
        .sign(ca_key, hashes.SHA256())  # Signed with CA's key
    )

    der_path, pem_path, key_path = _write_cert_and_key(output_dir, "client_cert", client_cert, client_key)

    logger.info("--- Client Certificate ---")
    logger.info(f"  Subject:         {client_cert.subject}")
    logger.info(f"  Issuer:          {client_cert.issuer}")
    logger.info(f"  Application URI: {application_uri}")
    logger.info(f"  Valid from:      {client_cert.not_valid_before_utc}")
    logger.info(f"  Valid until:     {client_cert.not_valid_after_utc}")
    logger.info(f"  Serial:          {client_cert.serial_number}")

    return der_path, pem_path, key_path


def main():
    parser = argparse.ArgumentParser(
        description="Generate OPC/UA CA and client certificates"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("certs"),
        help="Output directory for certificate files (default: certs/)",
    )
    parser.add_argument(
        "--hostname",
        default="localhost",
        help="Client hostname or IP address for the SAN field (default: localhost)",
    )
    parser.add_argument(
        "--application-uri",
        default=DEFAULT_APPLICATION_URI,
        help=f"OPC/UA application URI (default: {DEFAULT_APPLICATION_URI})",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=365 * 5,
        help="Client certificate validity in days (default: 1825 = 5 years)",
    )
    parser.add_argument(
        "--client-only",
        action="store_true",
        help="Only regenerate client cert (reuse existing CA)",
    )
    args = parser.parse_args()

    if args.client_only:
        ca_cert, ca_key = load_ca(args.output_dir)
    else:
        ca_cert, ca_key = generate_ca(args.output_dir)

    generate_client_cert(
        output_dir=args.output_dir,
        ca_cert=ca_cert,
        ca_key=ca_key,
        hostname=args.hostname,
        application_uri=args.application_uri,
        days_valid=args.days,
    )

    print()
    if not args.client_only:
        print("1. Upload ca.der to the PLC's 'Trusted Issuers' in Sysmac Studio")
        print("   and transfer to controller.")
        print()
    print("2. To connect, use:")
    print(f"   export OPC_USE_SECURITY=true")
    print(f"   export OPC_CERTIFICATE_PATH=certs/client_cert.pem")
    print(f"   export OPC_PRIVATE_KEY_PATH=certs/client_cert_key.pem")
    print()
    print("3. To regenerate a new client cert (same CA):")
    print(f"   python scripts/generate_opcua_certificate.py --client-only --hostname {args.hostname}")


if __name__ == "__main__":
    main()
