"""Probe an OPC UA endpoint with no security: list what the server offers.

Useful as a reachability + discovery check before configuring trust/credentials.
Prints the security policies, modes, and the server's application URI.

Usage:
    python scripts/probe_opcua_endpoint.py opc.tcp://host:4840
"""

import asyncio
import sys

from asyncua import Client


async def probe(url: str) -> int:
    print(f"Probing {url} ...")
    try:
        endpoints = await Client(url=url).connect_and_get_server_endpoints()
    except Exception as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}")
        return 1

    print(f"OK — {len(endpoints)} endpoint(s):")
    for ep in endpoints:
        policy = ep.SecurityPolicyUri.rsplit("#", 1)[-1]
        print(f"  - url:    {ep.EndpointUrl}")
        print(f"    policy: {policy}")
        print(f"    mode:   {ep.SecurityMode.name}")
        print(f"    app:    {ep.Server.ApplicationUri}")
    return 0


def main() -> int:
    if len(sys.argv) != 2:
        print(f"usage: {sys.argv[0]} <opc.tcp://host:port>", file=sys.stderr)
        return 2
    return asyncio.run(probe(sys.argv[1]))


if __name__ == "__main__":
    sys.exit(main())
