"""Regression guard: writes to the Omron PLC must not include timestamps.

The Omron NX OPC UA server rejects WriteValue requests where the DataValue
has any of SourceTimestamp / ServerTimestamp / StatusCode populated, with
`BadWriteNotSupported`. asyncua's `node.write_value(value, varianttype)`
convenience form auto-stamps SourceTimestamp (see
`asyncua/common/ua_utils.py:value_to_datavalue`), so every callsite that
writes to the PLC must pre-build the DataValue itself.

This was observed in prod 2026-05-22: the operator activating a partij
in the web UI failed with `BadWriteNotSupported` after three retries.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from asyncua import ua

from production_control.opcua.protocol.scan_cycle import ScanCycleHandler
from production_control.potting_lots.line_controller import PottingLineController


def _captured_datavalue(write_call) -> ua.DataValue:
    """Pull the DataValue from the asyncua write_value call args."""
    assert write_call.await_count == 1, "expected exactly one write_value call"
    args, _kwargs = write_call.await_args
    dv = args[0]
    assert isinstance(dv, ua.DataValue), f"expected pre-built DataValue, got {type(dv).__name__}"
    return dv


def _assert_omron_safe(dv: ua.DataValue) -> None:
    # StatusCode defaults to Good and is fine — scripts/write_plc.py uses
    # the same pattern in prod. Only the timestamps trigger Omron's
    # BadWriteNotSupported.
    assert (
        dv.SourceTimestamp is None
    ), "DataValue.SourceTimestamp is set; Omron NX rejects this with BadWriteNotSupported"
    assert dv.ServerTimestamp is None, "DataValue.ServerTimestamp must not be set for Omron"


@pytest.mark.asyncio
async def test_line_controller_does_not_send_timestamps(monkeypatch):
    monkeypatch.setenv("VINEAPP_OPCUA_SECURITY", "none")
    monkeypatch.setenv("VINEAPP_OPCUA_PLC_URL", "opc.tcp://127.0.0.1:4840")

    write_mock = AsyncMock()
    fake_node = MagicMock()
    fake_node.write_value = write_mock
    fake_client = MagicMock()
    fake_client.get_node = MagicMock(return_value=fake_node)
    fake_client.connect = AsyncMock()
    fake_client.disconnect = AsyncMock()

    @asynccontextmanager
    async def fake_connected_client(self):
        yield fake_client

    with patch.object(PottingLineController, "_get_connected_client", fake_connected_client):
        controller = PottingLineController()
        success = await controller.set_active_lot(1, 12345)

    assert success
    _assert_omron_safe(_captured_datavalue(write_mock))


@pytest.mark.asyncio
async def test_scan_cycle_write_does_not_send_timestamps():
    write_mock = AsyncMock()
    fake_node = MagicMock()
    fake_node.write_value = write_mock

    handler = ScanCycleHandler()
    handler._plc_write_node = fake_node

    await handler._write(27246)

    _assert_omron_safe(_captured_datavalue(write_mock))
