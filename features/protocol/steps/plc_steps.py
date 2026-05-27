"""Steps that drive or read the PLC side of the protocol.

behave's step loader exec's modules without `__name__`, so relative
imports don't work — sync asyncua helpers are inlined here.
"""

import asyncio
import time

from asyncua import Client, ua
from behave import given, then

from production_control.opcua.protocol import (
    PLC_AANTAL_BOLLEN_NODEID,
    PLC_SCAN_RESULTAAT_NODEID,
)
from production_control.potting_lots.line_controller import ACTIVE_PARTIJ_NODEIDS

ENDPOINT = "opc.tcp://127.0.0.1:4840"


async def _write(node_id, value, variant):
    client = Client(url=ENDPOINT)
    async with client:
        await client.get_node(node_id).write_value(value, variant)


async def _read(node_id):
    client = Client(url=ENDPOINT)
    async with client:
        return await client.get_node(node_id).read_value()


def _write_scan_resultaat(value):
    asyncio.run(_write(PLC_SCAN_RESULTAAT_NODEID, value, ua.VariantType.Int32))


def _read_scan_resultaat():
    return int(asyncio.run(_read(PLC_SCAN_RESULTAAT_NODEID)))


def _wait_for_scan_resultaat(expected, timeout_s=5.0):
    deadline = time.monotonic() + timeout_s
    last = None
    while time.monotonic() < deadline:
        last = _read_scan_resultaat()
        if last == expected:
            return
        time.sleep(0.1)
    raise AssertionError(f"ScanResultaat never became {expected}; last value: {last}")


@given("the PLC reports ScanResultaat = {value:d}")
def step_plc_reports_scan_resultaat(context, value):
    _write_scan_resultaat(value)
    # Give the handler's subscription a moment to pick up the change so
    # the guard reflects this value when the next scan arrives.
    time.sleep(0.6)
    assert _read_scan_resultaat() == value
    context.expected_scan_resultaat = value


@then("PC writes {value:d} to ScanResultaat")
def step_pc_writes_scan_resultaat(context, value):
    _wait_for_scan_resultaat(value)
    context.expected_scan_resultaat = value


@then("AantalBollenPerKrat = {value:d}")
def step_aantal_bollen_equals(context, value):
    # Once ScanResultaat is non-zero, AantalBollenPerKrat must already
    # hold the value paired with that scan — that's the write-order
    # invariant. Reading here (after the wait_for_scan_resultaat step)
    # observes the value the OS would see.
    actual = int(asyncio.run(_read(PLC_AANTAL_BOLLEN_NODEID)))
    assert actual == value, (
        f"expected AantalBollenPerKrat={value}, got {actual}"
    )
    context.expected_aantal_bollen = value


@then("PC does not write to AantalBollenPerKrat")
def step_pc_does_not_write_aantal_bollen(context):
    expected = getattr(context, "expected_aantal_bollen", 0)
    actual = int(asyncio.run(_read(PLC_AANTAL_BOLLEN_NODEID)))
    assert actual == expected, (
        f"expected AantalBollenPerKrat to stay at {expected}, but it became {actual}"
    )


@then("PC writes {value:d} to ActievePartijnummer{line:d}")
def step_pc_writes_active_partij(context, value, line):
    node_id = ACTIVE_PARTIJ_NODEIDS[line]
    actual = int(asyncio.run(_read(node_id)))
    assert actual == value, (
        f"expected ActievePartijnummer{line}={value}, got {actual}"
    )
