# Leuze production connect — capture (2026-07-07)

Production scanner connected and scanning end-to-end. Findings from the
on-site session, keyed to the plan in `leuze_production_connect.md`.

## What we hit and how it resolved

- **`BadSecurityChecksFailed` at OpenSecureChannel (step 3).** The
  production scanner is a new device with an empty trust store. Fix:
  upload our client certificate (`client_cert.der`) to the Leuze device.
  No cert regeneration needed — same cert as the PLC connection.
- **Lenient cert parser fired as expected.** Log line "Using lenient
  certificate parser for malformed server cert" appeared on every
  connect — confirmed the production unit has the same malformed server
  certificate as the test bench (firmware V2.4.0). Normal, not an error.
- **"certificate does not contain the hostname in DNSNames" warnings**
  are cosmetic: our cert's SAN DNS doesn't cover the random Docker
  container hostname. Ignore.
- **Kratten carry bulb-picklist labels, not potting-lot labels.** First
  real scan produced `.../bulb-picking/scan/27978` and the protocol
  driver dropped it as unparseable. Bulb-picklist rows are potting lots
  (same id), so the parser now accepts both path forms — commit
  `84d7324`.

## Confirmed

- Production Leuze URL is `opc.tcp://10.0.0.191:4840` as documented in
  `docs/protocol.md`.
- Node ids match the test bench (`ns=5;i=6122` LastScanData).

## Deferred / follow-ups

- The `84d7324` parser fix needs a release (`make release`) and an image
  pull on serraserver to reach the `ontstapelaar_protocol` service.
