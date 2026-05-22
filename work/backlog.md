# Backlog

Product increments to realize the product vision.

- **PLC monitor — remaining slices.** **v4**: rotated JSONL under
  `VINEAPP_OPCUA_MONITOR_LOG_DIR`. **v5**: persistent run on serraserver.
  Status: [`work/notes/plc_monitoring_app.md`](notes/plc_monitoring_app.md).
- **Protocol daemon: per-source supervisor.** Today `protocol/scan_cycle.py`
  has no `supervise()` wrapper, so any failure in `_leuze_loop` (e.g. Leuze
  unreachable, asyncua `set_security` timing out during its endpoint probe)
  kills `_plc_loop` via `asyncio.gather` and the container crash-loops. Wrap
  each role's loop in `supervise()` (already in `monitor.py`) and drop the
  `RECONNECT_MAX_ATTEMPTS` giveup for the protocol daemon — Docker's
  `restart: unless-stopped` is the right policy for "process truly broken";
  the supervisor's job is riding out transient outages. Add a unit test that
  asserts a Leuze failure doesn't kill the PLC loop.
- Show scan details page from the potting list and inspection list so the scan
  screen is one click away for commenting.
- Show QR code button on the potting list.
