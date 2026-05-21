# Integratie ontstapelmachine — references & guidelines

Working docs: [Fibery action].

Production endpoints, certs, and operational commands live in
[`doing_ontstapelaar.md`](doing_ontstapelaar.md) (was previously duplicated
here). Auto-memory in `MEMORY.md` covers the test-setup IPs and credentials
that we still occasionally use for reproductions.

## Guidelines for OPC/UA scripts

Follow the [opcua-examples] closely — they're known to work and document the
details of the OMRON OPC implementation (cert EKUs, app URI length limit,
security policy combinations).

Keep scripts minimal and clean. Reuse `VINEAPP_OPCUA_*` env vars rather than
hardcoding endpoints; route shared logic through
`src/production_control/opcua/` rather than duplicating it in `scripts/`.

[Fibery action]:
  https://potlilium.fibery.io/ICT_Wetering_Potlilium/Actie/Integratatie-Onstapelmachine-met-oppotproces-256?sharing-key=0b2ea7ab-9c2d-4ae1-8b2a-c016b2816fa5
[opcua-examples]: ../../../docs/notes/opcua-examples/
