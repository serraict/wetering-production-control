# Omron PLC OPC/UA Connection (Ontsapelaar)

## Device
- **Model**: Omron NX/NJ series (NxOpcUaServer)
- **IP**: 192.168.50.36, port 4840
- **Server cert CN**: NxOpcUaServer@192.168.50.36
- **Server Application URI**: urn:192.168.50.36:OMRON:NxOpcUaServer

## How to connect (working)

Uses the UaExpert certificate as a workaround (see certificate issue below).

```python
import asyncio
from asyncua import Client

async def read_plc():
    client = Client("opc.tcp://192.168.50.36:4840")
    client.application_uri = "urn:Laptopper:UnifiedAutomation:UaExpert"
    client.set_user("Marijn")
    client.set_password("12345678")
    await client.set_security_string(
        "Basic256Sha256,SignAndEncrypt,"
        "certs/uaexpert_martin/uaexpert.der,"
        "certs/uaexpert_martin/uaexpert_key.pem"
    )
    async with client:
        # Read values
        for name in ["GoodRead", "Resultaat", "Trigger"]:
            node = client.get_node(f"ns=4;s={name}")
            value = await node.read_value()
            print(f"{name} = {value!r}")

        # Write a value
        node = client.get_node("ns=4;s=Trigger")
        await node.write_value(True)

asyncio.run(read_plc())
```

### Required files
- `certs/uaexpert_martin/uaexpert.der` — UaExpert client certificate
- `certs/uaexpert_martin/uaexpert_key.pem` — UaExpert private key

### Critical: application_uri must match cert
The `client.application_uri` MUST be set to `urn:Laptopper:UnifiedAutomation:UaExpert`
to match the URI in the UaExpert certificate SAN. The PLC validates this match.

## Key OPC/UA nodes (namespace index 4, string NodeIds)
| Node | NodeId | Type | Description |
|------|--------|------|-------------|
| GoodRead | ns=4;s=GoodRead | Boolean | Scanner got a good read |
| Resultaat | ns=4;s=Resultaat | String | Scan result value |
| Trigger | ns=4;s=Trigger | Boolean | Scanner trigger |
| Mode | ns=4;s=DeviceStatus.Mode | String | PLC mode (RUN) |
| ErrorStatus | ns=4;s=DeviceStatus.ErrorStatus | String | PLC error status |

## Browse command
```bash
uv run uabrowse -u opc.tcp://192.168.50.36:4840 \
  --security Basic256Sha256,SignAndEncrypt,certs/uaexpert_martin/uaexpert.der,certs/uaexpert_martin/uaexpert_key.pem \
  --user Marijn --password 12345678
```
Note: this gives a `BadCertificateUriInvalid` error because uabrowse sends
`urn:freeopcua:client` as application_uri which doesn't match the UaExpert cert.
Use a Python script instead (see above) where you can set `client.application_uri`.

## Certificate trust issue (unresolved)

Our self-signed and CA-signed client certificates are rejected with
`BadCertificateUseNotAllowed` at the `OpenSecureChannel` step.

### What was tried
- Self-signed certs with various key usage flags, serial number sizes, subject fields
- CA-signed cert (CA in "Trusted Issuers", client cert in "Trusted Certificates")
- OpenSSL-generated certs
- Importing via Sysmac Studio + transfer to controller + power cycle

### TODO
- Contact Omron support to understand how to properly import third-party client certificates
- Or find the correct Sysmac Studio workflow (reject-then-trust, GDS, etc.)
