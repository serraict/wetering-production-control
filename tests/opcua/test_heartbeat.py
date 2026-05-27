"""Tests for opcua.heartbeat: file appears, mtime advances, cancellation stops the beat."""

from __future__ import annotations

import asyncio

import pytest

from production_control.opcua import heartbeat


@pytest.fixture(autouse=True)
def _isolated_heartbeat_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("VINEAPP_OPCUA_HEARTBEAT_DIR", str(tmp_path))
    return tmp_path


def test_path_for_uses_env_dir(tmp_path):
    assert heartbeat.path_for("plc") == tmp_path / "opcua-plc.alive"
    assert heartbeat.path_for("leuze") == tmp_path / "opcua-leuze.alive"


@pytest.mark.asyncio
async def test_beat_creates_file_immediately(tmp_path):
    stop = asyncio.Event()
    task = asyncio.create_task(heartbeat.beat_while_alive("plc", stop, interval_s=10))
    # Yield once so the first touch runs before we assert.
    await asyncio.sleep(0.01)
    assert (tmp_path / "opcua-plc.alive").exists()
    stop.set()
    await task


@pytest.mark.asyncio
async def test_beat_advances_mtime(tmp_path):
    stop = asyncio.Event()
    task = asyncio.create_task(heartbeat.beat_while_alive("plc", stop, interval_s=0.02))
    await asyncio.sleep(0.01)
    first = (tmp_path / "opcua-plc.alive").stat().st_mtime
    await asyncio.sleep(0.06)
    second = (tmp_path / "opcua-plc.alive").stat().st_mtime
    stop.set()
    await task
    assert second > first


@pytest.mark.asyncio
async def test_beat_stops_on_event(tmp_path):
    stop = asyncio.Event()
    task = asyncio.create_task(heartbeat.beat_while_alive("plc", stop, interval_s=0.01))
    await asyncio.sleep(0.01)
    stop.set()
    # Should return promptly, not after a full interval.
    await asyncio.wait_for(task, timeout=0.1)


@pytest.mark.asyncio
async def test_beat_stops_on_cancellation(tmp_path):
    stop = asyncio.Event()
    task = asyncio.create_task(heartbeat.beat_while_alive("plc", stop, interval_s=10))
    await asyncio.sleep(0.01)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
