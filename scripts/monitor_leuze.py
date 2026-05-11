"""Browse the Leuze scanner's user namespaces and subscribe to every variable.

Goal 4 from work/doing.md: log datachange notifications from the scanner.
Mirrors monitor_plc.py. The test-setup Leuze required a monkey-patch for a
malformed server cert (see scripts/browse_leuze.py) — try the plain path
first against the production scanner; if you hit a cert-parsing error,
port the LenientCertificate patch over.

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

from asyncua import Client, Node, ua
from asyncua.crypto.security_policies import SecurityPolicyBasic256Sha256

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


async def collect_variables(node: Node, indent: int = 0) -> list[Node]:
    """Recurse from `node`, print structure, return all Variable nodes."""
    name = (await node.read_display_name()).Text
    node_class = await node.read_node_class()
    variables: list[Node] = []

    if node_class == ua.NodeClass.Variable:
        try:
            value = await node.read_value()
        except ua.UaError:
            value = "?"
        print(f"{'  ' * indent}{name} = {value}")
        variables.append(node)
    else:
        print(f"{'  ' * indent}{name}/")

    for child in await node.get_children():
        child_class = await child.read_node_class()
        if child_class in (ua.NodeClass.Object, ua.NodeClass.Variable):
            variables.extend(await collect_variables(child, indent + 1))

    return variables


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

    print(f"Connecting to {url} ...", flush=True)
    async with client:
        variables: list[Node] = []
        for child in await client.nodes.objects.get_children():
            if child.nodeid.NamespaceIndex == 0:
                continue
            variables.extend(await collect_variables(child))

        if not variables:
            print("No user-namespace variables found.", flush=True)
            return

        subscription = await client.create_subscription(500, Handler())
        await subscription.subscribe_data_change(variables)
        print(f"\nSubscribed to {len(variables)} variables (Ctrl+C to stop)", flush=True)
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
