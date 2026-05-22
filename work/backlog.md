# Backlog

Product increments to realize the product vision.

- **OS ↔ PC protocol implementation.** Contract is settled in
  [`docs/protocol.md`](../docs/protocol.md). What remains: implement
  `src/production_control/opcua/protocol/` (Leuze subscription, gated PLC
  writer, operator UI hooks), update `scripts/opc_test_server.py` to the
  protocol nodes, and ship the behave suite at `features/protocol/`. Plan:
  [`work/notes/os_pc_protocol_implementation.md`](notes/os_pc_protocol_implementation.md).
- **PLC monitor — remaining slices.** v3 (Textual TUI) awaiting prod
  verification on the next release. **v4**: rotated JSONL under
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
