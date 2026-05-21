# Integratie ontstapelmachine

See the [Working docs] for full description of the work.

## Context

OS PLC ip address and port: to be determined.
OS Leuze scanner ip address and port: TBD
PC runs on Serra Vine, on a docker container. The Docker containers are hosted on the server `serraserver`, with ip address 10.0.0.3.

Server and client certificates have yet to be generated.

## Guidelines for scripts

Follow the [opcua-examples] closely, as they are know to work and document the details of the OMRON PLC OPC implementation.

Keep the scripts minimal and clean.

[Working docs]: https://potlilium.fibery.io/ICT_Wetering_Potlilium/Actie/Integratatie-Onstapelmachine-met-oppotproces-256?sharing-key=0b2ea7ab-9c2d-4ae1-8b2a-c016b2816fa5
[opcua-examples]: ../../../docs/notes/opcua-examples/
