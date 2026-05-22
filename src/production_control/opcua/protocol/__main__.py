"""Entry point: `python -m production_control.opcua.protocol`."""

from __future__ import annotations

import asyncio
import logging
import os
import sys

from .. import config
from .scan_cycle import ScanCycleHandler, run_protocol


def cli() -> None:
    # Preflight: same shape as opcua.tui — fail visibly with named env
    # vars instead of burying a traceback inside the asyncio loop.
    mode = config.current_mode()
    required = [
        *config.required_env_for(mode, "plc"),
        *config.required_env_for(mode, "leuze"),
    ]
    missing = [name for name in required if not os.environ.get(name)]
    if missing:
        print(
            f"opc-protocol: missing required env vars (VINEAPP_OPCUA_SECURITY={mode}):",
            file=sys.stderr,
        )
        for name in missing:
            print(f"  {name}", file=sys.stderr)
        print("See docs/deployment.md for what each var should hold.", file=sys.stderr)
        sys.exit(2)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )
    logging.getLogger("asyncua").setLevel(logging.WARNING)
    try:
        asyncio.run(run_protocol(ScanCycleHandler()))
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass


if __name__ == "__main__":
    cli()
