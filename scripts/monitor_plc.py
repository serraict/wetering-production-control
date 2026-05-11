"""Subscribe to datachange notifications on the Omron PLC protocol fields.

Goal 2 from work/doing.md: log GoodRead / Resultaat / Trigger as they change.
Connects with SignAndEncrypt + Basic256Sha256 using the client cert/key from
the env (same pattern as docs/notes/opcua-examples/client/client_sign_and_encrypt.py).

Env vars (all required except where noted):
    VINEAPP_OPCUA_PLC_URL       opc.tcp://<plc-host>:4840
    VINEAPP_OPCUA_PLC_USER
    VINEAPP_OPCUA_PLC_PASSWORD
    VINEAPP_OPCUA_CLIENT_CERT   path to client_cert.der
    VINEAPP_OPCUA_CLIENT_KEY    path to client_cert_key.pem
    VINEAPP_OPCUA_CLIENT_APP_URI  (optional, default urn:serra:production-control-client)

Usage:
    python scripts/monitor_plc.py
"""

import asyncio
import logging
import os
import sys

from asyncua import Client, ua
from asyncua.crypto.security_policies import SecurityPolicyBasic256Sha256

NODES = ["ns=4;s=GoodRead", "ns=4;s=Resultaat", "ns=4;s=Trigger"]
DEFAULT_APP_URI = "urn:serra:production-control-client"


class Handler:
    def datachange_notification(self, node, val, data):
        print(f"  {node} -> {val}", flush=True)


def env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        print(f"missing env var: {name}", file=sys.stderr)
        sys.exit(2)
    return value


async def main() -> None:
    url = env("VINEAPP_OPCUA_PLC_URL")
    client = Client(url=url)
    client.application_uri = os.environ.get("VINEAPP_OPCUA_CLIENT_APP_URI", DEFAULT_APP_URI)
    client.set_user(env("VINEAPP_OPCUA_PLC_USER"))
    client.set_password(env("VINEAPP_OPCUA_PLC_PASSWORD"))

    await client.set_security(
        SecurityPolicyBasic256Sha256,
        certificate=env("VINEAPP_OPCUA_CLIENT_CERT"),
        private_key=env("VINEAPP_OPCUA_CLIENT_KEY"),
        mode=ua.MessageSecurityMode.SignAndEncrypt,
    )

    print(f"Connecting to {url} ...", flush=True)
    async with client:
        nodes = [client.get_node(nid) for nid in NODES]
        subscription = await client.create_subscription(500, Handler())
        await subscription.subscribe_data_change(nodes)
        print(f"Subscribed to {len(nodes)} nodes (Ctrl+C to stop)", flush=True)
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
