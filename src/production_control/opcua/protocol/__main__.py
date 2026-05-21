"""Entry point: `python -m production_control.opcua.protocol`."""

from __future__ import annotations

import asyncio
import logging
import sys

from .scan_cycle import ScanCycleHandler, run_protocol


def cli() -> None:
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
