"""Regression guard: a Leuze outage must not stop the PLC loop in the
protocol daemon.

Before `supervise()`-per-role, `run_protocol` ran both loops under one
`asyncio.gather`, so any exception in `_leuze_loop` (e.g. asyncua
`set_security` timing out on the endpoint probe) cancelled the PLC
loop too and the container crash-looped via Docker.
"""

from __future__ import annotations

import asyncio

import pytest

from production_control.opcua import monitor
from production_control.opcua.protocol import scan_cycle


@pytest.mark.asyncio
async def test_leuze_failure_does_not_kill_plc(monkeypatch):
    # Speed up backoff so the test resolves in ~0.2s rather than seconds.
    monkeypatch.setattr(monitor, "RECONNECT_BASE_DELAY_S", 0.01)
    monkeypatch.setattr(monitor, "RECONNECT_MAX_DELAY_S", 0.05)

    plc_invocations = 0
    leuze_invocations = 0
    plc_running = asyncio.Event()

    async def fake_plc_loop(handler, ready, stop_event):
        nonlocal plc_invocations
        plc_invocations += 1
        if ready is not None:
            ready.set()
        plc_running.set()
        await stop_event.wait()

    async def fake_leuze_loop(handler, ready, stop_event):
        nonlocal leuze_invocations
        leuze_invocations += 1
        raise RuntimeError("leuze unreachable")

    monkeypatch.setattr(scan_cycle, "_plc_loop", fake_plc_loop)
    monkeypatch.setattr(scan_cycle, "_leuze_loop", fake_leuze_loop)

    stop_event = asyncio.Event()
    plc_ready = asyncio.Event()
    leuze_ready = asyncio.Event()

    task = asyncio.create_task(
        scan_cycle.run_protocol(
            plc_ready=plc_ready,
            leuze_ready=leuze_ready,
            stop_event=stop_event,
        )
    )

    try:
        # PLC subscription comes up.
        await asyncio.wait_for(plc_ready.wait(), timeout=1.0)

        # Give the Leuze supervisor a few backoff cycles to retry.
        await asyncio.sleep(0.2)

        # PLC stayed up — never restarted by gather-induced cancellation.
        assert plc_running.is_set()
        assert plc_invocations == 1, "PLC loop should not have been re-entered"

        # Leuze actually retried (not just failed once and gave up).
        assert (
            leuze_invocations >= 2
        ), f"expected supervise to retry Leuze; got {leuze_invocations} invocation(s)"
    finally:
        stop_event.set()
        await asyncio.wait_for(task, timeout=2.0)


@pytest.mark.asyncio
async def test_supervise_never_gives_up_when_max_attempts_is_none(monkeypatch):
    """`max_attempts=None` is the protocol daemon's policy: Docker decides
    when to bail, not the supervisor."""
    monkeypatch.setattr(monitor, "RECONNECT_BASE_DELAY_S", 0.001)
    monkeypatch.setattr(monitor, "RECONNECT_MAX_DELAY_S", 0.001)

    attempts = 0

    async def always_fails():
        nonlocal attempts
        attempts += 1
        raise RuntimeError("boom")

    stop_event = asyncio.Event()
    task = asyncio.create_task(
        monitor.supervise(
            "test",
            always_fails,
            max_attempts=None,
            stop_event=stop_event,
        )
    )

    try:
        # Far more attempts than the default RECONNECT_MAX_ATTEMPTS (10).
        await asyncio.sleep(0.1)
        assert attempts > 20, f"expected supervise to keep retrying; got {attempts}"
        assert not task.done(), "supervise should still be running"
    finally:
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task


@pytest.mark.asyncio
async def test_supervise_stops_silently_on_clean_return_with_stop_event(monkeypatch):
    """A clean `run()` return + stop_event set = graceful shutdown.

    Without `stop_event` awareness, supervise would treat the clean
    return as a transient close and start an exponential-backoff sleep
    + log 'reconnecting in Ns', which is misleading during shutdown."""
    monkeypatch.setattr(monitor, "RECONNECT_BASE_DELAY_S", 0.001)

    invocations = 0

    async def run_once_then_return(stop_event):
        nonlocal invocations
        invocations += 1
        await stop_event.wait()

    stop_event = asyncio.Event()

    async def runner():
        await monitor.supervise(
            "test",
            lambda: run_once_then_return(stop_event),
            max_attempts=None,
            stop_event=stop_event,
        )

    task = asyncio.create_task(runner())
    await asyncio.sleep(0.05)
    assert invocations == 1
    assert not task.done()

    stop_event.set()
    await asyncio.wait_for(task, timeout=1.0)
    assert invocations == 1, "supervise should not have re-entered run() after stop_event"
