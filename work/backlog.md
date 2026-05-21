# Backlog

Product increments to realize the product vision.

- **PLC monitoring app** — v1 (discover + JSONL on PLC) and v2 (Leuze as
  second source, supervised reconnect with exponential backoff) are shipped
  and verified against the production PLC. **v3** (Textual TUI) is implemented
  locally and pending prod verification via the next release. **v4** (rotated
  file logging under `VINEAPP_OPCUA_MONITOR_LOG_DIR`) and **v5** (persistent
  run on serraserver — compose service or background command) remain. Slice
  plan + status: [`work/notes/plc_monitoring_app.md`](notes/plc_monitoring_app.md).
- **OS ↔ PC protocol implementation** — long-running OPC client inside the
  web app (NiceGUI process) that owns the protocol from [protocol draft]:
  parses Leuze scans, writes `ScanResultaat` / `ActievePartijnummer{1,2}`
  on the PLC (full NodeIds confirmed against prod, see note), and waits for
  OS acknowledgement. `bolmaat` deferred. Specified with behave running
  against an updated `scripts/opc_test_server.py`. Details:
  [`work/notes/os_pc_protocol_implementation.md`](notes/os_pc_protocol_implementation.md).
- add show scan details page to potting list and inspection list so that i can
  quickly access the scan screen for commenting
- add show qr code button to potting list

[protocol draft]:
  https://potlilium.fibery.io/ICT_Wetering_Potlilium/Actie/Integratie-Onstapelmachine-met-oppotproces-257?sharing-key=0b2ea7ab-9c2d-4ae1-8b2a-c016b2816fa5
