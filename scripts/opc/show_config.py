"""Print the OPC UA configuration the container will use.

Deploy/run canary: confirms the production_control container can read its
env vars and find the certificate files mounted at the expected paths.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(REPO_ROOT / ".env")


def _exists(path: str | None) -> str:
    if not path:
        return "(not set)"
    p = Path(path)
    return f"{p} ({'found' if p.exists() else 'MISSING'})"


def main() -> None:
    plc_url = os.environ.get("VINEAPP_OPCUA_PLC_URL", "")
    leuze_url = os.environ.get("VINEAPP_OPCUA_LEUZE_URL", "")
    client_cert = os.environ.get(
        "VINEAPP_OPCUA_CLIENT_CERT", str(REPO_ROOT / "certs" / "client_cert.der")
    )
    client_key = os.environ.get(
        "VINEAPP_OPCUA_CLIENT_KEY", str(REPO_ROOT / "certs" / "client_cert_key.pem")
    )

    print("OPC UA configuration:")
    print(f"  PLC URL:           {plc_url or '(not set)'}")
    print(f"  Leuze scanner URL: {leuze_url or '(not set)'}")
    print(f"  Client cert (DER): {_exists(client_cert)}")
    print(f"  Client key (PEM):  {_exists(client_key)}")


if __name__ == "__main__":
    main()
