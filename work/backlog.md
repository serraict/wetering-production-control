# Backlog

This backlog describes the product increments we have to build to realize our
product vision.

- **PLC monitoring app** — read-only Textual TUI + JSONL logger over the
  protocol OPC nodes (Leuze + Potting PLC), plus a small fixed set of extras.
  Same container image as the web app, separate compose service. Testable
  against `scripts/opc_test_server.py`. Details:
  [`work/notes/plc_monitoring_app.md`](notes/plc_monitoring_app.md).
- **OS ↔ PC protocol implementation** — long-running service that owns the
  protocol from [protocol draft]: parses Leuze scans, writes
  `ScanResultaat` / `ActievePartijnummer{1,2}` on the PLC, waits for OS
  acknowledgement. Specified with behave running against
  `scripts/opc_test_server.py`; documented in
  `docs/architecture.md#opcua-machine-communication`. Details:
  [`work/notes/os_pc_protocol_implementation.md`](notes/os_pc_protocol_implementation.md).
- add show scan details page to potting list and inspection list so that i can
  quickly access the scan screen for commenting
- add show qr code button to potting list

[protocol draft]:
  https://potlilium.fibery.io/ICT_Wetering_Potlilium/Actie/Integratie-Onstapelmachine-met-oppotproces-257?sharing-key=0b2ea7ab-9c2d-4ae1-8b2a-c016b2816fa5
