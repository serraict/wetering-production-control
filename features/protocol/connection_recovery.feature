Feature: Connection recovery (v3 placeholder)

  This file is reserved for the v3 reconnection scenarios: PLC drops
  and recovers, Leuze drops and recovers, both sources recover
  independently, scans that arrive during a PLC outage are dropped
  (we don't queue). v1 relies on the per-source supervise() loop in
  src/production_control/opcua/monitor.py and verifies recovery only
  by manual observation. Intentionally empty — behave's runner stays
  green.
