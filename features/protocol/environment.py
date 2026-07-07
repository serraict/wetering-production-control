"""behave hooks for the OS↔PC protocol suite.

Each scenario gets:
- A fresh test OPC server subprocess on opc.tcp://127.0.0.1:4840.
- A fresh protocol handler running in a background event loop.

Step code talks to the OPC server in-process via asyncua (sync wrappers
in steps/_helpers.py) and asserts on the server's state. We don't
inspect the handler directly — the contract is what the PLC sees.
"""

from __future__ import annotations

import asyncio
import logging
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

from production_control.opcua.protocol import ScanCycleHandler, run_protocol

REPO_ROOT = Path(__file__).resolve().parents[2]
ENDPOINT = "opc.tcp://127.0.0.1:4840"


def _port_open(host: str = "127.0.0.1", port: int = 4840, timeout: float = 0.2) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _wait_for_port(deadline_s: float = 10.0) -> None:
    start = time.monotonic()
    while time.monotonic() - start < deadline_s:
        if _port_open():
            return
        time.sleep(0.1)
    raise RuntimeError(f"test OPC server did not open port within {deadline_s}s")


def _start_test_server(context) -> None:
    env = os.environ.copy()
    env.setdefault("OPC_TEST_OS_ACK_DELAY_MS", "0")
    context.server_proc = subprocess.Popen(
        [sys.executable, "scripts/opc/test_server.py"],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    _wait_for_port()


def _stop_test_server(context) -> None:
    proc = getattr(context, "server_proc", None)
    if not proc:
        return
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=2)


def _start_protocol_handler(context) -> None:
    # Run the protocol module in its own asyncio event loop on a daemon
    # thread. Steps drive the OPC server directly; the handler observes
    # via its subscriptions.
    context.handler = ScanCycleHandler()
    context.loop = asyncio.new_event_loop()
    context.plc_ready = asyncio.Event()
    context.leuze_ready = asyncio.Event()
    context.stop_event = asyncio.Event()

    def runner() -> None:
        asyncio.set_event_loop(context.loop)
        try:
            context.loop.run_until_complete(
                run_protocol(
                    context.handler,
                    plc_ready=context.plc_ready,
                    leuze_ready=context.leuze_ready,
                    stop_event=context.stop_event,
                )
            )
        except (asyncio.CancelledError, RuntimeError):
            pass
        finally:
            context.loop.close()

    context.handler_thread = threading.Thread(target=runner, name="protocol-loop", daemon=True)
    context.handler_thread.start()

    # Wait for both subscriptions to come up.
    deadline = time.monotonic() + 10.0
    while time.monotonic() < deadline:
        if context.plc_ready.is_set() and context.leuze_ready.is_set():
            return
        time.sleep(0.05)
    raise RuntimeError("protocol handler did not become ready within 10s")


def _stop_protocol_handler(context) -> None:
    loop = getattr(context, "loop", None)
    stop = getattr(context, "stop_event", None)
    thread = getattr(context, "handler_thread", None)
    if loop and stop:
        loop.call_soon_threadsafe(stop.set)
    if thread:
        thread.join(timeout=5)


class _WarningCapture(logging.Handler):
    """Stash WARNING+ records from the protocol logger so steps can
    assert on them."""

    def __init__(self, sink: list[str]) -> None:
        super().__init__(level=logging.WARNING)
        self._sink = sink

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._sink.append(self.format(record))
        except Exception:
            pass


def before_all(context):
    # Quiet asyncua a bit; keep our own loggers chatty.
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    logging.getLogger("asyncua").setLevel(logging.WARNING)

    # behave runs with the project root as cwd; ensure the env points
    # the protocol module at our local test server.
    os.environ.setdefault("VINEAPP_OPCUA_PLC_URL", ENDPOINT)
    os.environ.setdefault("VINEAPP_OPCUA_LEUZE_URL", ENDPOINT)
    os.environ["VINEAPP_OPCUA_SECURITY"] = "none"
    # No Dremio in this suite: force the bollen-per-krat lookup down its
    # error path so every scan ack writes the default (999), even when
    # the developer's shell has a real VINEAPP_DB_CONNECTION.
    os.environ["VINEAPP_DB_CONNECTION"] = ""
    os.environ.pop("VINEAPP_BOLLEN_PER_KRAT_DEFAULT", None)


def before_scenario(context, scenario):
    context.warnings = []
    context.log_handler = _WarningCapture(context.warnings)
    context.log_handler.setFormatter(logging.Formatter("%(message)s"))
    logging.getLogger("opcua_protocol").addHandler(context.log_handler)

    _start_test_server(context)
    _start_protocol_handler(context)


def after_scenario(context, scenario):
    _stop_protocol_handler(context)
    _stop_test_server(context)
    handler = getattr(context, "log_handler", None)
    if handler:
        logging.getLogger("opcua_protocol").removeHandler(handler)
