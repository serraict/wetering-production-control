Field-test scripts kept for reference. Superseded by:

- `scripts/probe_opcua_endpoint.py`, `scripts/monitor_plc.py`,
  `scripts/monitor_leuze.py`, `scripts/write_plc.py`
- `src/production_control/opcua/` (monitor + TUI)

Numbered `test_*` files map to the original protocol-probe sequence
(read protocol vars, write actieve_partij, read Leuze scan, read/write
ScanResultaat). They predate the consolidated env-var config and the
discover-and-subscribe monitor.
